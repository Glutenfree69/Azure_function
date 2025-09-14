import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient  # Import au début
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    # Debug complet
    endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
    key = os.environ.get('COSMOS_DB_KEY')
    
    # Retourner plus d'infos de debug
    debug_info = {
        "endpoint": endpoint,
        "key_exists": bool(key),
        "key_length": len(key) if key else 0,
        "all_cosmos_vars": {k: v for k, v in os.environ.items() if 'COSMOS' in k.upper()}
    }
    
    if not endpoint:
        return func.HttpResponse(
            json.dumps({"error": "Missing COSMOS_DB_ENDPOINT", "debug": debug_info}),
            status_code=500
        )
    
    try:
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(os.environ['COSMOS_DB_DATABASE'])
        container = database.get_container_client(os.environ['COSMOS_DB_CONTAINER'])
        
        return func.HttpResponse(
            json.dumps({"status": "cosmos connection ok", "debug": debug_info})
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Cosmos error: {str(e)}", "debug": debug_info}),
            status_code=500
        )