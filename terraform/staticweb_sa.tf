
# ========================================
# STORAGE ACCOUNT DÉDIÉ POUR LE SITE WEB STATIQUE
# ========================================

# Storage Account séparé pour le site web statique
resource "azurerm_storage_account" "static_website" {
  name                     = "static${var.sa_staticweb_name}"
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
