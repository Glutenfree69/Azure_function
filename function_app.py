import azure.functions as func
import logging
import json
import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configuration Cosmos DB depuis les app settings
COSMOS_ENDPOINT = os.environ.get('COSMOS_DB_ENDPOINT')
COSMOS_KEY = os.environ.get('COSMOS_DB_KEY')
COSMOS_DATABASE = os.environ.get('COSMOS_DB_DATABASE')
COSMOS_CONTAINER = os.environ.get('COSMOS_DB_CONTAINER')

# Client Cosmos DB global
cosmos_client = None
database = None
container = None

def get_cosmos_container():
    """Initialise et retourne le container Cosmos DB"""
    global cosmos_client, database, container
    
    if container is None:
        try:
            cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
            database = cosmos_client.get_database_client(COSMOS_DATABASE)
            container = database.get_container_client(COSMOS_CONTAINER)
            logging.info("Connected to Cosmos DB successfully")
        except Exception as e:
            logging.error(f"Failed to connect to Cosmos DB: {str(e)}")
            raise
    
    return container

def get_counter_value(counter_id: str = "main") -> int:
    """Récupère la valeur actuelle du compteur depuis Cosmos DB"""
    try:
        container = get_cosmos_container()
        
        # Tenter de récupérer le document
        item = container.read_item(item=counter_id, partition_key=counter_id)
        current_value = item.get('count', 0)
        logging.info(f"Counter '{counter_id}' current value: {current_value}")
        return current_value
        
    except exceptions.CosmosResourceNotFoundError:
        # Le compteur n'existe pas encore, on commence à 0
        logging.info(f"Counter '{counter_id}' not found, starting from 0")
        return 0
    except Exception as e:
        logging.error(f"Error reading counter '{counter_id}': {str(e)}")
        return 0

def update_counter_value(counter_id: str, new_value: int) -> bool:
    """Met à jour la valeur du compteur dans Cosmos DB"""
    try:
        container = get_cosmos_container()
        
        # Document à insérer/mettre à jour
        counter_doc = {
            'id': counter_id,
            'count': new_value,
            'type': 'counter'
        }
        
        # Upsert (insert ou update)
        container.upsert_item(counter_doc)
        logging.info(f"Counter '{counter_id}' updated to {new_value}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating counter '{counter_id}': {str(e)}")
        return False

def list_all_counters() -> list:
    """Liste tous les compteurs existants"""
    try:
        container = get_cosmos_container()
        
        # Query pour récupérer tous les compteurs
        query = "SELECT c.id, c.count FROM c WHERE c.type = 'counter'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        logging.info(f"Found {len(items)} counters")
        return items
        
    except Exception as e:
        logging.error(f"Error listing counters: {str(e)}")
        return []

@app.route(route="counter", methods=["GET", "POST", "PUT", "DELETE"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Counter function processed a request')
    
    try:
        # Récupérer l'ID du compteur depuis les paramètres (défaut: "main")
        counter_id = req.params.get('id', 'main')
        method = req.method
        
        if method == "GET":
            # Récupérer la valeur actuelle
            if counter_id == "all":
                # Lister tous les compteurs
                counters = list_all_counters()
                return func.HttpResponse(
                    json.dumps({"counters": counters}),
                    mimetype="application/json"
                )
            else:
                current_value = get_counter_value(counter_id)
                return func.HttpResponse(
                    json.dumps({
                        "id": counter_id,
                        "count": current_value,
                        "action": "read"
                    }),
                    mimetype="application/json"
                )
        
        elif method == "POST":
            # Incrémenter le compteur (+1)
            current_value = get_counter_value(counter_id)
            new_value = current_value + 1
            
            if update_counter_value(counter_id, new_value):
                return func.HttpResponse(
                    json.dumps({
                        "id": counter_id,
                        "count": new_value,
                        "previous": current_value,
                        "action": "increment"
                    }),
                    mimetype="application/json"
                )
            else:
                return func.HttpResponse(
                    json.dumps({"error": "Failed to increment counter"}),
                    status_code=500,
                    mimetype="application/json"
                )
        
        elif method == "PUT":
            # Décrémenter le compteur (-1) ou set une valeur spécifique
            try:
                req_body = req.get_json()
                if req_body and 'value' in req_body:
                    # Set une valeur spécifique
                    new_value = int(req_body['value'])
                    action = "set"
                else:
                    # Décrémenter (-1)
                    current_value = get_counter_value(counter_id)
                    new_value = current_value - 1
                    action = "decrement"
                
                if update_counter_value(counter_id, new_value):
                    return func.HttpResponse(
                        json.dumps({
                            "id": counter_id,
                            "count": new_value,
                            "action": action
                        }),
                        mimetype="application/json"
                    )
                else:
                    return func.HttpResponse(
                        json.dumps({"error": f"Failed to {action} counter"}),
                        status_code=500,
                        mimetype="application/json"
                    )
                    
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid value provided"}),
                    status_code=400,
                    mimetype="application/json"
                )
        
        elif method == "DELETE":
            # Supprimer un compteur
            try:
                container = get_cosmos_container()
                container.delete_item(item=counter_id, partition_key=counter_id)
                
                return func.HttpResponse(
                    json.dumps({
                        "id": counter_id,
                        "action": "deleted"
                    }),
                    mimetype="application/json"
                )
                
            except exceptions.CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": f"Counter '{counter_id}' not found"}),
                    status_code=404,
                    mimetype="application/json"
                )
            except Exception as e:
                return func.HttpResponse(
                    json.dumps({"error": f"Failed to delete counter: {str(e)}"}),
                    status_code=500,
                    mimetype="application/json"
                )
        
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f'Exception in counter function: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check pour vérifier la connexion Cosmos DB"""
    try:
        # Test de connexion à Cosmos DB
        container = get_cosmos_container()
        
        # Test simple de query
        list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.type = 'counter'",
            enable_cross_partition_query=True
        ))
        
        return func.HttpResponse(
            json.dumps({
                "status": "healthy",
                "cosmos_db": "connected",
                "timestamp": func.utcnow().isoformat()
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "unhealthy",
                "cosmos_db": "disconnected",
                "error": str(e),
                "timestamp": func.utcnow().isoformat()
            }),
            status_code=503,
            mimetype="application/json"
        )