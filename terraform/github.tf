######## GitHub deployment setup #######
######## Attention need créer service principal manuellement - check README ########

# Assign Website Contributor role to Service Principal
resource "azurerm_role_assignment" "github_actions_website" {
  scope                = azurerm_resource_group.vladimirpoutine69.id
  role_definition_name = "Website Contributor"
  principal_id         = var.github_actions_object_id
}

# Assign Storage Blob Data Contributor role (needed for deployments)
resource "azurerm_role_assignment" "github_actions_storage" {
  scope                = azurerm_storage_account.vladimirpoutine69.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.github_actions_object_id
}