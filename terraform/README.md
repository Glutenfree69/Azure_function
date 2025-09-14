# Infrastructure Azure Function - Terraform

Infrastructure as Code pour déployer une Azure Function avec monitoring et sécurité sur Microsoft Azure.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Resource      │    │   Function App   │    │   Storage       │
│   Group         │───▶│   (Python)       │───▶│   Account       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                          │
                               ▼                          │
                       ┌──────────────────┐               │
                       │  App Service     │               │
                       │  Plan (FC1)       │               │
                       └──────────────────┘               │
                               │                          │
                               ▼                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Application     │    │  Managed        │
                       │  Insights        │    │  Identity       │
                       └──────────────────┘    └─────────────────┘
```

## Structure du projet

```
terraform/
├── providers.tf              # Configuration du provider AzureRM
├── terraform.tf              # Backend et versions Terraform
├── resource_group.tf         # Groupe de ressources principal
├── storage_account.tf        # Stockage pour la Function App
├── service_plan.tf           # Plan d'hébergement FC1
├── managed_identity.tf       # Identité pour l'authentification
├── application_insights.tf   # Monitoring et observabilité
├── linux_function_app.tf     # Function App Python
└── terraform.lock.hcl        # Verrouillage des versions
```

## Ressources déployées

### Resource Group
**Fichier** : `resource_group.tf`
```hcl
azurerm_resource_group.glutenfree69
```
- Nom : `glutenfree69`
- Région : France Central
- Conteneur logique pour toutes les ressources

### Storage Account
**Fichier** : `storage_account.tf`
```hcl
azurerm_storage_account.glutenfree69
```
- Type : Storage (legacy)
- Réplication : LRS
- Authentification : OAuth activé
- Usage : Stockage des fichiers de fonction et données applicatives

### App Service Plan
**Fichier** : `service_plan.tf`
```hcl
azurerm_service_plan.glutenfree69
```
- SKU : FC1 (Basic, ~13€/mois)
- OS : Linux
- Usage : Hébergement de la Function App

### Managed Identity
**Fichier** : `managed_identity.tf`
```hcl
azurerm_user_assigned_identity.glutenfree69
```
- Type : User Assigned
- Usage : Authentification sécurisée entre Function App et Storage Account
- Avantage : Pas de clés à gérer

### Application Insights
**Fichier** : `application_insights.tf`
```hcl
azurerm_application_insights.glutenfree69
```
- Type : Web application
- Sampling : 0% (capture tout)
- Usage : Logs, métriques, monitoring des performances

### Linux Function App
**Fichier** : `linux_function_app.tf`
```hcl
azurerm_linux_function_app.glutenfree69
```
- Runtime : Python
- Version Functions : ~4
- Authentification : Certificats clients requis
- Logging : Intégré avec Application Insights

## Configuration des connexions

### Authentification Storage
```hcl
app_settings = {
  "AzureWebJobsStorage__credential" = "managedidentity"
  "AzureWebJobsStorage__clientId" = "<managed-identity-id>"
  # URLs des services de stockage...
}
```

### Monitoring
- Connection string Application Insights dans `site_config`
- Tag de liaison automatique vers Application Insights
- Collecte automatique des métriques et logs

## Utilisation

### Déploiement initial
```bash
# Initialisation
terraform init

# Vérification
terraform plan

# Déploiement
terraform apply
```

## Sécurité

### Managed Identity
- Authentification sans clés stockées
- Rotation automatique des tokens
- Principe du moindre privilège

### Storage Account
- Authentification OAuth par défaut
- TLS 1.0 minimum (legacy)
- Accès par clés contrôlé

### Function App
- HTTPS uniquement
- Certificats clients requis
- Restrictions IP configurables

## Monitoring

### Application Insights collecte
- Requêtes HTTP entrantes
- Durées d'exécution des fonctions
- Exceptions et erreurs
- Dépendances externes (Storage, APIs)
- Logs personnalisés de l'application

### Métriques disponibles
- Temps de réponse
- Throughput (requêtes/seconde)
- Taux d'erreur
- Utilisation CPU/mémoire
