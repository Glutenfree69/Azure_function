#!/bin/bash

# Variables
RESOURCE_GROUP="rg-vladimirpoutine69"
FUNCTION_APP_NAME="vladimirpoutine69"

echo "=== REMOTE BUILD DEPLOYMENT ==="

# 1. Créer le ZIP (source code uniquement, pas de dépendances)
echo "Creating ZIP package..."
zip -r function-app.zip \
  function_app.py \
  host.json \
  requirements.txt \
  .funcignore

# 2. Vérifier le contenu
echo -e "\nZIP contents:"
unzip -l function-app.zip

# 3. Déployer avec build distant
echo -e "\nDeploying to Azure..."
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --src function-app.zip \
  --build-remote true \
  --timeout 600

echo -e "\n✅ Deployment complete!"

# 4. Attendre la propagation
echo "Waiting for deployment to propagate..."
sleep 30

# 5. Vérifier les fonctions déployées
echo -e "\nChecking deployed functions:"
az functionapp function list \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table

# 6. Tester l'endpoint
FUNCTION_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/api/counter"
echo -e "\nTesting endpoint: $FUNCTION_URL"
curl -X OPTIONS $FUNCTION_URL -v

# Nettoyage
rm function-app.zip