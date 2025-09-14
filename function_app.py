import azure.functions as func
import logging
import json
import os
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configuration Table Storage
STORAGE_CONNECTION_STRING = os.environ.get('AzureWebJobsStorage')
TABLE_NAME = 'counterdata'

def get_table_client():
    """Obtient le client pour Azure Table Storage"""
    service_client = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    table_client = service_client.get_table_client(table_name=TABLE_NAME)

    # Créer la table si elle n'existe pas
    try:
        table_client.create_table()
    except Exception:
        pass  # Table existe déjà

    return table_client

def get_counter_value():
    """Récupère la valeur actuelle du compteur"""
    try:
        logging.info("Getting counter value...")
        table_client = get_table_client()
        logging.info("Getting entity from table...")
        entity = table_client.get_entity(partition_key="counter", row_key="main")
        count = entity.get('count', 0)
        logging.info(f"Counter value retrieved: {count}")
        return count
    except Exception as e:
        logging.error(f"Error getting counter value: {e}")
        logging.info("Counter not found, starting from 0")
        return 0

def update_counter_value(new_value):
    """Met à jour la valeur du compteur"""
    try:
        logging.info(f"Updating counter to {new_value}...")
        table_client = get_table_client()
        entity = TableEntity()
        entity['PartitionKey'] = 'counter'
        entity['RowKey'] = 'main'
        entity['count'] = new_value

        logging.info("Upserting entity...")
        table_client.upsert_entity(entity=entity)
        logging.info(f"Counter updated successfully to {new_value}")
        return True
    except Exception as e:
        logging.error(f"Error updating counter: {e}")
        return False

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Counter function processed a request.')

    if req.method == "POST":
        try:
            # Incrémenter le compteur
            logging.info('POST request - getting current counter value')
            current_count = get_counter_value()
            logging.info(f'Current count: {current_count}')

            new_count = current_count + 1
            logging.info(f'Trying to update counter to: {new_count}')

            if update_counter_value(new_count):
                logging.info(f'Counter successfully incremented to: {new_count}')
                return func.HttpResponse(
                    json.dumps({"count": new_count, "action": "incremented"}),
                    mimetype="application/json"
                )
            else:
                logging.error('Failed to update counter value')
                return func.HttpResponse(
                    json.dumps({"error": "Failed to update counter"}),
                    status_code=500,
                    mimetype="application/json"
                )
        except Exception as e:
            logging.error(f'Exception in POST handler: {str(e)}')
            return func.HttpResponse(
                json.dumps({"error": f"Exception: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )

    elif req.method == "GET":
        # Récupérer la valeur actuelle et retourner la page HTML
        current_count = get_counter_value()

        # Détecter le type de stockage utilisé
        storage_type = "💾 Table Storage" if get_table_client() else "🧠 Mémoire (local)"
        storage_info = "Les données persistent entre les redémarrages" if get_table_client() else "Stockage temporaire - données perdues au redémarrage"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compteur Azure Function</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    text-align: center;
                    margin-top: 50px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .counter {{
                    font-size: 72px;
                    margin: 30px;
                    color: #0078d4;
                    font-weight: bold;
                }}
                .button {{
                    background-color: #0078d4;
                    color: white;
                    padding: 15px 30px;
                    font-size: 18px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }}
                .button:hover {{ background-color: #106ebe; }}
                .button:active {{ transform: scale(0.95); }}
                .info {{
                    margin-top: 20px;
                    color: #666;
                    font-size: 14px;
                }}
                .storage-type {{
                    background-color: #f0f8ff;
                    border: 1px solid #0078d4;
                    border-radius: 5px;
                    padding: 10px;
                    margin-top: 15px;
                    color: #0078d4;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧮 Compteur Azure</h1>
                <div class="counter" id="counter">{current_count}</div>
                <button class="button" onclick="incrementCounter()">➕ Ajouter 1</button>
                <div class="storage-type">
                    <strong>{storage_type}</strong><br>
                    {storage_info}
                </div>
            </div>

            <script>
                async function incrementCounter() {{
                    const button = document.querySelector('.button');
                    button.disabled = true;
                    button.textContent = '⏳ Chargement...';

                    try {{
                        const response = await fetch(window.location.href, {{
                            method: 'POST'
                        }});
                        const data = await response.json();

                        if (data.count !== undefined) {{
                            document.getElementById('counter').textContent = data.count;
                        }} else {{
                            alert('Erreur: ' + (data.error || 'Erreur inconnue'));
                        }}
                    }} catch (error) {{
                        console.error('Erreur:', error);
                        alert('Erreur de connexion');
                    }} finally {{
                        button.disabled = false;
                        button.textContent = '➕ Ajouter 1';
                    }}
                }}
            </script>
        </body>
        </html>
        """

        return func.HttpResponse(
            html_content,
            mimetype="text/html"
        )