# Documentation: Azure Functions avec Terraform et GitHub Actions

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture du projet](#architecture-du-projet)
- [Infrastructure Terraform](#infrastructure-terraform)
- [Site web statique](#site-web-statique)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Déploiement et sécurité](#déploiement-et-sécurité)
- [Troubleshooting](#troubleshooting)
- [Bonnes pratiques](#bonnes-pratiques)

## Vue d'ensemble

Ce projet déploie une Azure Function App avec un site web statique en utilisant Terraform et un pipeline de déploiement automatisé (GitHub Actions). L'architecture utilise le plan **Consumption Plan (Y1)** pour les fonctions et **Azure Storage Static Website** pour l'interface utilisateur.

### Technologies utilisées

- **Azure Functions** : Plateforme serverless pour exécuter du code event-driven
- **Azure Cosmos DB** : Base de données NoSQL pour la persistance des données
- **Azure Storage Static Website** : Hébergement statique pour l'interface web
- **Terraform** : Infrastructure as Code pour provisionner les ressources Azure
- **GitHub Actions** : CI/CD pour automatiser le déploiement
- **Python 3.11** : Runtime de la fonction
- **Azure RBAC** : Authentification sécurisée pour le déploiement

## Architecture du projet

### Structure des fichiers

```
AZURE_FUNCTION/
├── .github/
│   └── workflows/
│       └── azure-function-app-python.yml  # Pipeline GitHub Actions
├── terraform/
│   ├── app_function.tf             # Ressources Function App principales
│   ├── staticweb_sa.tf             # Storage Account pour site web statique
│   ├── cosmos.tf                   # Ressources Cosmos DB
│   ├── github.tf                   # Configuration RBAC GitHub Actions
│   ├── variables.tf                # Variables Terraform
│   ├── outputs.tf                  # Outputs Terraform
│   ├── data.tf                     # Sources de données
│   ├── random.tf                   # Ressources aléatoires
│   ├── terraform.tf                # Configuration Terraform
│   └── terraform.tfvars            # Valeurs des variables
├── website/
│   ├── index.html                  # Interface utilisateur principale
│   ├── style.css                   # Styles CSS responsifs
│   └── script.js.tpl               # Template JavaScript avec URL dynamique
├── function_app.py                 # Code de la fonction principale
├── host.json                       # Configuration Azure Functions
├── requirements.txt                # Dépendances Python
├── local.settings.json             # Configuration locale (dev)
└── README.md                       # Documentation
```

### Flux de déploiement

```mermaid
graph TD
    A[Code Push vers GitHub] --> B[GitHub Actions Trigger]
    B --> C[Setup Python Environment]
    C --> D[Install Dependencies]
    D --> E[Create ZIP Package]
    E --> F[Azure CLI Login avec RBAC]
    F --> G[Deploy ZIP to Function App]
    G --> H[Function App Running]
    H --> I[Cosmos DB Storage]
    J[Static Website deployed] --> K[User Interface]
    K --> H
    H --> L[JSON API Response]
```

## Infrastructure Terraform

### Ressources créées

#### 1. Resource Group
```hcl
resource "azurerm_resource_group" "vladimirpoutine69" {
  location = var.resource_group_location
  name     = coalesce("rg-${var.resource_group_name}", random_pet.rg_name.id)
}
```

**Rôle** : Conteneur logique pour toutes les ressources du projet

#### 2. Storage Account (Function App)
```hcl
resource "azurerm_storage_account" "vladimirpoutine69" {
  name                     = coalesce(var.sa_name, random_string.name.result)
  resource_group_name      = azurerm_resource_group.vladimirpoutine69.name
  location                 = azurerm_resource_group.vladimirpoutine69.location
  account_tier             = var.sa_account_tier
  account_replication_type = var.sa_account_replication_type
}
```

**Rôle** : 
- Stockage du code de la fonction (deployment packages)
- Stockage des logs et métadonnées
- Support pour les triggers et bindings Azure Functions

#### 3. Storage Account (Site Web Statique)
```hcl
resource "azurerm_storage_account" "static_website" {
  name                     = "static${var.sa_staticweb_name}"
  resource_group_name      = azurerm_resource_group.vladimirpoutine69.name
  location                 = azurerm_resource_group.vladimirpoutine69.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  static_website {
    index_document     = "index.html"
    error_404_document = "404.html"
  }

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }
}
```

**Rôle** : 
- Hébergement du site web statique (HTML, CSS, JS)
- Configuration CORS pour les appels API vers la Function App
- CDN intégré pour la distribution globale
- HTTPS automatique

**Configuration** :
- Container `$web` créé automatiquement
- Document d'index : `index.html`
- Page d'erreur 404 : `404.html`
- CORS configuré pour permettre les appels cross-origin

#### 4. Log Analytics Workspace
```hcl
resource "azurerm_log_analytics_workspace" "vladimirpoutine69" {
  name                = coalesce(var.ws_name, random_string.name.result)
  location            = azurerm_resource_group.vladimirpoutine69.location
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}
```

**Rôle** : Collecte et analyse des logs pour Application Insights

#### 5. Application Insights
```hcl
resource "azurerm_application_insights" "vladimirpoutine69" {
  name                = coalesce(var.ai_name, random_string.name.result)
  location            = azurerm_resource_group.vladimirpoutine69.location
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.vladimirpoutine69.id
}
```

**Rôle** : 
- Monitoring des performances de l'API et du site web
- Collecte des logs applicatifs
- Debugging et diagnostics

#### 6. Service Plan (Consumption Y1)
```hcl
resource "azurerm_service_plan" "vladimirpoutine69" {
  name                = coalesce(var.asp_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  sku_name            = "Y1"
  os_type             = "Linux"
}
```

**Caractéristiques Y1** :
- **Facturation** : Pay-per-execution + GB-secondes de mémoire utilisée
- **Scaling** : 0 à 200 instances automatiquement (Windows) / 0 à 100 instances (Linux)
- **Démarrage à froid** : Présent, temps de démarrage variable selon la complexité de l'app
- **Limitations** : 10 minutes max par exécution, pas de connectivité VNet native
- **OS** : Windows et Linux supportés

#### 7. Cosmos DB Account
```hcl
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
}
```

**Rôle** : 
- Base de données NoSQL distribuée globalement
- Stockage des données de l'application de compteur
- Haute disponibilité et consistance configurée

**Configuration** :
- **Offer Type** : Standard
- **Kind** : GlobalDocumentDB (API SQL)
- **Consistency Level** : BoundedStaleness (équilibre entre performance et consistance)
- **Geo-location** : Single region (France Central)

#### 8. Cosmos DB SQL Database
```hcl
resource "azurerm_cosmosdb_sql_database" "counter_database" {
  name                = "counterdb"
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  throughput          = 400
}
```

**Rôle** : Base de données SQL dans le compte Cosmos DB

**Configuration** :
- **Throughput** : 400 RU/s (Request Units par seconde)
- **Facturation** : Basée sur les RU/s provisionnées

#### 9. Cosmos DB SQL Container
```hcl
resource "azurerm_cosmosdb_sql_container" "counter_container" {
  name                  = "counters"
  resource_group_name   = azurerm_resource_group.vladimirpoutine69.name
  account_name          = azurerm_cosmosdb_account.counter_db.name
  database_name         = azurerm_cosmosdb_sql_database.counter_database.name
  partition_key_paths   = ["/id"]
  partition_key_version = 1
  throughput            = 400
}
```

**Rôle** : Container (équivalent d'une table) pour stocker les documents de compteur

**Configuration** :
- **Partition Key** : `/id` (clé de partitionnement pour la distribution des données)
- **Throughput** : 400 RU/s dédié au container

#### 10. Cosmos DB Custom Role Definition
```hcl
resource "azurerm_cosmosdb_sql_role_definition" "counter_admin" {
  name                = "counter-admin"
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  type               = "CustomRole"
  assignable_scopes  = [
    azurerm_cosmosdb_account.counter_db.id
  ]

  permissions {
    data_actions = [
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*"
    ]
  }
}
```

**Rôle** : Définition de rôle personnalisé pour l'accès sécurisé à Cosmos DB

**Avantages par rapport aux clés** :
- **Sécurité** : Utilise l'identité managée de la Function App (pas de clés à gérer)
- **Permissions granulaires** : Accès limité aux opérations nécessaires uniquement
- **Rotation automatique** : Pas de rotation manuelle des clés
- **Audit** : Traçabilité via Azure AD

**Permissions accordées** :
- `readMetadata` : Lecture des métadonnées du compte
- `containers/*` : Accès complet aux containers
- `items/*` : Accès complet aux documents

#### 11. Cosmos DB Role Assignment
```hcl
resource "azurerm_cosmosdb_sql_role_assignment" "function_cosmos_access_v2" {
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  account_name        = azurerm_cosmosdb_account.counter_db.name
  scope              = azurerm_cosmosdb_account.counter_db.id
  role_definition_id = azurerm_cosmosdb_sql_role_definition.counter_admin.id
  principal_id       = azurerm_linux_function_app.vladimirpoutine69.identity[0].principal_id
}
```

**Rôle** : Assignation du rôle personnalisé à l'identité managée de la Function App

**Sécurité** :
- Utilise l'identité managée système de la Function App
- Évite l'utilisation des clés d'accès dans les app settings
- Principe du moindre privilège appliqué

#### 12. Function App
```hcl
resource "azurerm_linux_function_app" "vladimirpoutine69" {
  name                = coalesce(var.fa_name, random_string.name.result)
  resource_group_name = azurerm_resource_group.vladimirpoutine69.name
  location            = azurerm_resource_group.vladimirpoutine69.location
  service_plan_id     = azurerm_service_plan.vladimirpoutine69.id

  storage_account_name       = azurerm_storage_account.vladimirpoutine69.name
  storage_account_access_key = azurerm_storage_account.vladimirpoutine69.primary_access_key

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_insights_connection_string = azurerm_application_insights.vladimirpoutine69.connection_string
    application_insights_key               = azurerm_application_insights.vladimirpoutine69.instrumentation_key

    application_stack {
      python_version = var.runtime_version
    }

    cors {
      allowed_origins = ["*"]
      support_credentials = false
    }
  }

  app_settings = {
    "COSMOS_DB_ENDPOINT"             = azurerm_cosmosdb_account.counter_db.endpoint
    "COSMOS_DB_DATABASE"             = azurerm_cosmosdb_sql_database.counter_database.name
    "COSMOS_DB_CONTAINER"            = azurerm_cosmosdb_sql_container.counter_container.name
    "COSMOS_DB_USE_MANAGED_IDENTITY" = "true"
  }
}
```

**Configuration** :
- **Runtime** : Python 3.11
- **OS** : Linux
- **Identité managée** : Activée pour l'accès sécurisé à Cosmos DB
- **CORS** : Configuré pour autoriser tous les origins (permissif pour le développement)
- **Variables d'environnement Cosmos DB** : Endpoint, base de données et container (sans clé)
- **Storage** : Connection automatique au Storage Account

## Site web statique

### Architecture du site web

Le site web statique est hébergé sur Azure Storage et fournit une interface utilisateur moderne pour interagir avec l'API Azure Functions.

#### Fichiers du site web

##### 1. Interface utilisateur ([website/index.html](website/index.html))

**Fonctionnalités** :
- **URL dynamique** : L'URL de l'API est injectée par Terraform
- **Gestion d'erreurs** : Affichage d'états d'erreur appropriés
- **Indicateurs visuels** : États de chargement et hors ligne
- **API REST** : Appels GET/POST vers l'Azure Function

### Déploiement automatique du site web

#### Configuration Terraform pour les blobs
```hcl
# Génération du script.js avec l'URL dynamique
resource "azurerm_storage_blob" "script_js" {
  name                   = "script.js"
  storage_account_name   = azurerm_storage_account.static_website.name
  storage_container_name = "$web"
  type                   = "Block"
  content_type           = "application/javascript"

  source_content = templatefile("${path.module}/../website/script.js.tpl", {
    function_app_url = "https://${azurerm_linux_function_app.vladimirpoutine69.default_hostname}"
  })
}

# Upload des autres fichiers du site web
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
```

**Avantages** :
- **Déploiement automatique** : Les fichiers sont uploadés automatiquement lors du `terraform apply`
- **URL dynamique** : Le script JavaScript reçoit automatiquement l'URL de la Function App
- **Types MIME corrects** : Configuration automatique des content-types
- **Gestion des templates** : Traitement spécial pour les fichiers `.tpl`

### Système de permissions RBAC

#### Problématique des comptes Azure Students
Les comptes Azure Students ont des restrictions sur la création d'applications Azure AD. Solution adoptée :

1. **Création manuelle** du service principal
2. **Assignment automatique** des rôles via Terraform

#### Commandes manuelles requises

##### Création du Service Principal
```bash
# Créer le service principal pour GitHub Actions
az ad sp create-for-rbac \
  --name "sp-github-actions" \
  --skip-assignment \
  --sdk-auth
```

**Output à sauvegarder** : JSON complet pour le secret GitHub `AZURE_RBAC_CREDENTIALS`

##### Récupération de l'Object ID
```bash
# Récupérer l'Object ID avec le Client ID obtenu précédemment
az ad sp show --id "VOTRE-CLIENT-ID" --query id -o tsv
```

**Utilisation** : Passer cette valeur à Terraform via `terraform.tfvars`

#### Rôles assignés
```hcl
resource "azurerm_role_assignment" "github_actions_website" {
  scope                = azurerm_resource_group.vladimirpoutine69.id
  role_definition_name = "Website Contributor"
  principal_id         = var.github_actions_object_id
}

resource "azurerm_role_assignment" "github_actions_storage" {
  scope                = azurerm_storage_account.vladimirpoutine69.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.github_actions_object_id
}
```

**Website Contributor** :
- Déploiement d'applications web
- Gestion des app settings
- Redémarrage des services

**Storage Blob Data Contributor** :
- Upload des packages de déploiement
- Accès aux containers blob

## GitHub Actions CI/CD

### Configuration du workflow

#### Trigger
```yaml
on:
  push:
    branches: ["main" ,"je_lis_la_doc_zzzz"]
```

Le pipeline se déclenche sur chaque push vers les branches `main` et `je_lis_la_doc_zzzz`.

#### Variables d'environnement
```yaml
env:
  AZURE_FUNCTIONAPP_NAME: 'vladimirpoutine69'
  AZURE_FUNCTIONAPP_PACKAGE_PATH: '.'
  PYTHON_VERSION: '3.11'
```

### Étapes du pipeline

#### 1. Checkout du code
```yaml
- name: 'Checkout GitHub Action'
  uses: actions/checkout@v4
```

Récupère le code source depuis le repository.

#### 2. Authentification Azure
```yaml
- name: 'Login via Azure CLI'
  uses: azure/login@v2
  with:
    creds: ${{ secrets.AZURE_RBAC_CREDENTIALS }}
```

#### 3. Setup environnement Python
```yaml
- name: Setup Python ${{ env.PYTHON_VERSION }} Environment
  uses: actions/setup-python@v4
  with:
    python-version: ${{ env.PYTHON_VERSION }}
```

#### 4. Installation des dépendances
```yaml
- name: 'Resolve Project Dependencies Using Pip'
  shell: bash
  run: |
    pushd './${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}'
    python -m pip install --upgrade pip
    pip install -r requirements.txt --target=".python_packages/lib/site-packages"
    popd
```

**Important** : Les dépendances sont installées dans `.python_packages/lib/site-packages/` pour être compatibles avec Azure Functions.

#### 5. Création du package de déploiement
```yaml
- name: 'Create deployment package'
  shell: bash
  run: |
    pushd './${{ env.AZURE_FUNCTIONAPP_PACKAGE_PATH }}'
    zip -r function-app.zip . \
      -x "*.git*" "__pycache__/*" "*.pyc" "venv/*" ".env*" "local.settings.json"
    popd
```

**Fichiers exclus** :
- `.git*` : Historique Git
- `__pycache__/*` : Cache Python
- `venv/*` : Environnement virtuel local
- `.env*` : Variables d'environnement sensibles

#### 6. Déploiement
```yaml
- name: 'Deploy to Azure Functions'
  shell: bash
  run: |
    RG_NAME="rg-vladimirpoutine69" 
    
    az functionapp deployment source config-zip \
      --resource-group $RG_NAME \
      --name ${{ env.AZURE_FUNCTIONAPP_NAME }} \
      --src function-app.zip \
      --build-remote \
      --timeout 300
```

**Méthode** : ZIP deployment via Azure CLI avec build distant

### Sécurité des secrets

#### GitHub Secrets utilisés :
- `AZURE_RBAC_CREDENTIALS` : Credentials complets du service principal

#### App Settings sensibles :
- `AzureWebJobsStorage` : Connection string du storage account (géré automatiquement)
- `APPLICATIONINSIGHTS_CONNECTION_STRING` : Télémétrie (géré automatiquement)
- **Cosmos DB** : Accès via identité managée (pas de clés stockées)

### Application Function - Compteur avec Cosmos DB

L'application implémente un compteur interactif avec interface web utilisant Cosmos DB pour la persistance :

#### Fonctionnalités
- **GET `/api/counter`** : Retourne les données JSON du compteur
- **POST `/api/counter`** : Actions sur le compteur (increment, decrement, reset)
- **OPTIONS `/api/counter`** : Support CORS pour les requêtes cross-origin
- **Persistance** : Données stockées dans Cosmos DB avec identité managée
- **Interface** : Site web statique hébergé sur Azure Storage

#### Structure des données Cosmos DB
```json
{
  "id": "main-counter",
  "value": 42,
  "created_at": "2024-01-01T00:00:00.000Z",
  "last_updated": "2024-01-01T12:30:00.000Z"
}
```

#### Endpoints de l'API
- **URL de l'API** : `https://vladimirpoutine69.azurewebsites.net/api/counter`
- **URL du site web** : URL du endpoint primaire d'Azure Storage Static Website

#### Tests locaux
```bash
# Installer Azure Functions Core Tools - Azurite pour le stockage local
func start

# Tester la fonction
curl http://localhost:7071/api/counter

# Tester avec action
curl -X POST http://localhost:7071/api/counter \
  -H "Content-Type: application/json" \
  -d '{"action": "increment"}'
```

## Coûts estimés

### Ressources principales
- **Function App (Y1)** : ~0€ (1M exécutions gratuites/mois)
- **Storage Account Function** : ~0.02€/GB/mois
- **Storage Account Static Website** : ~0.02€/GB/mois + 0.0004€ par 10k requêtes
- **Cosmos DB** : ~24€/mois (400 RU/s)
- **Application Insights** : Gratuit jusqu'à 5GB/mois
- **Log Analytics** : ~2.30€/GB après 5GB gratuits
- **Transfert de données** : Premier 5GB gratuit par mois

### Optimisations possibles
- Réduire les RU/s Cosmos DB si le trafic est faible
- Utiliser l'auto-scaling pour Cosmos DB
- Configurer un CDN pour le site web statique (amélioration des performances)
- Monitoring des coûts via Azure Cost Management
- Utiliser des lifecycle policies pour les logs anciens

### Architecture complète

```mermaid
graph TB
    subgraph "Azure Resource Group"
        subgraph "Frontend"
            SW[Storage Account Static Website]
            SW --> HTML[index.html]
            SW --> CSS[style.css] 
            SW --> JS[script.js]
        end
        
        subgraph "Backend"
            FA[Function App Python 3.11]
            SA[Storage Account Functions]
            FA --> SA
        end
        
        subgraph "Database"
            CDB[Cosmos DB Account]
            CDB --> DB[Database: counterdb]
            DB --> CONT[Container: counters]
        end
        
        subgraph "Monitoring"
            LAW[Log Analytics Workspace]
            AI[Application Insights]
            AI --> LAW
        end
        
        subgraph "Identity & Access"
            MI[Managed Identity]
            RBAC[Custom RBAC Role]
            MI --> RBAC
            RBAC --> CDB
        end
    end
    
    subgraph "External"
        USER[User Browser]
        GH[GitHub Actions]
    end
    
    USER --> SW
    JS --> FA
    FA --> CONT
    GH --> FA
    FA --> AI
```
