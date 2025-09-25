// URL générée automatiquement par Terraform
const API_BASE_URL = '${function_app_url}/api';

// Vérification du statut d'authentification
async function checkAuthStatus() {
    try {
        console.log('Vérification du statut d\'authentification...');
        const response = await fetch('/.auth/me');
        const authInfo = await response.json();
        
        if (authInfo.clientPrincipal) {
            const userName = authInfo.clientPrincipal.userDetails;
            
            document.getElementById('user-info').innerHTML = `
                <div class="user-connected">
                    <span>Connecté en tant que: <strong>$${userName}</strong></span>
                    <button onclick="logout()" class="logout-btn">Se déconnecter</button>
                </div>
            `;
            
            document.getElementById('app-content').style.display = 'block';
            return true;
        } else {
            showLoginScreen();
            return false;
        }
    } catch (error) {
        console.error('Erreur auth:', error);
        showLoginScreen();
        return false;
    }
}

function showLoginScreen() {
    document.getElementById('user-info').innerHTML = `
        <div class="login-screen">
            <h2>Authentification requise</h2>
            <p>Connectez-vous avec votre compte Entra ID</p>
            <button onclick="login()" class="login-btn">Se connecter</button>
        </div>
    `;
    document.getElementById('app-content').style.display = 'none';
}

function login() {
    window.location.href = '/.auth/login/aad';
}

function logout() {
    window.location.href = '/.auth/logout';
}

async function loadCounter() {
    try {
        document.getElementById('counter-value').textContent = 'Chargement...';
        
        const response = await fetch(`$${API_BASE_URL}/counter`, {
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/.auth/login/aad';
                return;
            }
            throw new Error(`HTTP error! status: $${response.status}`);
        }

        const data = await response.json();
        document.getElementById('counter-value').textContent = data.value;
        document.getElementById('last-updated').textContent = new Date(data.last_updated).toLocaleString('fr-FR');
        
        if (data.last_user) {
            document.getElementById('last-user').textContent = data.last_user;
            document.getElementById('last-user-info').style.display = 'block';
        }
        
        if (data.current_user) {
            document.getElementById('current-user').textContent = data.current_user;
        }

    } catch (error) {
        console.error('Erreur:', error);
        document.getElementById('counter-value').textContent = 'Erreur';
        document.getElementById('last-updated').textContent = 'Connexion impossible';
    }
}

async function updateCounter(action) {
    try {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = true);

        const response = await fetch(`$${API_BASE_URL}/counter`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action }),
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/.auth/login/aad';
                return;
            }
            throw new Error(`HTTP error! status: $${response.status}`);
        }

        await loadCounter();
    } catch (error) {
        console.error('Erreur:', error);
    } finally {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = false);
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    const isAuthenticated = await checkAuthStatus();
    if (isAuthenticated) {
        await loadCounter();
    }
});

window.addEventListener('online', () => loadCounter());
window.addEventListener('offline', () => {
    document.getElementById('counter-value').textContent = 'Hors ligne';
});