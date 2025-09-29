// URL générée automatiquement par Terraform
const API_BASE_URL = '${function_app_url}/api';

console.log('🚀 Application initialisée');
console.log('📍 API URL:', API_BASE_URL);

// Vérification du statut d'authentification
async function checkAuthStatus() {
    try {
        console.log('🔐 Vérification du statut d\'authentification...');
        
        // Appel à /.auth/me pour récupérer les infos utilisateur
        const response = await fetch('/.auth/me', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.warn('⚠️ Impossible de récupérer le statut auth');
            showLoginScreen();
            return false;
        }
        
        const authInfo = await response.json();
        console.log('📋 Auth info:', authInfo);
        
        if (authInfo.clientPrincipal) {
            const userName = authInfo.clientPrincipal.userDetails;
            const userId = authInfo.clientPrincipal.userId;
            
            console.log('✅ Utilisateur authentifié:', userName);
            
            document.getElementById('user-info').innerHTML = `
                <div class="user-connected">
                    <span>Connecté en tant que: <strong>$${userName}</strong></span>
                    <button onclick="logout()" class="logout-btn">Se déconnecter</button>
                </div>
            `;
            
            document.getElementById('app-content').style.display = 'block';
            return true;
        } else {
            console.log('❌ Non authentifié');
            showLoginScreen();
            return false;
        }
    } catch (error) {
        console.error('❌ Erreur lors de la vérification auth:', error);
        showLoginScreen();
        return false;
    }
}

function showLoginScreen() {
    document.getElementById('user-info').innerHTML = `
        <div class="login-screen">
            <h2>🔐 Authentification requise</h2>
            <p>Connectez-vous avec votre compte Entra ID pour accéder au compteur</p>
            <button onclick="login()" class="login-btn">Se connecter avec Entra ID</button>
        </div>
    `;
    document.getElementById('app-content').style.display = 'none';
}

function login() {
    console.log('🔑 Redirection vers login Entra ID...');
    const returnUrl = encodeURIComponent(window.location.href);
    window.location.href = `/.auth/login/aad?post_login_redirect_url=$${returnUrl}`;
}

function logout() {
    console.log('👋 Déconnexion...');
    if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
        window.location.href = '/.auth/logout';
    }
}

async function loadCounter() {
    try {
        console.log('📥 Chargement du compteur...');
        document.getElementById('counter-value').textContent = 'Chargement...';
        
        const response = await fetch(`$${API_BASE_URL}/counter`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });

        console.log('📡 Réponse API:', response.status, response.statusText);

        if (!response.ok) {
            if (response.status === 401) {
                console.warn('⚠️ Session expirée ou non authentifié');
                alert('Votre session a expiré. Redirection vers la page de connexion...');
                window.location.href = '/.auth/login/aad';
                return;
            }
            throw new Error(`Erreur HTTP $${response.status}: $${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ Données reçues:', data);
        
        document.getElementById('counter-value').textContent = data.value;
        
        if (data.last_updated) {
            const lastUpdate = new Date(data.last_updated);
            document.getElementById('last-updated').textContent = lastUpdate.toLocaleString('fr-FR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
        
        if (data.last_user) {
            document.getElementById('last-user').textContent = data.last_user;
            const lastUserInfo = document.getElementById('last-user-info');
            if (lastUserInfo) {
                lastUserInfo.style.display = 'block';
            }
        }
        
        if (data.current_user) {
            const currentUserEl = document.getElementById('current-user');
            if (currentUserEl) {
                currentUserEl.textContent = data.current_user;
            }
        }

        console.log('✅ Compteur chargé avec succès:', data.value);

    } catch (error) {
        console.error('❌ Erreur lors du chargement du compteur:', error);
        document.getElementById('counter-value').textContent = 'Erreur';
        document.getElementById('last-updated').textContent = 'Connexion impossible';
        alert(`Erreur lors du chargement du compteur: $${error.message}`);
    }
}

async function updateCounter(action) {
    try {
        console.log(`🔄 Action "$${action}" en cours...`);
        
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = true);

        const response = await fetch(`$${API_BASE_URL}/counter`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ action: action }),
            credentials: 'include'
        });

        console.log('📡 Réponse API:', response.status, response.statusText);

        if (!response.ok) {
            if (response.status === 401) {
                console.warn('⚠️ Session expirée ou non authentifié');
                alert('Votre session a expiré. Redirection vers la page de connexion...');
                window.location.href = '/.auth/login/aad';
                return;
            }
            
            let errorMessage = `Erreur HTTP $${response.status}`;
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                }
            } catch (e) {
                // Impossible de parser l'erreur JSON
            }
            
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('✅ Action réussie:', data);

        const actionMessages = {
            'increment': '➕ Compteur incrémenté',
            'decrement': '➖ Compteur décrémenté',
            'reset': '🔄 Compteur réinitialisé'
        };
        
        const message = actionMessages[action] || '✅ Action effectuée';
        showToast(message, 'success');

        await loadCounter();

    } catch (error) {
        console.error('❌ Erreur lors de l\'action:', error);
        showToast(`❌ Erreur: $${error.message}`, 'error');
    } finally {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => btn.disabled = false);
    }
}

function showToast(message, type = 'info') {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            transition: opacity 0.3s ease;
            max-width: 300px;
        `;
        document.body.appendChild(toast);
    }
    
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };
    
    toast.style.backgroundColor = colors[type] || colors.info;
    toast.textContent = message;
    toast.style.opacity = '1';
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', async function() {
    console.log('📱 Page chargée, initialisation...');
    
    const isAuthenticated = await checkAuthStatus();
    
    if (isAuthenticated) {
        await loadCounter();
        
        setInterval(() => {
            if (navigator.onLine) {
                console.log('🔄 Rafraîchissement automatique du compteur...');
                loadCounter();
            }
        }, 30000);
    }
});

window.addEventListener('online', () => {
    console.log('🌐 Connexion rétablie');
    showToast('Connexion rétablie', 'success');
    loadCounter();
});

window.addEventListener('offline', () => {
    console.log('📡 Connexion perdue');
    document.getElementById('counter-value').textContent = 'Hors ligne';
    showToast('Connexion perdue', 'warning');
});

document.addEventListener('visibilitychange', () => {
    if (!document.hidden && navigator.onLine) {
        console.log('👁️ Page redevenue visible, rafraîchissement...');
        checkAuthState().then(isAuth => {
            if (isAuth) {
                loadCounter();
            }
        });
    }
});

console.log('✅ Script.js chargé avec succès');