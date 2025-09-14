import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="counter", methods=["GET", "POST"])
def counter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Counter function test - basic version')
    
    try:
        method = req.method
        logging.info(f'Method: {method}')
        
        if method == "POST":
            return func.HttpResponse(
                json.dumps({"count": 42, "action": "test"}),
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                "<h1>Test Function</h1><p>Cette fonction fonctionne !</p>",
                mimetype="text/html"
            )
            
    except Exception as e:
        logging.error(f'Exception in test function: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Exception: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )