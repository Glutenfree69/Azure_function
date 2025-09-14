resource "azurerm_application_insights" "glutenfree69" {
  name                = "glutenfree69"
  resource_group_name = azurerm_resource_group.glutenfree69.name
  location            = azurerm_resource_group.glutenfree69.location
  application_type    = "web"

  sampling_percentage = 0
  workspace_id        = "/subscriptions/249471bf-b8ae-4c8a-abf4-f9e67509e192/resourceGroups/DefaultResourceGroup-PAR/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-249471bf-b8ae-4c8a-abf4-f9e67509e192-PAR"
}