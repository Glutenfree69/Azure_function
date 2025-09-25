import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential
import logging
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="counter", methods=["GET", "POST", "OPTIONS"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Gestion des requêtes OPTIONS (CORS preflight)
    if req.method == "OPTIONS":
        return func.HttpResponse(
            "",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    try:
        # Configuration Cosmos DB
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
        database_name = os.environ.get('COSMOS_DB_DATABASE')
        container_name = os.environ.get('COSMOS_DB_CONTAINER')

        if not all([endpoint, database_name, container_name]):
            return func.HttpResponse(
                json.dumps({"error": "Configuration Cosmos DB manquante"}),
                status_code=500,
                mimetype="application/json",
                headers=get_cors_headers()
            )

        # Authentification sécurisée avec Managed Identity
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)
        logging.info("✅ Authentification via Managed Identity")

        # Connexion à la base de données et container
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        counter_id = "main-counter"

        if req.method == "GET":
            return handle_get_request(container, counter_id)
        elif req.method == "POST":
            return handle_post_request(req, container, counter_id)

    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )

def get_cors_headers():
    """Retourne les headers CORS standard"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

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
    """Gère les requêtes GET - Retourne les données JSON du compteur"""
    try:
        counter_doc = get_or_create_counter(container, counter_id)

        # Retourne du JSON au lieu de HTML
        return func.HttpResponse(
            json.dumps({
                "value": counter_doc['value'],
                "last_updated": counter_doc['last_updated'],
                "created_at": counter_doc['created_at']
            }),
            mimetype="application/json",
            headers=get_cors_headers()
        )
    except Exception as e:
        logging.error(f"Erreur GET: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur lors de la récupération: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )

def handle_post_request(req, container, counter_id):
    """Gère les requêtes POST - Actions sur le compteur"""
    try:
        # Parser le JSON de la requête
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None

        if not action:
            return func.HttpResponse(
                json.dumps({"error": "Action manquante"}),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )

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
            return func.HttpResponse(
                json.dumps({"error": "Action non valide"}),
                status_code=400,
                mimetype="application/json",
                headers=get_cors_headers()
            )

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
            mimetype="application/json",
            headers=get_cors_headers()
        )

    except Exception as e:
        logging.error(f"Erreur POST: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
            headers=get_cors_headers()
        )