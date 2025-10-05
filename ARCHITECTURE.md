# Architecture - Azure Functions avec MSAL.js

Documentation visuelle complète de l'architecture du projet.

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture par composants](#architecture-par-composants)
- [Flux d'authentification OAuth 2.0](#flux-dauthentification-oauth-20)
- [Flux de requête API](#flux-de-requête-api)
- [Flux de déploiement](#flux-de-déploiement)
- [Infrastructure Terraform](#infrastructure-terraform)

## Vue d'ensemble

Architecture complète de l'application avec tous les composants Azure et flux de données.

```mermaid
graph TB
    subgraph "Client"
        USER[👤 Utilisateur]
        BROWSER[🌐 Navigateur Web]
        USER --> BROWSER
    end
    
    subgraph "Microsoft Entra ID"
        ENTRA[🔐 Azure AD Tenant]
        LOGIN[login.microsoftonline.com]
        JWKS[JWKS Keys Endpoint]
        ENTRA --> LOGIN
        ENTRA --> JWKS
    end
    
    subgraph "Azure Resource Group: rg-vladimirpoutine69"
        subgraph "Frontend Layer"
            STORAGE[💾 Storage Account Static Website]
            HTML[📄 index.html<br/>MSAL.js + Tailwind CSS]
            STORAGE --> HTML
        end
        
        subgraph "Backend Layer"
            FA[⚡ Function App<br/>Python 3.11<br/>Plan Consumption Y1]
            ROUTE_OPTIONS[OPTIONS /api/counter<br/>CORS Preflight]
            ROUTE_API[GET/POST /api/counter<br/>require_auth]
            JWT_VALIDATOR[🔒 JWT Validator<br/>PyJWT + RSA]
            
            FA --> ROUTE_OPTIONS
            FA --> ROUTE_API
            ROUTE_API --> JWT_VALIDATOR
        end
        
        subgraph "Data Layer"
            COSMOS[🗄️ Cosmos DB<br/>SQL API]
            DATABASE[Database: counterdb]
            CONTAINER[Container: counters<br/>Partition: /id]
            
            COSMOS --> DATABASE
            DATABASE --> CONTAINER
        end
        
        subgraph "Observability"
            INSIGHTS[📊 Application Insights]
            ANALYTICS[Log Analytics Workspace]
            INSIGHTS --> ANALYTICS
        end
        
        subgraph "Security"
            MANAGED_ID[🔑 Managed Identity<br/>System Assigned]
            CUSTOM_ROLE[Custom RBAC Role<br/>counter-admin]
            
            MANAGED_ID --> CUSTOM_ROLE
            CUSTOM_ROLE -.->|Permissions| COSMOS
        end
    end
    
    subgraph "CI/CD Pipeline"
        GITHUB[🐙 GitHub Repository]
        ACTIONS[⚙️ GitHub Actions<br/>Python 3.11 + Azure CLI]
        TERRAFORM[🏗️ Terraform<br/>azurerm provider]
        
        GITHUB --> ACTIONS
        GITHUB --> TERRAFORM
    end
    
    %% Flux utilisateur
    BROWSER -->|1. Visite| HTML
    HTML -->|2. Auth OAuth 2.0| LOGIN
    LOGIN -->|3. Token JWT| HTML
    HTML -->|4. API Call<br/>Bearer token| ROUTE_API
    
    %% Validation
    JWT_VALIDATOR -.->|Vérifie signature| JWKS
    ROUTE_API -->|5. Query| CONTAINER
    CONTAINER -->|6. Data| ROUTE_API
    ROUTE_API -->|7. JSON| HTML
    
    %% Monitoring
    FA --> INSIGHTS
    
    %% CI/CD
    ACTIONS -->|Deploy code| FA
    TERRAFORM -->|Provision| STORAGE
    TERRAFORM -->|Provision| FA
    TERRAFORM -->|Provision| COSMOS
    
    %% Managed Identity
    FA -.->|Uses| MANAGED_ID
```

## Architecture par composants

### Frontend : Single Page Application

```mermaid
graph LR
    subgraph "Storage Account Static Website"
        INDEX[index.html<br/>10KB]
        MSAL_LIB[MSAL.js v2<br/>CDN]
        TAILWIND[Tailwind CSS<br/>CDN]
        
        INDEX --> MSAL_LIB
        INDEX --> TAILWIND
    end
    
    subgraph "MSAL.js Configuration"
        CONFIG[msalConfig<br/>clientId + authority]
        CACHE[localStorage<br/>tokens cache]
        
        MSAL_LIB --> CONFIG
        MSAL_LIB --> CACHE
    end
    
    subgraph "API Client"
        GET_TOKEN[getAccessToken]
        FETCH_API[fetch API<br/>Authorization: Bearer]
        
        CACHE --> GET_TOKEN
        GET_TOKEN --> FETCH_API
    end
    
    USER[👤 User] --> INDEX
    FETCH_API -->|HTTPS| FUNCTION_APP[Function App]
```

### Backend : Azure Functions

```mermaid
graph TB
    subgraph "Function App: vladimirpoutine69"
    
        HOST[host.json<br/>Python 3.11]
        
        subgraph "Routes"
            PREFLIGHT[counter_preflight<br/>OPTIONS]
            COUNTER[counter<br/>GET + POST]
        end
        
        subgraph "Middleware"
            DECORATOR[require_auth decorator<br/>JWT validation]
        end
        
        subgraph "Business Logic"
            GET_HANDLER[handle_get_request]
            POST_HANDLER[handle_post_request]
            COSMOS_CLIENT[CosmosClient<br/>DefaultAzureCredential]
        end
        
        HOST --> PREFLIGHT
        HOST --> COUNTER
        COUNTER --> DECORATOR
        DECORATOR --> GET_HANDLER
        DECORATOR --> POST_HANDLER
        GET_HANDLER --> COSMOS_CLIENT
        POST_HANDLER --> COSMOS_CLIENT
    end
    
    REQUEST[HTTP Request] --> HOST
    COSMOS_CLIENT --> COSMOS[(Cosmos DB)]
```

### Database : Cosmos DB

```mermaid
graph TB
    subgraph "Cosmos DB Account: vladimirpoutine69"
        ACCOUNT[Account<br/>GlobalDocumentDB<br/>SQL API]
        
        subgraph "Database: counterdb"
            DB[counterdb<br/>400 RU/s]
            
            subgraph "Container: counters"
                CONTAINER[counters<br/>Partition: /id<br/>400 RU/s]
                
                DOC1[Document<br/>id: main-counter<br/>value: 42]
            end
        end
        
        ACCOUNT --> DB
        DB --> CONTAINER
        CONTAINER --> DOC1
    end
    
    subgraph "Access Control"
        ROLE_DEF[Custom Role Definition<br/>counter-admin]
        ROLE_ASSIGN[Role Assignment<br/>to Function App Identity]
        
        ROLE_DEF --> ROLE_ASSIGN
    end
    
    ROLE_ASSIGN -.->|Grants permissions| ACCOUNT
    
    FUNCTION[Function App<br/>Managed Identity] -->|Data operations| CONTAINER
```

## Flux d'authentification OAuth 2.0

Séquence complète de l'authentification avec MSAL.js et validation JWT.

```mermaid
sequenceDiagram
    participant U as 👤 Utilisateur
    participant B as 🌐 Navigateur
    participant M as MSAL.js
    participant E as 🔐 Entra ID
    participant F as ⚡ Function App
    participant J as JWT Validator
    participant K as JWKS Endpoint
    participant C as 🗄️ Cosmos DB

    Note over U,C: Phase 1: Authentification initiale
    
    U->>B: Visite https://static...
    B->>M: Initialise MSAL
    M->>M: Vérifie localStorage
    
    alt Token en cache et valide
        M->>B: Retourne token existant
    else Pas de token ou expiré
        B->>U: Affiche écran de login
        U->>B: Clique "Se connecter"
        M->>E: Redirect /authorize
        E->>U: Formulaire de connexion
        U->>E: Email + Password
        E->>E: Valide credentials
        E->>M: Redirect avec code
        M->>E: POST /token<br/>code vers tokens
        E->>M: access_token + id_token
        M->>M: Store dans localStorage
    end

    Note over U,C: Phase 2: Appel API protégé
    
    B->>M: getAccessToken()
    M->>B: access_token (JWT)
    B->>F: GET /api/counter<br/>Authorization: Bearer token
    
    Note over F,K: Phase 3: Validation JWT
    
    F->>F: Extrait token du header
    F->>J: validate_token(token)
    J->>J: jwt.get_unverified_header()<br/>extrait kid
    J->>K: GET /discovery/v2.0/keys
    K->>J: JWKS (clés publiques)
    J->>J: Trouve clé avec kid matching
    J->>J: Vérifie signature RSA
    J->>J: Vérifie expiration (exp)
    J->>J: Vérifie audience (aud)
    J->>J: Vérifie issuer (iss)
    
    alt ✅ Token valide
        J->>F: Claims {name, email, ...}
        F->>C: Query avec Managed Identity
        C->>F: Data
        F->>B: 200 OK + JSON
        B->>U: Affiche compteur
    else ❌ Token invalide
        J->>F: ValueError
        F->>B: 401 Unauthorized
        B->>U: Erreur / Redirect login
    end

    Note over U,C: Phase 4: Rafraîchissement (30s)
    
    loop Toutes les 30 secondes
        B->>M: acquireTokenSilent()
        alt Token valide
            M->>B: Token existant
        else Token expiré
            M->>E: Refresh token
            E->>M: Nouveau access_token
        end
        B->>F: Rafraîchit les données
    end
```

## Flux de requête API

Détail d'un appel API complet avec validation JWT.

```mermaid
sequenceDiagram
    participant C as 🌐 Client SPA
    participant FA as ⚡ Function App
    participant D as require_auth
    participant V as validate_token()
    participant K as JWKS
    participant H as Handler
    participant DB as 🗄️ Cosmos DB

    C->>FA: POST /api/counter<br/>Authorization: Bearer eyJ...
    
    FA->>D: Appel décorateur
    D->>D: Extrait header<br/>Authorization
    
    alt Header manquant ou invalide
        D->>C: 401 Unauthorized<br/>{"error": "Auth requise"}
    else Header valide
        D->>D: token = header.replace('Bearer ', '')
        D->>V: validate_token(token)
        
        V->>V: Decode header extrait kid
        V->>K: GET /keys
        K->>V: Public keys
        V->>V: Find key by kid
        V->>V: jwt.decode(...)<br/>verify all claims
        
        alt Signature/Claims invalides
            V-->>D: ValueError
            D->>C: 401 Unauthorized<br/>{"error": "Token invalide"}
        else Token valide
            V->>D: claims dict
            D->>D: req.claims = claims
            D->>H: handler(req)
            
            H->>H: Extract user info<br/>from req.claims
            H->>DB: Query/Update<br/>via Managed Identity
            DB->>H: Result
            H->>D: HttpResponse(200)
            D->>FA: Response
            FA->>C: 200 OK + JSON<br/>Access-Control-Allow-Origin
        end
    end
```

## Flux de déploiement

Pipeline CI/CD avec GitHub Actions et Terraform.

```mermaid
graph TB
    subgraph "Developer"
        DEV[👨‍💻 Developer]
        CODE[📝 Code Changes]
        DEV --> CODE
    end
    
    subgraph "GitHub Repository"
        REPO[📦 Repository]
        MAIN[main branch]
        
        CODE --> REPO
        REPO --> MAIN
    end
    
    subgraph "GitHub Actions Pipeline"
        TRIGGER[⚙️ Workflow Trigger<br/>on: push main]
        
        subgraph "Build Stage"
            CHECKOUT[Checkout code]
            SETUP_PY[Setup Python 3.11]
            INSTALL[pip install<br/>PyJWT, requests, etc.]
            ZIP[Create ZIP package]
        end
        
        subgraph "Deploy Stage"
            LOGIN[Azure CLI Login<br/>RBAC credentials]
            DEPLOY[az functionapp<br/>deployment config-zip]
            BUILD_REMOTE[Remote build on Azure]
        end
        
        TRIGGER --> CHECKOUT
        CHECKOUT --> SETUP_PY
        SETUP_PY --> INSTALL
        INSTALL --> ZIP
        ZIP --> LOGIN
        LOGIN --> DEPLOY
        DEPLOY --> BUILD_REMOTE
    end
    
    subgraph "Terraform Workflow"
        TF_CODE[Terraform Files<br/>*.tf]
        
        subgraph "Terraform Apply"
            TF_INIT[terraform init]
            TF_PLAN[terraform plan]
            TF_APPLY[terraform apply]
            
            TF_INIT --> TF_PLAN
            TF_PLAN --> TF_APPLY
        end
        
        CODE --> TF_CODE
        TF_CODE --> TF_INIT
    end
    
    subgraph "Azure Resources"
        RG[Resource Group]
        
        subgraph "Provisioned by Terraform"
            SA_STATIC[Storage Account<br/>Static Website]
            BLOB_HTML[Blob: index.html<br/>with injected values]
        end
        
        subgraph "Updated by GitHub Actions"
            FA_DEPLOYED[Function App<br/>with new code]
        end
        
        TF_APPLY --> SA_STATIC
        TF_APPLY --> BLOB_HTML
        BUILD_REMOTE --> FA_DEPLOYED
    end
    
    MAIN --> TRIGGER
```

## Infrastructure Terraform

Organisation des ressources Terraform et dépendances.

```mermaid
graph TB
    subgraph "Terraform Root"
        TFVARS[terraform.tfvars<br/>tenant_id, client_id]
        VARS[variables.tf]
        
        TFVARS --> VARS
    end
    
    subgraph "Core Infrastructure"
        RG[azurerm_resource_group<br/>rg-vladimirpoutine69]
        
        SA_FUNC[azurerm_storage_account<br/>vladimirpoutine69<br/>Function storage]
        
        SA_STATIC[azurerm_storage_account<br/>staticvladimirpoutine69<br/>Static website]
        
        RG --> SA_FUNC
        RG --> SA_STATIC
    end
    
    subgraph "Compute"
        ASP[azurerm_service_plan<br/>Y1 Consumption]
        
        FA[azurerm_linux_function_app<br/>vladimirpoutine69<br/>Python 3.11]
        
        RG --> ASP
        ASP --> FA
        SA_FUNC --> FA
    end
    
    subgraph "Database"
        COSMOS_ACC[azurerm_cosmosdb_account<br/>vladimirpoutine69]
        
        COSMOS_DB[azurerm_cosmosdb_sql_database<br/>counterdb]
        
        COSMOS_CONT[azurerm_cosmosdb_sql_container<br/>counters]
        
        RG --> COSMOS_ACC
        COSMOS_ACC --> COSMOS_DB
        COSMOS_DB --> COSMOS_CONT
    end
    
    subgraph "Security & RBAC"
        ROLE_DEF[azurerm_cosmosdb_sql_role_definition<br/>counter-admin]
        
        ROLE_ASSIGN[azurerm_cosmosdb_sql_role_assignment<br/>FA identity to role]
        
        COSMOS_ACC --> ROLE_DEF
        ROLE_DEF --> ROLE_ASSIGN
        FA -.->|identity| ROLE_ASSIGN
    end
    
    subgraph "Monitoring"
        LAW[azurerm_log_analytics_workspace]
        AI[azurerm_application_insights]
        
        RG --> LAW
        LAW --> AI
        AI --> FA
    end
    
    subgraph "Static Website Deployment"
        BLOB_HTML[azurerm_storage_blob<br/>index.html<br/>with template injection]
        
        SA_STATIC --> BLOB_HTML
        VARS -.->|inject values| BLOB_HTML
    end
```

## Résumé des flux

### 1. Authentification utilisateur
1. Utilisateur visite le site
2. MSAL.js détecte pas de token
3. Redirect vers Entra ID
4. Login → Authorization code
5. MSAL échange code → tokens
6. Tokens stockés dans localStorage

### 2. Appel API sécurisé
1. Frontend demande token à MSAL
2. MSAL retourne token (cache ou refresh)
3. Frontend appelle API avec `Authorization: Bearer <token>`
4. Backend extrait et valide JWT
5. Backend récupère données Cosmos DB
6. Backend retourne JSON

### 3. Validation JWT
1. Extraire kid du header JWT
2. Récupérer clés publiques Microsoft
3. Trouver clé matching le kid
4. Vérifier signature RSA
5. Vérifier claims (exp, aud, iss)
6. Retourner claims ou erreur

### 4. Déploiement
1. Push code vers GitHub
2. GitHub Actions déclenché
3. Build + ZIP du code Python
4. Deploy vers Function App
5. Remote build sur Azure
6. Terraform gère l'infrastructure

---

**Légende des icônes** : 👤 Utilisateur | 🌐 Web | 🔐 Auth | ⚡ Serverless | 🗄️ Database | 📊 Monitoring | 🐙 Git | ⚙️ CI/CD | 🏗️ IaC