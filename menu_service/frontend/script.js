// Configuration
const API_BASE_URL = 'http://localhost:9999';

// Global state
let currentUser = null;

// DOM elements
const sections = document.querySelectorAll('.section');
const navButtons = document.querySelectorAll('.nav-btn');
const menuGrid = document.getElementById('menu-grid');
const dishModal = document.getElementById('dish-modal');
const notification = document.getElementById('notification');
const mainNav = document.getElementById('main-nav');
const userInfo = document.getElementById('user-info');
const userEmail = document.getElementById('user-email');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    initializeNavigation();
    initializeForms();
    checkAuthStatus();
});

// Authentication
function initializeAuth() {
    // Auth tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchAuthTab(targetTab);
            
            // Update active tab
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function switchAuthTab(tabName) {
    document.querySelectorAll('.auth-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function checkAuthStatus() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showAuthenticatedUI();
    } else {
        showAuthUI();
    }
}

function showAuthUI() {
    document.getElementById('auth-section').classList.add('active');
    mainNav.style.display = 'none';
    userInfo.style.display = 'none';
}

function showAuthenticatedUI() {
    document.getElementById('auth-section').classList.remove('active');
    mainNav.style.display = 'flex';
    userInfo.style.display = 'block';
    userEmail.textContent = currentUser.email;
    loadMenu();
}

function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    showAuthUI();
    showNotification('Logout effettuato', 'info');
}

// Navigation
function initializeNavigation() {
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-section');
            showSection(targetSection);
            
            // Update active nav button
            navButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function showSection(sectionName) {
    sections.forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${sectionName}-section`).classList.add('active');
}

// Forms initialization
function initializeForms() {
    // Auth forms
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('confirm-form').addEventListener('submit', handleConfirm);
    
    // Menu forms
    document.getElementById('add-dish-btn').addEventListener('click', showDishModal);
    document.getElementById('dish-form').addEventListener('submit', handleAddDish);
    document.querySelector('.close').addEventListener('click', hideDishModal);
    
    // Order forms
    document.getElementById('new-order-form').addEventListener('submit', handleNewOrder);
    document.getElementById('order-status-form').addEventListener('submit', handleOrderStatus);
    document.getElementById('load-orders-btn').addEventListener('click', handleMyOrders);
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === dishModal) {
            hideDishModal();
        }
    });
}

// Menu functions
async function loadMenu() {
    try {
        showLoading(menuGrid);
        const response = await fetch(`${API_BASE_URL}/menu/get_menu`);
        const menu = await response.json();
        
        if (response.ok) {
            displayMenu(menu);
        } else {
            showNotification('Errore nel caricamento del menu', 'error');
        }
    } catch (error) {
        console.error('Error loading menu:', error);
        showNotification('Errore di connessione', 'error');
    }
}

function displayMenu(menu) {
    menuGrid.innerHTML = '';
    
    if (menu && menu.length > 0) {
        menu.forEach(dish => {
            const dishCard = createDishCard(dish);
            menuGrid.appendChild(dishCard);
        });
    } else {
        menuGrid.innerHTML = '<p style="text-align: center; color: #718096; grid-column: 1/-1;">Nessun piatto disponibile</p>';
    }
}

function createDishCard(dish) {
    const card = document.createElement('div');
    card.className = 'dish-card';
    card.innerHTML = `
        <div class="dish-name">${dish.name}</div>
        <div class="dish-price">€${dish.price.toFixed(2)}</div>
        <div class="dish-description">${dish.description}</div>
        <div style="margin-top: 15px;">
            <button class="btn btn-primary" onclick="orderDish('${dish.id}')" style="width: 100%;">
                Ordina Ora
            </button>
        </div>
        <div style="margin-top: 10px; font-size: 0.9rem; color: #a0aec0;">ID: ${dish.id}</div>
    `;
    return card;
}

async function orderDish(dishId) {
    if (!currentUser) {
        showNotification('Devi essere autenticato per ordinare', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/new_order?dish_id=${encodeURIComponent(dishId)}&user_id=${encodeURIComponent(currentUser.id)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const order = await response.json();
            showNotification(`Ordine creato con successo! ID: ${order.id}`, 'success');
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Errore sconosciuto'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating order:', error);
        showNotification('Errore di connessione', 'error');
    }
}

function showDishModal() {
    dishModal.style.display = 'block';
}

function hideDishModal() {
    dishModal.style.display = 'none';
    document.getElementById('dish-form').reset();
}

async function handleAddDish(event) {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('name', document.getElementById('dish-name').value);
    formData.append('price', document.getElementById('dish-price').value);
    formData.append('description', document.getElementById('dish-description').value);
    
    try {
        const response = await fetch(`${API_BASE_URL}/menu/new_dish`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showNotification('Piatto aggiunto con successo!', 'success');
            hideDishModal();
            loadMenu(); // Reload menu
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Errore sconosciuto'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding dish:', error);
        showNotification('Errore di connessione', 'error');
    }
}

// User functions
async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const region = document.getElementById('register-region').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/register?region=${encodeURIComponent(region)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            showNotification('Utente registrato con successo!', 'success');
            document.getElementById('register-form').reset();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Errore sconosciuto'}`, 'error');
        }
    } catch (error) {
        console.error('Error registering user:', error);
        showNotification('Errore di connessione', 'error');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            // Simulate getting user data (in real app, this would come from login response)
            currentUser = {
                id: 'user-' + Date.now(), // This should come from the API
                email: email
            };
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showNotification('Login effettuato con successo!', 'success');
            document.getElementById('login-form').reset();
            showAuthenticatedUI();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Credenziali non valide'}`, 'error');
        }
    } catch (error) {
        console.error('Error logging in:', error);
        showNotification('Errore di connessione', 'error');
    }
}

async function handleConfirm(event) {
    event.preventDefault();
    
    const email = document.getElementById('confirm-email').value;
    const password = document.getElementById('confirm-password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            showNotification('Utente confermato con successo!', 'success');
            document.getElementById('confirm-form').reset();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Utente non trovato'}`, 'error');
        }
    } catch (error) {
        console.error('Error confirming user:', error);
        showNotification('Errore di connessione', 'error');
    }
}

// Order functions
async function handleNewOrder(event) {
    event.preventDefault();
    
    if (!currentUser) {
        showNotification('Devi essere autenticato per creare ordini', 'error');
        return;
    }
    
    const dishId = document.getElementById('order-dish-id').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/new_order?dish_id=${encodeURIComponent(dishId)}&user_id=${encodeURIComponent(currentUser.id)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const order = await response.json();
            showNotification(`Ordine creato con successo! ID: ${order.id}`, 'success');
            document.getElementById('new-order-form').reset();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Errore sconosciuto'}`, 'error');
        }
    } catch (error) {
        console.error('Error creating order:', error);
        showNotification('Errore di connessione', 'error');
    }
}

async function handleOrderStatus(event) {
    event.preventDefault();
    
    if (!currentUser) {
        showNotification('Devi essere autenticato per controllare lo stato ordini', 'error');
        return;
    }
    
    const orderId = document.getElementById('status-order-id').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/get_order_status?order_id=${encodeURIComponent(orderId)}&user_id=${encodeURIComponent(currentUser.id)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const status = await response.json();
            displayOrderResult('Stato Ordine', status);
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Ordine non trovato'}`, 'error');
        }
    } catch (error) {
        console.error('Error getting order status:', error);
        showNotification('Errore di connessione', 'error');
    }
}

async function handleMyOrders(event) {
    if (event) event.preventDefault();
    
    if (!currentUser) {
        showNotification('Devi essere autenticato per vedere i tuoi ordini', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/get_order_status?user_id=${encodeURIComponent(currentUser.id)}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const orders = await response.json();
            displayOrderResult('I Miei Ordini', orders);
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Nessun ordine trovato'}`, 'error');
        }
    } catch (error) {
        console.error('Error getting my orders:', error);
        showNotification('Errore di connessione', 'error');
    }
}

function displayOrderResult(title, data) {
    const resultsContainer = document.getElementById('orders-results');
    
    if (Array.isArray(data) && data.length > 0) {
        // Display multiple orders
        let ordersHtml = `<div class="result-card"><h4>${title}</h4>`;
        data.forEach((order, index) => {
            ordersHtml += `
                <div class="order-item" style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 10px; background: #f7fafc;">
                    <h5>Ordine #${index + 1}</h5>
                    <p><strong>ID:</strong> ${order.id || 'N/A'}</p>
                    <p><strong>Stato:</strong> ${order.status || 'N/A'}</p>
                    <p><strong>Piatto ID:</strong> ${order.dish_id || 'N/A'}</p>
                    <p><strong>Utente ID:</strong> ${order.user_id || 'N/A'}</p>
                    ${order.created_at ? `<p><strong>Creato:</strong> ${new Date(order.created_at).toLocaleString()}</p>` : ''}
                </div>
            `;
        });
        ordersHtml += '</div>';
        resultsContainer.innerHTML = ordersHtml;
    } else if (data && typeof data === 'object') {
        // Display single order
        resultsContainer.innerHTML = `
            <div class="result-card">
                <h4>${title}</h4>
                <div class="order-item" style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; background: #f7fafc;">
                    <p><strong>ID:</strong> ${data.id || 'N/A'}</p>
                    <p><strong>Stato:</strong> ${data.status || 'N/A'}</p>
                    <p><strong>Piatto ID:</strong> ${data.dish_id || 'N/A'}</p>
                    <p><strong>Utente ID:</strong> ${data.user_id || 'N/A'}</p>
                    ${data.created_at ? `<p><strong>Creato:</strong> ${new Date(data.created_at).toLocaleString()}</p>` : ''}
                </div>
            </div>
        `;
    } else {
        // Fallback to JSON display
        resultsContainer.innerHTML = `
            <div class="result-card">
                <h4>${title}</h4>
                <pre style="background: #f7fafc; padding: 15px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap;">${JSON.stringify(data, null, 2)}</pre>
            </div>
        `;
    }
}

// Utility functions
function showLoading(container) {
    container.innerHTML = '<div style="text-align: center; padding: 40px;"><div class="loading"></div><p style="margin-top: 10px; color: #718096;">Caricamento...</p></div>';
}

function showNotification(message, type = 'info') {
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Auto-hide notification after 3 seconds
setTimeout(() => {
    if (notification.classList.contains('show')) {
        notification.classList.remove('show');
    }
}, 3000);
