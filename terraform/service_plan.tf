resource "azurerm_service_plan" "glutenfree69" {
  name                = "FLEX-glutenfree69-d7c3"
  resource_group_name = azurerm_resource_group.glutenfree69.name
  location            = azurerm_resource_group.glutenfree69.location
  os_type             = "Linux"
  sku_name            = "B1"
}