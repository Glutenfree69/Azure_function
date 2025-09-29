import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential
import logging
from datetime import datetime, timezone
import jwt
import requests
from functools import wraps

# Configuration avec authentification ANONYMOUS (MSAL gère l'auth)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Configuration Entra ID
TENANT_ID = os.environ.get('TENANT_ID')
CLIENT_ID = os.environ.get('ENTRA_CLIENT_ID')
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

# Cache pour les clés publiques de Microsoft (évite de les récupérer à chaque requête)
_jwks_cache = None

def get_jwks():
    """Récupère les clés publiques de Microsoft pour valider les JWT"""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_uri = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
        response = requests.get(jwks_uri)
        _jwks_cache = response.json()
    return _jwks_cache

def validate_token(token: str) -> dict:
    """
    Valide un token JWT et retourne les claims si valide
    
    Raises:
        ValueError: Si le token est invalide
    """
    try:
        # Décoder le header pour obtenir le kid (key id)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise ValueError("Token sans kid")
        
        # Trouver la clé publique correspondante
        jwks = get_jwks()
        public_key = None
        
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise ValueError("Clé publique non trouvée")
        
        # Valider le token avec la clé publique
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=f"api://{CLIENT_ID}",  # L'audience doit matcher l'API
            issuer=ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True
            }
        )
        
        logging.info(f"✅ Token validé pour: {decoded.get('name', 'unknown')}")
        return decoded
        
    except jwt.ExpiredSignatureError:
        logging.error("❌ Token expiré")
        raise ValueError("Token expiré")
    except jwt.InvalidAudienceError:
        logging.error("❌ Audience invalide")
        raise ValueError("Audience invalide")
    except jwt.InvalidIssuerError:
        logging.error("❌ Issuer invalide")
        raise ValueError("Issuer invalide")
    except Exception as e:
        logging.error(f"❌ Erreur de validation du token: {str(e)}")
        raise ValueError(f"Token invalide: {str(e)}")

def require_auth(handler):
    """Décorateur pour protéger les routes avec authentification JWT"""
    @wraps(handler)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        # Extraire le token du header Authorization
        auth_header = req.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logging.warning("⚠️ Header Authorization manquant ou invalide")
            return func.HttpResponse(
                json.dumps({"error": "Authentification requise"}),
                status_code=401,
                mimetype="application/json",
                headers={
                    'Access-Control-Allow-Origin': req.headers.get('Origin', '*'),
                    'Access-Control-Allow-Credentials': 'true'
                }
            )
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Valider le token
            claims = validate_token(token)
            
            # Ajouter les claims au contexte de la requête
            req.claims = claims
            
            # Appeler la fonction originale
            return handler(req)
            
        except ValueError as e:
            logging.error(f"❌ Token invalide: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"Token invalide: {str(e)}"}),
                status_code=401,
                mimetype="application/json",
                headers={
                    'Access-Control-Allow-Origin': req.headers.get('Origin', '*'),
                    'Access-Control-Allow-Credentials': 'true'
                }
            )
    
    return wrapper

# ========================================
# ROUTES
# ========================================

@app.route(route="counter", methods=["OPTIONS"])
def counter_preflight(req: func.HttpRequest) -> func.HttpResponse:
    """Gère les requêtes preflight CORS"""
    logging.info('Preflight CORS request')
    
    return func.HttpResponse(
        status_code=204,
        headers={
            'Access-Control-Allow-Origin': req.headers.get('Origin', '*'),
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '3600'
        }
    )

@app.route(route="counter", methods=["GET", "POST"])
@require_auth
def counter(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint principal du compteur avec authentification JWT"""
    
    # Récupérer les infos utilisateur depuis le token validé
    user_name = req.claims.get('name', req.claims.get('preferred_username', 'unknown'))
    user_email = req.claims.get('email', req.claims.get('upn', 'unknown'))
    
    logging.info(f"✅ Requête authentifiée: {user_name} ({user_email})")

    try:
        # Configuration Cosmos DB
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
        database_name = os.environ.get('COSMOS_DB_DATABASE')
        container_name = os.environ.get('COSMOS_DB_CONTAINER')

        if not all([endpoint, database_name, container_name]):
            return create_json_response(
                {"error": "Configuration Cosmos DB manquante"},
                status_code=500,
                origin=req.headers.get('Origin')
            )

        # Authentification avec Managed Identity
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)

        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        counter_id = "main-counter"

        if req.method == "GET":
            return handle_get_request(container, counter_id, user_name, req)
        elif req.method == "POST":
            return handle_post_request(req, container, counter_id, user_name)

    except Exception as e:
        logging.error(f"❌ Erreur générale: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur serveur: {str(e)}"},
            status_code=500,
            origin=req.headers.get('Origin')
        )

# ========================================
# HELPERS
# ========================================

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
        logging.info(f"Compteur existant: {counter_doc['value']}")
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
    """Gère les requêtes GET"""
    try:
        counter_doc = get_or_create_counter(container, counter_id)
        
        return create_json_response(
            {
                "value": counter_doc['value'],
                "last_updated": counter_doc['last_updated'],
                "created_at": counter_doc['created_at'],
                "last_user": counter_doc.get('last_user', 'unknown'),
                "current_user": user_name
            },
            origin=req.headers.get('Origin')
        )
    except Exception as e:
        logging.error(f"❌ Erreur GET: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur lors de la récupération: {str(e)}"},
            status_code=500,
            origin=req.headers.get('Origin')
        )

def handle_post_request(req, container, counter_id, user_name=None):
    """Gère les requêtes POST"""
    try:
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None

        if not action:
            return create_json_response(
                {"error": "Action manquante (increment, decrement, reset)"},
                status_code=400,
                origin=req.headers.get('Origin')
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
            return create_json_response(
                {"error": f"Action '{action}' non valide"},
                status_code=400,
                origin=req.headers.get('Origin')
            )

        updated_doc = update_counter(container, counter_id, new_value, user_name)

        return create_json_response(
            {
                "success": True,
                "action": action,
                "previous_value": current_value,
                "new_value": new_value,
                "timestamp": updated_doc["last_updated"],
                "user": user_name
            },
            origin=req.headers.get('Origin')
        )

    except ValueError as e:
        logging.error(f"❌ Erreur de validation POST: {str(e)}")
        return create_json_response(
            {"error": "Format JSON invalide"},
            status_code=400,
            origin=req.headers.get('Origin')
        )
    except Exception as e:
        logging.error(f"❌ Erreur POST: {str(e)}", exc_info=True)
        return create_json_response(
            {"error": f"Erreur lors de l'action: {str(e)}"},
            status_code=500,
            origin=req.headers.get('Origin')
        )