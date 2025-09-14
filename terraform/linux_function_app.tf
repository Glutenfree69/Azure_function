resource "azurerm_linux_function_app" "glutenfree69" {
  name                = "glutenfree69"
  resource_group_name = azurerm_resource_group.glutenfree69.name
  location            = azurerm_resource_group.glutenfree69.location

  storage_account_name       = azurerm_storage_account.glutenfree69.name
  storage_account_access_key = azurerm_storage_account.glutenfree69.primary_access_key
  service_plan_id            = azurerm_service_plan.glutenfree69.id

  # Paramètres manquants détectés dans le plan
  builtin_logging_enabled     = false
  client_certificate_mode     = "Required"
  functions_extension_version = "~4"

  # Zip deploy
  zip_deploy_file = data.archive_file.function_zip.output_path

  # App settings actuels
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "WEBSITE_RUN_FROM_PACKAGE" = "1"
    "AzureWebJobsStorage" = "DefaultEndpointsProtocol=https;AccountName=${azurerm_storage_account.glutenfree69.name};AccountKey=${azurerm_storage_account.glutenfree69.primary_access_key};EndpointSuffix=core.windows.net"
  }

  # Tags actuels
  tags = {
    "hidden-link: /app-insights-resource-id" = azurerm_application_insights.glutenfree69.id
  }

  # Identité managée
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.glutenfree69.id]
  }

  site_config {
    # Application Insights connection string (sensible)
    application_insights_connection_string = azurerm_application_insights.glutenfree69.connection_string
    ftps_state                             = "FtpsOnly"
    ip_restriction_default_action          = "Allow"
    scm_ip_restriction_default_action      = "Allow"

    application_stack {
      python_version = "3.12"
    }
  }

  # Dépendance pour s'assurer que le zip est créé avant le déploiement
  depends_on = [data.archive_file.function_zip]
}