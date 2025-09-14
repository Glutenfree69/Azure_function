resource "azurerm_storage_account" "glutenfree69" {
  name                     = "glutenfree69"
  resource_group_name      = azurerm_resource_group.glutenfree69.name
  location                 = azurerm_resource_group.glutenfree69.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Les arguments ci dessous ont été rajouté suite au terraform import pour correspondre à la conf de la console
  account_kind                     = "Storage"
  allow_nested_items_to_be_public  = "false"
  cross_tenant_replication_enabled = "false"
  default_to_oauth_authentication  = "true"
  min_tls_version                  = "TLS1_0"
}