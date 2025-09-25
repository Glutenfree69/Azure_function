import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential
import logging
from datetime import datetime, timezone

# ✅ CHANGEMENT : Passer de ANONYMOUS à USER
app = func.FunctionApp(http_auth_level=func.AuthLevel.USER)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    # ✅ NOUVEAU : Récupération des informations utilisateur
    try:
        user_id = req.headers.get('X-MS-CLIENT-PRINCIPAL-ID')
        user_name = req.headers.get('X-MS-CLIENT-PRINCIPAL-NAME')
        logging.info(f"✅ Utilisateur authentifié: {user_name} (ID: {user_id})")
    except Exception as e:
        logging.warning(f"Impossible de récupérer les infos utilisateur: {e}")

    try:
        # Configuration Cosmos DB (reste identique)
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
        database_name = os.environ.get('COSMOS_DB_DATABASE')
        container_name = os.environ.get('COSMOS_DB_CONTAINER')

        if not all([endpoint, database_name, container_name]):
            return func.HttpResponse(
                json.dumps({"error": "Configuration Cosmos DB manquante"}),
                status_code=500,
                mimetype="application/json"
            )

        # Authentification sécurisée avec Managed Identity (reste identique)
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)
        logging.info("✅ Authentification via Managed Identity")

        # Connexion à la base de données et container (reste identique)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        counter_id = "main-counter"

        if req.method == "GET":
            return handle_get_request(container, counter_id, user_name)
        elif req.method == "POST":
            return handle_post_request(req, container, counter_id, user_name)

    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

def get_or_create_counter(container, counter_id):
    """Récupère ou crée le document compteur (reste identique)"""
    try:
        counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
        return counter_doc
    except exceptions.CosmosResourceNotFoundError:
        current_time = datetime.now(timezone.utc).isoformat()
        counter_doc = {
            "id": counter_id,
            "value": 0,
            "created_at": current_time,
            "last_updated": current_time,
            "last_user": "system"  # ✅ NOUVEAU : Tracker qui a modifié
        }
        container.create_item(body=counter_doc)
        return counter_doc

def update_counter(container, counter_id, new_value, user_name=None):
    """Met à jour la valeur du compteur"""
    counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
    counter_doc["value"] = new_value
    counter_doc["last_updated"] = datetime.now(timezone.utc).isoformat()
    counter_doc["last_user"] = user_name or "unknown"  # ✅ NOUVEAU : Tracker l'utilisateur
    container.replace_item(item=counter_id, body=counter_doc)
    return counter_doc

def handle_get_request(container, counter_id, user_name=None):
    """Gère les requêtes GET - Retourne les données JSON du compteur"""
    try:
        counter_doc = get_or_create_counter(container, counter_id)

        return func.HttpResponse(
            json.dumps({
                "value": counter_doc['value'],
                "last_updated": counter_doc['last_updated'],
                "created_at": counter_doc['created_at'],
                "last_user": counter_doc.get('last_user', 'unknown'),  # ✅ NOUVEAU
                "current_user": user_name  # ✅ NOUVEAU : Qui fait la requête
            }),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Erreur GET: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur lors de la récupération: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

def handle_post_request(req, container, counter_id, user_name=None):
    """Gère les requêtes POST - Actions sur le compteur"""
    try:
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None

        if not action:
            return func.HttpResponse(
                json.dumps({"error": "Action manquante"}),
                status_code=400,
                mimetype="application/json"
            )

        counter_doc = get_or_create_counter(container, counter_id)
        current_value = counter_doc['value']

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
                mimetype="application/json"
            )

        # ✅ NOUVEAU : Passer le nom d'utilisateur
        updated_doc = update_counter(container, counter_id, new_value, user_name)

        return func.HttpResponse(
            json.dumps({
                "success": True,
                "action": action,
                "previous_value": current_value,
                "new_value": new_value,
                "timestamp": updated_doc["last_updated"],
                "user": user_name  # ✅ NOUVEAU : Qui a fait l'action
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Erreur POST: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Erreur: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )