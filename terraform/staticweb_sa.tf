# ========================================
# STORAGE ACCOUNT DÉDIÉ POUR LE SITE WEB STATIQUE
# ========================================

resource "azurerm_storage_account" "static_website" {
  name                     = "static${var.sa_staticweb_name}"
  resource_group_name      = azurerm_resource_group.vladimirpoutine69.name
  location                 = azurerm_resource_group.vladimirpoutine69.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  static_website {
    index_document = "index.html"
  }

  # Pas besoin de CORS ici - MSAL gère tout côté client
  # Les appels API vers la Function App sont gérés par CORS de la Function App
}

# Upload du fichier HTML avec injection des valeurs Entra ID et API URL
resource "azurerm_storage_blob" "index_html" {
  name                   = "index.html"
  storage_account_name   = azurerm_storage_account.static_website.name
  storage_container_name = "$web"
  type                   = "Block"
  content_type           = "text/html"

  # Triple replacement : CLIENT_ID, TENANT_ID, API_URL
  source_content = replace(
    replace(
      replace(
        file("${path.module}/../website/index.html"),
        "COUNTER_CLIENT_ID",
        var.entra_client_id
      ),
      "COUNTER_TENANT_ID",
      var.tenant_id
    ),
    "COUNTER_API_URL",
    "https://${azurerm_linux_function_app.vladimirpoutine69.default_hostname}"
  )
}

# Upload des autres fichiers du site web (CSS, images, etc.) - optionnel
# Si tu as d'autres fichiers dans website/ (logos, images, etc.)
resource "azurerm_storage_blob" "website_assets" {
  for_each = toset([
    for file in fileset("${path.module}/../website", "*") : file
    if file != "index.html" && file != "script.js.tpl" && file != "staticwebapp.config.json"
  ])

  name                   = each.value
  storage_account_name   = azurerm_storage_account.static_website.name
  storage_container_name = "$web"
  type                   = "Block"
  source                 = "${path.module}/../website/${each.value}"

  content_type = lookup({
    "css"  = "text/css"
    "js"   = "application/javascript"
    "json" = "application/json"
    "png"  = "image/png"
    "jpg"  = "image/jpeg"
    "jpeg" = "image/jpeg"
    "svg"  = "image/svg+xml"
    "ico"  = "image/x-icon"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")
}