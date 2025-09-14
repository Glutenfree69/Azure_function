resource "azurerm_user_assigned_identity" "glutenfree69" {
  name                = "glutenfree69-identities-4f6283"
  resource_group_name = azurerm_resource_group.glutenfree69.name
  location            = azurerm_resource_group.glutenfree69.location
}