# resource "azurerm_function_app_function" "glutenfree69" {
#   name            = "counter_function"
#   function_app_id = azurerm_linux_function_app.glutenfree69.id
#   language        = "Python"

#   file {
#     name    = "__init__.py"
#     content = file("../function_app.py")
#   }

#   file {
#     name    = "requirements.txt"
#     content = file("../requirements.txt")
#   }

#   file {
#     name    = "host.json"
#     content = file("../host.json")
#   }

#   config_json = jsonencode({
#     "bindings" = [
#       {
#         "authLevel" = "function"
#         "type"      = "httpTrigger"
#         "direction" = "in"
#         "name"      = "req"
#         "methods"   = ["get", "post"]
#         "route"     = "counter"
#       },
#       {
#         "type"      = "http"
#         "direction" = "out"
#         "name"      = "$return"
#       }
#     ]
#   })
# }