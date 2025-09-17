import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions
import logging
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        # Configuration Cosmos DB
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
        key = os.environ.get('COSMOS_DB_KEY')
        database_name = os.environ.get('COSMOS_DB_DATABASE')
        container_name = os.environ.get('COSMOS_DB_CONTAINER')
        
        if not all([endpoint, key, database_name, container_name]):
            return func.HttpResponse("Configuration Cosmos DB manquante", status_code=500)
        
        # Initialisation du client Cosmos DB
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        counter_id = "main-counter"
        
        # Traitement selon la méthode HTTP
        if req.method == "GET":
            return handle_get_request(container, counter_id)
        elif req.method == "POST":
            return handle_post_request(req, container, counter_id)
            
    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}")
        return func.HttpResponse(
            f"Erreur: {str(e)}", 
            status_code=500
        )

def get_or_create_counter(container, counter_id):
    """Récupère ou crée le document compteur"""
    try:
        # Essayer de récupérer le compteur existant
        counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
        return counter_doc
    except exceptions.CosmosResourceNotFoundError:
        # Si le compteur n'existe pas, le créer
        counter_doc = {
            "id": counter_id,
            "value": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        container.create_item(body=counter_doc)
        return counter_doc

def update_counter(container, counter_id, new_value):
    """Met à jour la valeur du compteur"""
    counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
    counter_doc["value"] = new_value
    counter_doc["last_updated"] = datetime.utcnow().isoformat()
    container.replace_item(item=counter_id, body=counter_doc)
    return counter_doc

def handle_get_request(container, counter_id):
    """Gère les requêtes GET - Affiche l'interface du compteur"""
    counter_doc = get_or_create_counter(container, counter_id)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Compteur Azure Function</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                text-align: center;
                background-color: #f0f2f5;
            }}
            .counter-container {{
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .counter-value {{
                font-size: 4em;
                font-weight: bold;
                color: #0078d4;
                margin: 20px 0;
            }}
            .button {{
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 15px 30px;
                margin: 10px;
                font-size: 1.2em;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
            }}
            .button:hover {{
                background-color: #106ebe;
            }}
            .button.danger {{
                background-color: #d13438;
            }}
            .button.danger:hover {{
                background-color: #a4262c;
            }}
            .info {{
                margin-top: 20px;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="counter-container">
            <h1>🔢 Compteur Azure Function</h1>
            <div class="counter-value">{counter_doc['value']}</div>
            
            <div>
                <button class="button" onclick="updateCounter('increment')">➕ Incrémenter</button>
                <button class="button" onclick="updateCounter('decrement')">➖ Décrémenter</button>
                <button class="button danger" onclick="updateCounter('reset')">🔄 Reset</button>
            </div>
            
            <div class="info">
                <p>Dernière mise à jour: {counter_doc['last_updated']}</p>
                <p>Stocké dans Cosmos DB ☁️</p>
            </div>
        </div>

        <script>
            async function updateCounter(action) {{
                try {{
                    const response = await fetch(window.location.href, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ action: action }})
                    }});
                    
                    if (response.ok) {{
                        location.reload();
                    }} else {{
                        alert('Erreur lors de la mise à jour du compteur');
                    }}
                }} catch (error) {{
                    console.error('Erreur:', error);
                    alert('Erreur de connexion');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return func.HttpResponse(html_content, mimetype="text/html")

def handle_post_request(req, container, counter_id):
    """Gère les requêtes POST - Actions sur le compteur"""
    try:
        # Parser le JSON de la requête
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None
        
        if not action:
            return func.HttpResponse("Action manquante", status_code=400)
        
        # Récupérer le compteur actuel
        counter_doc = get_or_create_counter(container, counter_id)
        current_value = counter_doc['value']
        
        # Traiter l'action
        if action == 'increment':
            new_value = current_value + 1
        elif action == 'decrement':
            new_value = current_value - 1
        elif action == 'reset':
            new_value = 0
        else:
            return func.HttpResponse("Action non valide", status_code=400)
        
        # Mettre à jour dans Cosmos DB
        updated_doc = update_counter(container, counter_id, new_value)
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "action": action,
                "previous_value": current_value,
                "new_value": new_value,
                "timestamp": updated_doc["last_updated"]
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Erreur POST: {str(e)}")
        return func.HttpResponse(f"Erreur: {str(e)}", status_code=500)