import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential
import logging
from datetime import datetime, timezone

# Configuration avec authentification USER
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)  # ✅ CHANGÉ temporairement

# ✅ NOUVEAU : Route séparée pour gérer OPTIONS (preflight CORS)
@app.route(route="counter", methods=["OPTIONS"])
def counter_preflight(req: func.HttpRequest) -> func.HttpResponse:
    """Gère les requêtes preflight CORS"""
    logging.info('Preflight CORS request processed')
    
    return func.HttpResponse(
        status_code=204,  # No Content
        headers={
            'Access-Control-Allow-Origin': req.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-MS-CLIENT-PRINCIPAL-ID, X-MS-CLIENT-PRINCIPAL-NAME',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        }
    )

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint principal du compteur avec authentification"""
    logging.info('Python HTTP trigger function processed a request.')
    
    # Récupération des informations utilisateur (Entra ID)
    user_id = req.headers.get('X-MS-CLIENT-PRINCIPAL-ID', 'anonymous')
    user_name = req.headers.get('X-MS-CLIENT-PRINCIPAL-NAME', 'anonymous')
    logging.info(f"Utilisateur: {user_name} (ID: {user_id})")

    try:
        # Configuration Cosmos DB
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
        database_name = os.environ.get('COSMOS_DB_DATABASE')
        container_name = os.environ.get('COSMOS_DB_CONTAINER')

        if not all([endpoint, database_name, container_name]):
            return create_json_response(
                {"error": "Configuration Cosmos DB manquante"},
                status_code=500
            )

        # Authentification avec Managed Identity
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)
        logging.info("✅ Authentification via Managed Identity réussie")

        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        counter_id = "main-counter"

        if req.method == "GET":
            return handle_get_request(container, counter_id, user_name, req)
        elif req.method == "POST":
            return handle_post_request(req, container, counter_id, user_name)

    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur serveur: {str(e)}"},
            status_code=500
        )

def create_json_response(data, status_code=200, origin=None):
    """Crée une réponse JSON avec les headers CORS appropriés"""
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    if origin:
        headers['Access-Control-Allow-Origin'] = origin
    
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        headers=headers,
        mimetype="application/json"
    )

def get_or_create_counter(container, counter_id):
    """Récupère ou crée le document compteur"""
    try:
        counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
        logging.info(f"Compteur existant récupéré: {counter_doc['value']}")
        return counter_doc
    except exceptions.CosmosResourceNotFoundError:
        current_time = datetime.now(timezone.utc).isoformat()
        counter_doc = {
            "id": counter_id,
            "value": 0,
            "created_at": current_time,
            "last_updated": current_time,
            "last_user": "system"
        }
        container.create_item(body=counter_doc)
        logging.info("Nouveau compteur créé")
        return counter_doc

def update_counter(container, counter_id, new_value, user_name=None):
    """Met à jour la valeur du compteur"""
    counter_doc = container.read_item(item=counter_id, partition_key=counter_id)
    counter_doc["value"] = new_value
    counter_doc["last_updated"] = datetime.now(timezone.utc).isoformat()
    counter_doc["last_user"] = user_name or "unknown"
    container.replace_item(item=counter_id, body=counter_doc)
    logging.info(f"Compteur mis à jour: {new_value} par {user_name}")
    return counter_doc

def handle_get_request(container, counter_id, user_name=None, req=None):
    """Gère les requêtes GET - Retourne les données JSON du compteur"""
    try:
        counter_doc = get_or_create_counter(container, counter_id)
        
        origin = req.headers.get('Origin') if req else None

        return create_json_response(
            {
                "value": counter_doc['value'],
                "last_updated": counter_doc['last_updated'],
                "created_at": counter_doc['created_at'],
                "last_user": counter_doc.get('last_user', 'unknown'),
                "current_user": user_name
            },
            origin=origin
        )
    except Exception as e:
        logging.error(f"Erreur GET: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur lors de la récupération: {str(e)}"},
            status_code=500
        )

def handle_post_request(req, container, counter_id, user_name=None):
    """Gère les requêtes POST - Actions sur le compteur"""
    try:
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None

        if not action:
            return create_json_response(
                {"error": "Action manquante (increment, decrement, reset)"},
                status_code=400
            )

        counter_doc = get_or_create_counter(container, counter_id)
        current_value = counter_doc['value']

        # Validation et calcul de la nouvelle valeur
        if action == 'increment':
            new_value = current_value + 1
        elif action == 'decrement':
            new_value = current_value - 1
        elif action == 'reset':
            new_value = 0
        else:
            return create_json_response(
                {"error": f"Action '{action}' non valide. Actions valides: increment, decrement, reset"},
                status_code=400
            )

        updated_doc = update_counter(container, counter_id, new_value, user_name)
        
        origin = req.headers.get('Origin')

        return create_json_response(
            {
                "success": True,
                "action": action,
                "previous_value": current_value,
                "new_value": new_value,
                "timestamp": updated_doc["last_updated"],
                "user": user_name
            },
            origin=origin
        )

    except ValueError as e:
        logging.error(f"Erreur de validation POST: {str(e)}")
        return create_json_response(
            {"error": "Format JSON invalide"},
            status_code=400
        )
    except Exception as e:
        logging.error(f"Erreur POST: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur lors de l'action: {str(e)}"},
            status_code=500
        )