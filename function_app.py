import azure.functions as func
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    
    if req.method == "GET":
        return func.HttpResponse(json.dumps({"count": 0}))
    
    elif req.method == "POST":
        return func.HttpResponse(json.dumps({"count": 1}))