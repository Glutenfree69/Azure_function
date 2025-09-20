// URL générée automatiquement par Terraform
const API_BASE_URL = '${function_app_url}/api';

async function loadCounter() {
    try {
        console.log('Chargement du compteur depuis:', API_BASE_URL);
        const response = await fetch(`$${API_BASE_URL}/counter`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: $${response.status}`);
        }

        const data = await response.json();

        document.getElementById('counter-value').textContent = data.value;
        document.getElementById('last-updated').textContent = new Date(data.last_updated).toLocaleString('fr-FR');
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
        document.getElementById('counter-value').textContent = 'Erreur';
        document.getElementById('last-updated').textContent = 'Connexion impossible';
    }
}

async function updateCounter(action) {
    try {
        console.log('Mise à jour du compteur:', action);

        // Désactiver les boutons pendant la requête
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = true);

        const response = await fetch(`$${API_BASE_URL}/counter`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action: action })
        });

        if (response.ok) {
            await loadCounter(); // Recharger les données
        } else {
            const errorText = await response.text();
            console.error('Erreur API:', errorText);
            alert('Erreur lors de la mise à jour: ' + response.status);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur de connexion: ' + error.message);
    } finally {
        // Réactiver les boutons
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = false);
    }
}

// Charger le compteur au démarrage
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page chargée, initialisation...');
    loadCounter();
});

// Ajouter un indicateur de connexion
window.addEventListener('online', function() {
    console.log('Connexion rétablie');
    loadCounter();
});

window.addEventListener('offline', function() {
    console.log('Connexion perdue');
    document.getElementById('counter-value').textContent = 'Hors ligne';
});