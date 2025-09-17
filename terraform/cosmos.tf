# Create Cosmos DB Account
resource "azurerm_cosmosdb_account" "counter_db" {
  name                = coalesce(var.cosmos_account_name, "cosmos-${random_string.name.result}")
  location            = azurerm_resource_group.vladimirpoutine69.location
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  geo_location {
    location          = azurerm_resource_group.vladimirpoutine69.location
    failover_priority = 0
  }

  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 300
    max_staleness_prefix    = 100000
  }

  depends_on = [
    azurerm_resource_group.vladimirpoutine69
  ]
}

# Create Cosmos DB SQL Database
resource "azurerm_cosmosdb_sql_database" "counter_database" {
  name                = "counterdb"
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  throughput          = 400
}

# Create Cosmos DB SQL Container (equivalent to table)
resource "azurerm_cosmosdb_sql_container" "counter_container" {
  name                  = "counters"
  resource_group_name   = azurerm_resource_group.vladimirpoutine69.name
  account_name          = azurerm_cosmosdb_account.counter_db.name
  database_name         = azurerm_cosmosdb_sql_database.counter_database.name
  partition_key_paths   = ["/id"]
  partition_key_version = 1
  throughput            = 400
}

# Le data commenté la en dessous fonctionne mais je trouve ca degeulasse et pas maintenable
# Je préfère créer un rôle custom avec les permissions minimales nécessaires

# # Utiliser une data source pour récupérer le rôle
# data "azurerm_cosmosdb_sql_role_definition" "cosmos_db_data_contributor" {
#   resource_group_name = azurerm_resource_group.vladimirpoutine69.name
#   account_name        = azurerm_cosmosdb_account.counter_db.name
#   role_definition_id  = "00000000-0000-0000-0000-000000000002"  # Built-in Data Contributor
# }

resource "azurerm_cosmosdb_sql_role_definition" "counter_admin" {
  name                = "counter-admin"
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  type               = "CustomRole"
  assignable_scopes  = [
    azurerm_cosmosdb_account.counter_db.id  # Peut être assigné sur tout le compte
  ]

  permissions {
    data_actions = [
      # Métadonnées nécessaires pour le SDK
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      
      # Accès complet aux containers (pour lire/écrire dans 'counters')
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*",
      
      # Accès complet aux documents dans les containers
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*"
    ]
  }
}


resource "azurerm_cosmosdb_sql_role_assignment" "function_cosmos_access_v2" {
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  scope              = azurerm_cosmosdb_account.counter_db.id
  role_definition_id = azurerm_cosmosdb_sql_role_definition.counter_admin.id
  principal_id       = azurerm_linux_function_app.vladimirpoutine69.identity[0].principal_id
  
  depends_on = [azurerm_linux_function_app.vladimirpoutine69]
}