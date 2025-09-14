import azure.functions as func
import json
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    
    # Test 1: Vérifier les variables d'environnement
    endpoint = os.environ.get('COSMOS_DB_ENDPOINT')
    if not endpoint:
        return func.HttpResponse(json.dumps({"error": "Missing COSMOS_DB_ENDPOINT"}))
    
    # Test 2: Essayer l'import azure-cosmos
    try:
        from azure.cosmos import CosmosClient
    except ImportError:
        return func.HttpResponse(json.dumps({"error": "azure-cosmos not installed"}))
    
    # Test 3: Essayer la connexion
    try:
        client = CosmosClient(endpoint, os.environ['COSMOS_DB_KEY'])
        return func.HttpResponse(json.dumps({"status": "cosmos connection ok"}))
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": f"Cosmos error: {str(e)}"}))