# 🧮 Compteur Azure Functions avec Table Storage

Un compteur web persistant construit avec Azure Functions (Python) et Azure Table Storage. Ce projet démontre l'utilisation des services cloud Azure pour créer une application web simple mais complète.

https://learn.microsoft.com/en-us/azure/azure-functions/how-to-create-function-vs-code?pivots=programming-language-python

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Configuration locale](#-configuration-locale)
- [Développement local](#-développement-local)
- [Déploiement Azure](#-déploiement-azure)
- [Configuration Azure](#-configuration-azure)
- [Structure du projet](#-structure-du-projet)
- [Dépannage](#-dépannage)
- [Bonnes pratiques](#-bonnes-pratiques)

## 🎯 Vue d'ensemble

Cette application est un compteur web qui :
- ✅ Affiche une interface web simple avec un compteur
- ✅ Permet d'incrémenter le compteur via un bouton
- ✅ Stocke les données de manière persistante dans Azure Table Storage
- ✅ Fonctionne en local avec Azurite (émulateur) et en production avec Azure
- ✅ Utilise une architecture serverless (Azure Functions)

## 🏗️ Architecture

```
┌─────────────────┐    HTTP    ┌──────────────────┐    Stockage    ┌─────────────────┐
│                 │ ────────▶  │                  │ ─────────────▶ │                 │
│   Navigateur    │            │  Azure Function  │                │  Table Storage  │
│   Web           │ ◀────────  │     (Python)     │ ◀───────────── │                 │
└─────────────────┘    HTML    └──────────────────┘    Données     └─────────────────┘
```

### Composants :

- **🌐 Frontend :** HTML/CSS/JavaScript intégré dans la réponse HTTP
- **⚡ Backend :** Azure Functions (Python 3.12+)
- **🗄️ Base de données :** Azure Table Storage (NoSQL)
- **🔧 Développement local :** Azurite (émulateur Azure Storage)

### Flux de données :

1. **GET** `/api/counter` → Affiche l'interface web avec le compteur actuel
2. **POST** `/api/counter` → Incrémente le compteur et retourne la nouvelle valeur
3. **Storage** → Les données sont stockées dans la table `counterdata`

## 📦 Prérequis

### Outils requis :

- **Python 3.12+** ([télécharger](https://python.org))
- **Node.js** ([télécharger](https://nodejs.org)) pour Azurite
- **Azure Functions Core Tools** ([installation](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local))
- **uv** (gestionnaire de packages Python) ([installation](https://docs.astral.sh/uv/))
- **VS Code** avec l'extension Azure Functions (recommandé)

### Installation sur macOS :

```bash
# Homebrew
brew install python node azure-functions-core-tools

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Azurite (émulateur Azure Storage)
npm install -g azurite
```

### Compte Azure :

- Compte Azure actif ([inscription gratuite](https://azure.microsoft.com/free/))
- Azure CLI installé et configuré

## 🖥️ Configuration locale

### 1. Cloner et configurer le projet

```bash
# Créer l'environnement virtuel
uv venv
source .venv/bin/activate  # macOS/Linux

# Installer les dépendances
uv pip install azure-functions azure-data-tables
uv pip freeze > requirements.txt
```

### 2. Structure des fichiers

```
azure_function/
├── .venv/                     # Environnement virtuel Python
├── .azurite/                  # Données Azurite (ignoré par git)
├── .vscode/
│   └── tasks.json            # Configuration VS Code
├── function_app.py           # Code principal de la fonction
├── requirements.txt          # Dépendances Python
├── host.json                 # Configuration Azure Functions
├── local.settings.json       # Configuration locale
├── .funcignore              # Exclusions pour le déploiement
└── .gitignore               # Exclusions Git
```

### 3. Configuration locale (`local.settings.json`)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

### 4. Configuration VS Code (`.vscode/tasks.json`)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "azurite: start",
      "type": "shell",
      "command": "azurite",
      "args": ["--silent", "--location", "${workspaceFolder}/.azurite"],
      "isBackground": true,
      "problemMatcher": []
    },
    {
      "type": "func",
      "label": "func: host start",
      "command": "host start",
      "problemMatcher": "$func-python-watch",
      "isBackground": true,
      "dependsOn": ["azurite: start", "pip install (functions)"]
    },
    {
      "label": "pip install (functions)",
      "type": "shell",
      "command": "uv pip install -r requirements.txt",
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {"VIRTUAL_ENV": "${workspaceFolder}/.venv"}
      }
    }
  ]
}
```

## 🚀 Développement local

### Démarrage automatique (VS Code)

1. **F5** ou "Start Debugging" → Lance automatiquement Azurite (la fonction faut la démarrer a la main avec func start --verbose, TODO: modifier la config)
2. Accéder à `http://localhost:7071/api/counter`

### Démarrage manuel

```bash
# Terminal 1 : Démarrer Azurite
azurite --silent --location .azurite

# Terminal 2 : Démarrer la fonction
source .venv/bin/activate
func start --verbose
```

### Vérification du fonctionnement

1. **Interface web :** `http://localhost:7071/api/counter`
2. **Logs :** Visibles dans le terminal func start
3. **Données :** Tables visibles dans Azure Storage Explorer (connecté à l'émulateur)

## ☁️ Déploiement Azure

### 1. Préparation du déploiement

Assurer que `.funcignore` exclut les fichiers inutiles :

```
.azurite/
__pycache__/
.venv/
local.settings.json
.vscode/
.git/
.DS_Store
```

### 2. Méthodes de déploiement

#### VS Code

1. **F1** → "Azure Functions: Deploy to Function App..."
2. **"Create new Function App in Azure..."**
3. Sélectionner :
   - **Nom :** unique (ex: `massacreur_de_vulves`)
   - **Runtime :** Python 3.12
   - **Région :** West Europe

## ⚙️ Configuration Azure

### Ressources créées automatiquement

- **📦 Function App :** Exécute votre code Python
- **🗄️ Storage Account :** Stocke les données du compteur
- **📊 Application Insights :** Monitoring et logs
- **⚡ App Service Plan :** Ressources de calcul (plan Consumption)

### Configuration du Storage

#### Problème courant : Authentification par clé désactivée

**Erreur :** `KeyBasedAuthenticationNotPermitted`

**Solution :**
1. **Storage Account** → **Settings** → **Configuration**
2. **"Allow storage account key access"** → **Enabled**
3. **Save**

#### Configuration de la connection string

1. **Function App** → **Settings** → **Environment variables**
2. **Ajouter** `AzureWebJobsStorage` si manquant :
   - **Name :** `AzureWebJobsStorage`
   - **Value :** Connection string du Storage Account

**Récupérer la connection string :**
1. **Storage Account** → **Security + networking** → **Access keys**
2. **key1** → **Show** → **Copier "Connection string"**

### Vérification du fonctionnement

#### URLs importantes

- **🌐 Application :** `https://[votre-app].azurewebsites.net/api/counter?code=...`
- **📊 Monitoring :** Portail Azure → Function App → Monitoring
- **🗄️ Données :** Portail Azure → Storage Account → Tables → `counterdata`

#### Surveillance

- **Logs en temps réel :** Function App → Log stream
- **Métriques :** Function App → Metrics
- **Erreurs :** Application Insights → Failures

## 📁 Structure du projet

### Fichiers principaux

#### `function_app.py`

```python
import azure.functions as func
import logging
import json
import os
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configuration
STORAGE_CONNECTION_STRING = os.environ.get('AzureWebJobsStorage')
TABLE_NAME = 'counterdata'

# Fonctions de gestion du storage...
```

#### `requirements.txt`

```
azure-functions
azure-data-tables
```

#### `host.json`

```json
{
  "version": "2.0",
  "functionTimeout": "00:05:00",
  "extensions": {
    "http": {
      "routePrefix": "api"
    }
  }
}
```

### Données stockées

**Table :** `counterdata`
**Structure :**

| PartitionKey | RowKey | count | Timestamp |
|--------------|--------|--------|-----------|
| counter      | main   | 42     | 2025-09-11... |

## 🛠️ Dépannage

### Problèmes courants

#### 1. Erreur 500 lors du clic sur le bouton

**Symptômes :** Page s'affiche, mais le compteur ne s'incrémente pas

**Causes possibles :**
- Configuration Storage manquante
- Permissions insuffisantes
- Authentification par clé désactivée

**Solutions :**
1. Vérifier les logs : Function App → Log stream
2. Vérifier `AzureWebJobsStorage` dans Environment variables
3. Activer l'authentification par clé dans le Storage Account

#### 2. Module 'azure.data.tables' not found

**Cause :** Dépendances non installées lors du déploiement

**Solution :**
```bash
# Vérifier requirements.txt
cat requirements.txt

# Redéployer
func azure functionapp publish [votre-app]
```

#### 3. Azurite ne démarre pas en local

**Symptômes :** `EADDRINUSE` ou ports occupés

**Solutions :**
```bash
# Tuer les processus Azurite
pkill -f azurite

# Changer les ports
azurite --blobPort 10001 --queuePort 10002 --tablePort 10003
```

#### 4. VS Code ne trouve pas la fonction

**Cause :** `.venv` inclus dans le déploiement

**Solution :**
```bash
# Nettoyer
rm -rf __pycache__ .azurite .venv

# Vérifier .funcignore
echo ".venv/" >> .funcignore

# Redéployer
```

### Logs et monitoring

#### Commandes utiles

```bash
# Logs en temps réel
func azure functionapp logstream [votre-app]

# Status de l'app
az functionapp show --name [votre-app] --resource-group [votre-rg]

# Redémarrer l'app
az functionapp restart --name [votre-app] --resource-group [votre-rg]
```

#### Logs détaillés

Dans Azure :
1. **Function App** → **Functions** → **counter_function** → **Monitor**
2. **Application Insights** → **Live Metrics**
3. **Storage Account** → **Monitoring** → **Insights**

## 🎯 Bonnes pratiques

### Sécurité

- ✅ Utiliser Managed Identity au lieu de connection strings
- ✅ Activer HTTPS uniquement
- ✅ Restreindre les Function Keys
- ✅ Surveiller les accès avec Application Insights

### Performance

- ✅ Utiliser le plan Consumption pour les charges légères
- ✅ Optimiser les requêtes Table Storage (PartitionKey/RowKey)
- ✅ Implémenter une logique de retry pour les erreurs transitoires
- ✅ Surveiller les métriques de performance

### Développement

- ✅ Tester localement avec Azurite avant déploiement
- ✅ Utiliser des environnements séparés (dev/staging/prod)
- ✅ Versioning du code avec Git
- ✅ CI/CD avec GitHub Actions ou Azure DevOps

### Coûts

- 📊 **Function App :** 1M exécutions gratuites/mois
- 💾 **Storage :** ~0.01€/mois pour usage typique
- 📈 **Application Insights :** Premiers 5GB gratuits/mois

**Total estimé :** Pratiquement gratuit pour usage personnel

### Évolutions possibles

- 🔐 **Authentification :** Ajouter login utilisateur
- 📱 **Mobile :** Application mobile avec Azure Mobile Apps
- 🌐 **API :** Exposer une API REST complète
- 📊 **Analytics :** Tableau de bord avec Azure Dashboard
- 🔄 **CI/CD :** Déploiement automatique depuis Git

## 📚 Ressources supplémentaires

- [Documentation Azure Functions](https://docs.microsoft.com/azure/azure-functions/)
- [Azure Table Storage SDK](https://docs.microsoft.com/azure/storage/tables/)
- [VS Code Azure Functions Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
- [Azure Free Account](https://azure.microsoft.com/free/)

---

**Auteur :** Nick Guer
**Version :** 1.0
**Dernière mise à jour :** Septembre 2025

💡 **Astuce :** N'hésitez pas à expérimenter et modifier le code pour apprendre ! Azure offre de nombreux services qui peuvent enrichir cette application de base.