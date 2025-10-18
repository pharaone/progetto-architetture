// Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentUser = null;

// DOM elements
const sections = document.querySelectorAll('.section');
const navButtons = document.querySelectorAll('.nav-btn');
const menuGrid = document.getElementById('menu-grid');
const dishModal = document.getElementById('dish-modal');
const notification = document.getElementById('notification');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeForms();
    loadMenu();
});

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
    // Menu forms
    document.getElementById('add-dish-btn').addEventListener('click', showDishModal);
    document.getElementById('dish-form').addEventListener('submit', handleAddDish);
    document.querySelector('.close').addEventListener('click', hideDishModal);
    
    // User forms
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('confirm-form').addEventListener('submit', handleConfirm);
    
    // Order forms
    document.getElementById('new-order-form').addEventListener('submit', handleNewOrder);
    document.getElementById('order-status-form').addEventListener('submit', handleOrderStatus);
    document.getElementById('my-orders-form').addEventListener('submit', handleMyOrders);
    
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
        <div style="margin-top: 10px; font-size: 0.9rem; color: #a0aec0;">ID: ${dish.id}</div>
    `;
    return card;
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
            showNotification('Login effettuato con successo!', 'success');
            document.getElementById('login-form').reset();
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
    
    const dishId = document.getElementById('order-dish-id').value;
    const userId = document.getElementById('order-user-id').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/new_order?dish_id=${encodeURIComponent(dishId)}&user_id=${encodeURIComponent(userId)}`, {
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
    
    const orderId = document.getElementById('status-order-id').value;
    const userId = document.getElementById('status-user-id').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/get_order_status?order_id=${encodeURIComponent(orderId)}&user_id=${encodeURIComponent(userId)}`, {
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
    event.preventDefault();
    
    const userId = document.getElementById('my-orders-user-id').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/get_order_status?user_id=${encodeURIComponent(userId)}`, {
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
    resultsContainer.innerHTML = `
        <div class="result-card">
            <h4>${title}</h4>
            <pre style="background: #f7fafc; padding: 15px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap;">${JSON.stringify(data, null, 2)}</pre>
        </div>
    `;
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
