# This Terraform configuration creates a Flex Consumption plan app in Azure Functions 
# with the required Storage account and Blob Storage deployment container.

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

# Create a storage container
resource "azurerm_storage_container" "vladimirpoutine69" {
  name                  = "vladimirpoutine69-flexcontainer"
  storage_account_id    = azurerm_storage_account.vladimirpoutine69.id
  container_access_type = "private"
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

# Create a service plan
resource "azurerm_service_plan" "vladimirpoutine69" {
  name                = coalesce(var.asp_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  sku_name            = "FC1"
  os_type             = "Linux"
}

# Create a function app
resource "azurerm_function_app_flex_consumption" "vladimirpoutine69" {
  name                = coalesce(var.fa_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  service_plan_id     = azurerm_service_plan.vladimirpoutine69.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.vladimirpoutine69.primary_blob_endpoint}${azurerm_storage_container.vladimirpoutine69.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.vladimirpoutine69.primary_access_key
  runtime_name                = var.runtime_name
  runtime_version             = var.runtime_version
  maximum_instance_count      = 50
  instance_memory_in_mb       = 2048

  site_config {
    # Configuration pour Application Insights
    application_insights_connection_string = azurerm_application_insights.vladimirpoutine69.connection_string
    application_insights_key               = azurerm_application_insights.vladimirpoutine69.instrumentation_key
  }

  app_settings = {
     "AzureWebJobsStorage"       = "DefaultEndpointsProtocol=https;AccountName=${azurerm_storage_account.vladimirpoutine69.name};AccountKey=${azurerm_storage_account.vladimirpoutine69.primary_access_key};EndpointSuffix=core.windows.net"

    "COSMOS_DB_ENDPOINT"    = azurerm_cosmosdb_account.counter_db.endpoint
    "COSMOS_DB_KEY"         = azurerm_cosmosdb_account.counter_db.primary_key
    "COSMOS_DB_DATABASE"    = azurerm_cosmosdb_sql_database.counter_database.name
    "COSMOS_DB_CONTAINER"   = azurerm_cosmosdb_sql_container.counter_container.name
  }

  depends_on = [ azurerm_cosmosdb_sql_container.counter_container, azurerm_cosmosdb_sql_database.counter_database, azurerm_cosmosdb_account.counter_db ]
}
