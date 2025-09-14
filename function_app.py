import azure.functions as func
import json
import os
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def get_env_variable(key):
    """Try multiple methods to get environment variable"""
    methods = {}
    
    # Method 1: os.environ.get()
    try:
        value = os.environ.get(key)
        methods["os.environ.get"] = {"value": value, "success": bool(value)}
    except Exception as e:
        methods["os.environ.get"] = {"error": str(e), "success": False}
    
    # Method 2: os.getenv()
    try:
        value = os.getenv(key)
        methods["os.getenv"] = {"value": value, "success": bool(value)}
    except Exception as e:
        methods["os.getenv"] = {"error": str(e), "success": False}
    
    # Method 3: Direct access
    try:
        value = os.environ[key]
        methods["os.environ[key]"] = {"value": value, "success": bool(value)}
    except Exception as e:
        methods["os.environ[key]"] = {"error": str(e), "success": False}
    
    # Method 4: Check if it exists with a different name
    try:
        similar_keys = [k for k in os.environ.keys() if key.upper() in k.upper()]
        methods["similar_keys"] = {"keys": similar_keys, "success": len(similar_keys) > 0}
    except Exception as e:
        methods["similar_keys"] = {"error": str(e), "success": False}
    
    return methods

@app.route(route="debug-env", methods=["GET"])
def debug_env(req: func.HttpRequest) -> func.HttpResponse:
    """Debug all environment access methods"""
    
    # Test each Cosmos variable
    cosmos_vars = ["COSMOS_DB_ENDPOINT", "COSMOS_DB_KEY", "COSMOS_DB_DATABASE", "COSMOS_DB_CONTAINER"]
    results = {}
    
    for var in cosmos_vars:
        results[var] = get_env_variable(var)
    
    # Also list ALL environment variables
    all_env = dict(os.environ)
    
    return func.HttpResponse(
        json.dumps({
            "cosmos_variable_tests": results,
            "total_env_vars": len(all_env),
            "env_keys_sample": list(all_env.keys())[:20],
            "cosmos_related_keys": [k for k in all_env.keys() if 'COSMOS' in k.upper()]
        }, indent=2),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )