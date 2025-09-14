# Data source pour créer le zip avec tous les fichiers de fonction
data "archive_file" "function_zip" {
  type        = "zip"
  output_path = "function.zip"

  source {
    content  = file("../function_app.py")
    filename = "function_app.py"
  }

  source {
    content  = file("../requirements.txt")
    filename = "requirements.txt"
  }

  source {
    content = jsonencode({
      "version": "2.0",
      "logging": {
        "applicationInsights": {
          "samplingSettings": {
            "isEnabled": true,
            "excludedTypes": "Request"
          }
        }
      },
      "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)"
      },
      "functionTimeout": "00:05:00"
    })
    filename = "host.json"
  }
}