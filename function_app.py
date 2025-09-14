import azure.functions as func
import json
import os
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Config Cosmos DB (variables d'environnement)
client = CosmosClient(os.environ['COSMOS_DB_ENDPOINT'], os.environ['COSMOS_DB_KEY'])
database = client.get_database_client(os.environ['COSMOS_DB_DATABASE'])
container = database.get_container_client(os.environ['COSMOS_DB_CONTAINER'])

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    
    if req.method == "GET":
        # Lire le compteur
        try:
            item = container.read_item("counter", partition_key="counter")
            count = item['value']
        except:
            count = 0
            
        return func.HttpResponse(json.dumps({"count": count}))
    
    elif req.method == "POST":
        # Incrémenter le compteur
        try:
            item = container.read_item("counter", partition_key="counter")
            count = item['value'] + 1
        except:
            count = 1
            
        # Sauvegarder
        container.upsert_item({
            "id": "counter", 
            "value": count
        })
        
        return func.HttpResponse(json.dumps({"count": count}))