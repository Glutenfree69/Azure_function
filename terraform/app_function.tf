# This Terraform configuration creates a Consumption plan app in Azure Functions
# with the required Storage account and Application Insights.

# Create a resource group
resource "azurerm_resource_group" "vladimirpoutine69" {
  location = var.resource_group_location
  name     = coalesce("rg-${var.resource_group_name}", random_pet.rg_name.id)
}

# Create a storage account
resource "azurerm_storage_account" "vladimirpoutine69" {
  name                     = coalesce(var.sa_name, random_string.name.result)
  resource_group_name      = azurerm_resource_group.vladimirpoutine69.name
  location                 = azurerm_resource_group.vladimirpoutine69.location
  account_tier             = var.sa_account_tier
  account_replication_type = var.sa_account_replication_type
}

# Create a Log Analytics workspace for Application Insights
resource "azurerm_log_analytics_workspace" "vladimirpoutine69" {
  name                = coalesce(var.ws_name, random_string.name.result)
  location            = azurerm_resource_group.vladimirpoutine69.location
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# Create an Application Insights instance for monitoring
resource "azurerm_application_insights" "vladimirpoutine69" {
  name                = coalesce(var.ai_name, random_string.name.result)
  location            = azurerm_resource_group.vladimirpoutine69.location
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.vladimirpoutine69.id
}

# Create a service plan (Consumption plan - Y1)
resource "azurerm_service_plan" "vladimirpoutine69" {
  name                = coalesce(var.asp_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  sku_name            = "Y1"
  os_type             = "Linux"
}

# Create a function app
resource "azurerm_linux_function_app" "vladimirpoutine69" {
  name                = coalesce(var.fa_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  service_plan_id     = azurerm_service_plan.vladimirpoutine69.id

  # Storage configuration
  storage_account_name       = azurerm_storage_account.vladimirpoutine69.name
  storage_account_access_key = azurerm_storage_account.vladimirpoutine69.primary_access_key

  # MANAGED IDENTITY (équivalent IAM Role)
  identity {
    type = "SystemAssigned"
  }

  site_config {
    # Configuration pour Application Insights
    application_insights_connection_string = azurerm_application_insights.vladimirpoutine69.connection_string
    application_insights_key               = azurerm_application_insights.vladimirpoutine69.instrumentation_key

    # Python configuration (ADDED: Required for Consumption plan)
    application_stack {
      python_version = var.runtime_version
    }

    cors {
      allowed_origins = [
        # azurerm_storage_account.static_website.primary_web_endpoint,
        # "https://portal.azure.com"
        "*"
      ]
      support_credentials = false
    }
  }

  # App settings - These will work properly with Consumption plan!
  app_settings = {
    # Cosmos DB settings
    "COSMOS_DB_ENDPOINT"  = azurerm_cosmosdb_account.counter_db.endpoint
    # "COSMOS_DB_KEY"       = azurerm_cosmosdb_account.counter_db.primary_key
    "COSMOS_DB_DATABASE"  = azurerm_cosmosdb_sql_database.counter_database.name
    "COSMOS_DB_CONTAINER" = azurerm_cosmosdb_sql_container.counter_container.name

    "COSMOS_DB_USE_MANAGED_IDENTITY" = "true"
  }

  # Dependencies
  depends_on = [
    azurerm_cosmosdb_sql_container.counter_container,
    azurerm_cosmosdb_sql_database.counter_database,
    azurerm_cosmosdb_account.counter_db
  ]

  lifecycle {
    ignore_changes = [tags]
  }
}

# ========================================
# STORAGE ACCOUNT DÉDIÉ POUR LE SITE WEB STATIQUE
# ========================================

# Storage Account séparé pour le site web statique
resource "azurerm_storage_account" "static_website" {
  name                     = "staticweb${random_string.name.result}"
  resource_group_name      = azurerm_resource_group.vladimirpoutine69.name
  location                 = azurerm_resource_group.vladimirpoutine69.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Enable static website hosting
  static_website {
    index_document     = "index.html"
    error_404_document = "404.html"
  }

  blob_properties {
    # CORS pour permettre les appels à ton API Function
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }


}

# Génération du script.js avec l'URL dynamique
resource "azurerm_storage_blob" "script_js" {
  name                   = "script.js"
  storage_account_name   = azurerm_storage_account.static_website.name
  storage_container_name = "$web"
  type                   = "Block"
  content_type           = "application/javascript"

  # Utilise le template avec l'URL de la Function App
  source_content = templatefile("${path.module}/../website/script.js.tpl", {
    function_app_url = "https://${azurerm_linux_function_app.vladimirpoutine69.default_hostname}"
  })
}

# Upload des autres fichiers du site web (HTML, CSS)
resource "azurerm_storage_blob" "website_files" {
  for_each = toset([
    for file in fileset("${path.module}/../website", "*") : file
    if file != "script.js.tpl"
  ])

  name                   = each.value
  storage_account_name   = azurerm_storage_account.static_website.name
  storage_container_name = "$web"
  type                   = "Block"
  source                 = "${path.module}/../website/${each.value}"

  content_type = lookup({
    "html" = "text/html"
    "css"  = "text/css"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")
}