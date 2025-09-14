output "resource_group_name" {
  value = azurerm_resource_group.vladimirpoutine69.name
}

output "sa_name" {
  value = azurerm_storage_account.vladimirpoutine69.name
}

output "asp_name" {
  value = azurerm_service_plan.vladimirpoutine69.name
}

output "fa_name" {
  value = azurerm_linux_function_app.vladimirpoutine69.name
}

output "fa_url" {
  value = "https://${azurerm_linux_function_app.vladimirpoutine69.name}.azurewebsites.net"
}

# Outputs utiles pour GitHub Actions
output "github_actions_info" {
  description = "Information needed for GitHub Actions"
  value = {
    function_app_name   = azurerm_linux_function_app.vladimirpoutine69.name
    resource_group_name = azurerm_resource_group.vladimirpoutine69.name
    subscription_id     = data.azurerm_client_config.current.subscription_id
    tenant_id           = data.azurerm_client_config.current.tenant_id
  }
}

output "cosmos_db_endpoint" {
  description = "Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.counter_db.endpoint
}