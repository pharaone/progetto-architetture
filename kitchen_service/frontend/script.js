// Configuration
const API_BASE_URL = 'http://localhost:8001/api';
const API_KEY = 'changeme123';
const KITCHEN_ID = '11111111-1111-1111-1111-111111111111';

// Helper function to generate UUID v4
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Helper function to validate UUID format
function isValidUUID(uuid) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
}

// DOM elements
const sections = document.querySelectorAll('.section');
const navButtons = document.querySelectorAll('.nav-btn');
const ordersContainer = document.getElementById('orders-container');
const menuGrid = document.getElementById('menu-grid');
const dishModal = document.getElementById('dish-modal');
const notification = document.getElementById('notification');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeForms();
    loadKitchenStatus();
    loadOrders();
    
    // Auto-refresh orders every 30 seconds
    setInterval(loadOrders, 30000);
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
    
    // Load data based on section
    if (sectionName === 'orders') {
        loadOrders();
    } else if (sectionName === 'menu') {
        loadMenu();
    } else if (sectionName === 'status') {
        loadKitchenStatus();
    }
}

// Forms initialization
function initializeForms() {
    document.getElementById('add-dish-btn').addEventListener('click', showDishModal);
    document.getElementById('dish-form').addEventListener('submit', handleAddDish);
    document.querySelector('.close').addEventListener('click', hideDishModal);
    document.getElementById('refresh-orders-btn').addEventListener('click', loadOrders);
    document.getElementById('toggle-operational-btn').addEventListener('click', toggleOperational);
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === dishModal) {
            hideDishModal();
        }
    });
}

// Orders functions
async function loadOrders() {
    try {
        showLoading(ordersContainer);
        console.log('Loading orders from:', `${API_BASE_URL}/orders`);
        const response = await fetch(`${API_BASE_URL}/orders`);
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const orders = await response.json();
            console.log('Orders received:', orders);
            displayOrders(orders);
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            showNotification(`Errore nel caricamento degli ordini: ${response.status}`, 'error');
            ordersContainer.innerHTML = `<p style="text-align: center; color: #6b7280; padding: 40px;">Errore nel caricamento<br><small>${response.status}: ${errorText.substring(0, 100)}</small></p>`;
        }
    } catch (error) {
        console.error('Error loading orders:', error);
        showNotification('Errore di connessione: ' + error.message, 'error');
        ordersContainer.innerHTML = `<p style="text-align: center; color: #6b7280; padding: 40px;">Errore di connessione<br><small>${error.message}</small></p>`;
    }
}

function displayOrders(orders) {
    if (!orders || orders.length === 0) {
        ordersContainer.innerHTML = '<p style="text-align: center; color: #6b7280; padding: 40px;">Nessun ordine da preparare 🎉</p>';
        return;
    }
    
    let ordersHtml = '';
    
    orders.forEach((order, index) => {
        const statusInfo = getStatusInfo(order.status);
        
        ordersHtml += `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-number">
                        <span class="order-icon">🍽️</span>
                        <span class="order-title">Ordine #${index + 1}</span>
                    </div>
                    <span class="status-badge status-${statusInfo.class}">${statusInfo.icon} ${statusInfo.text}</span>
                </div>
                
                <div class="order-body">
                    <div class="order-detail-item">
                        <span class="detail-label">ID Ordine:</span>
                        <span class="detail-value">${formatOrderId(order.order_id)}</span>
                    </div>
                    ${order.dish_id ? `
                    <div class="order-detail-item">
                        <span class="detail-label">Piatto ID:</span>
                        <span class="detail-value">${formatOrderId(order.dish_id)}</span>
                    </div>
                    ` : `
                    <div class="order-detail-item">
                        <span class="detail-label">Piatto:</span>
                        <span class="detail-value" style="color: #9ca3af; font-style: italic;">Informazioni non disponibili</span>
                    </div>
                    `}
                </div>
                
                <div class="order-actions">
                    ${order.status !== 'completed' && order.status !== 'cancelled' ? `
                        <div class="status-selector">
                            <label for="status-${order.order_id}">
                                <span style="margin-right: 8px;">🔄</span>
                                Cambia Stato:
                            </label>
                            <select id="status-${order.order_id}" class="status-select">
                                <option value="">-- Seleziona --</option>
                                <option value="pending" ${order.status === 'pending' ? 'selected' : ''}>⏳ In Attesa</option>
                                <option value="received" ${order.status === 'received' ? 'selected' : ''}>✅ Ricevuto</option>
                                <option value="preparing" ${order.status === 'preparing' ? 'selected' : ''}>👨‍🍳 In Preparazione</option>
                                <option value="ready_for_pickup" ${order.status === 'ready_for_pickup' ? 'selected' : ''}>🎉 Pronto per Ritiro</option>
                                <option value="completed" ${order.status === 'completed' ? 'selected' : ''}>✨ Completato</option>
                                <option value="cancelled" ${order.status === 'cancelled' ? 'selected' : ''}>❌ Annullato</option>
                            </select>
                            <button class="btn btn-primary btn-small" onclick="updateOrderStatusFromSelect('${order.order_id}')">
                                Aggiorna
                            </button>
                        </div>
                    ` : `
                        <p style="text-align: center; color: #6b7280; font-style: italic;">
                            Ordine ${order.status === 'completed' ? 'completato' : 'annullato'}
                        </p>
                    `}
                </div>
            </div>
        `;
    });
    
    ordersContainer.innerHTML = ordersHtml;
}

async function updateOrderStatusFromSelect(orderId) {
    const selectElement = document.getElementById(`status-${orderId}`);
    const newStatus = selectElement.value;
    
    if (!newStatus) {
        showNotification('Seleziona uno stato prima di aggiornare', 'error');
        return;
    }
    
    await updateOrderStatus(orderId, newStatus);
}

async function updateOrderStatus(orderId, newStatus) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.ok) {
            showNotification(`✅ Stato ordine aggiornato a: ${getStatusInfo(newStatus).text}`, 'success');
            await loadOrders(); // Reload orders
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Impossibile aggiornare lo stato'}`, 'error');
        }
    } catch (error) {
        console.error('Error updating order status:', error);
        showNotification('Errore di connessione', 'error');
    }
}

// Menu functions
async function loadMenu() {
    try {
        showLoading(menuGrid);
        console.log('Loading menu from:', `${API_BASE_URL}/menu/dishes`);
        const response = await fetch(`${API_BASE_URL}/menu/dishes`);
        
        if (response.ok) {
            const dishes = await response.json();
            console.log('Dishes received:', dishes);
            displayMenu(dishes);
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            showNotification(`Errore nel caricamento del menu: ${response.status}`, 'error');
            menuGrid.innerHTML = `<p style="text-align: center; color: #6b7280; grid-column: 1/-1; padding: 40px;">Errore nel caricamento del menu</p>`;
        }
    } catch (error) {
        console.error('Error loading menu:', error);
        showNotification('Errore di connessione: ' + error.message, 'error');
        menuGrid.innerHTML = `<p style="text-align: center; color: #6b7280; grid-column: 1/-1; padding: 40px;">Errore di connessione</p>`;
    }
}

function displayMenu(dishes) {
    if (!dishes || dishes.length === 0) {
        menuGrid.innerHTML = '<p style="text-align: center; color: #6b7280; grid-column: 1/-1; padding: 40px;">Nessun piatto nel menu 🍽️<br><small>Clicca su "Aggiungi Piatto" per iniziare</small></p>';
        return;
    }
    
    let menuHtml = '';
    
    dishes.forEach((dish) => {
        const isAvailable = dish.available_quantity > 0;
        const availabilityClass = isAvailable ? 'available' : 'unavailable';
        
        menuHtml += `
            <div class="menu-card ${availabilityClass}">
                <div class="menu-card-header">
                    <h3 class="dish-name">${dish.name}</h3>
                    <span class="dish-price">€${dish.price.toFixed(2)}</span>
                </div>
                
                <div class="menu-card-body">
                    <div class="quantity-info">
                        <span class="quantity-label">Disponibilità:</span>
                        <span class="quantity-value ${isAvailable ? 'in-stock' : 'out-of-stock'}">
                            ${dish.available_quantity} ${dish.available_quantity === 1 ? 'porzione' : 'porzioni'}
                        </span>
                    </div>
                    
                    <div class="dish-id-info">
                        <span style="font-size: 0.75rem; color: #9ca3af;">ID: ${formatOrderId(dish.dish_id)}</span>
                    </div>
                </div>
                
                <div class="menu-card-actions">
                    <button class="btn btn-secondary btn-small" onclick="restockDish('${dish.dish_id}', '${dish.name}')">
                        <span style="margin-right: 4px;">📦</span>
                        Ricarica
                    </button>
                    <button class="btn btn-danger btn-small" onclick="deleteDish('${dish.dish_id}', '${dish.name}')">
                        <span style="margin-right: 4px;">🗑️</span>
                        Elimina
                    </button>
                </div>
            </div>
        `;
    });
    
    menuGrid.innerHTML = menuHtml;
}

async function restockDish(dishId, dishName) {
    const amount = prompt(`Quante porzioni vuoi aggiungere a "${dishName}"?`, '5');
    
    if (!amount || isNaN(amount) || parseInt(amount) <= 0) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/menu/dishes/${dishId}/restock?amount=${amount}`, {
            method: 'PATCH',
            headers: {
                'X-API-Key': API_KEY
            }
        });
        
        if (response.ok) {
            const updatedDish = await response.json();
            showNotification(`✅ Scorta di "${dishName}" aggiornata! Nuova quantità: ${updatedDish.available_quantity}`, 'success');
            await loadMenu();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Impossibile aggiornare la scorta'}`, 'error');
        }
    } catch (error) {
        console.error('Error restocking dish:', error);
        showNotification('Errore di connessione', 'error');
    }
}

async function deleteDish(dishId, dishName) {
    if (!confirm(`Sei sicuro di voler eliminare "${dishName}" dal menu?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/menu/dishes/${dishId}`, {
            method: 'DELETE',
            headers: {
                'X-API-Key': API_KEY
            }
        });
        
        if (response.ok) {
            showNotification(`✅ Piatto "${dishName}" eliminato dal menu`, 'success');
            await loadMenu();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Impossibile eliminare il piatto'}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting dish:', error);
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

function generateAndFillDishId() {
    const dishIdInput = document.getElementById('dish-id');
    dishIdInput.value = generateUUID();
    dishIdInput.focus();
    // Feedback visivo
    dishIdInput.style.backgroundColor = '#d1fae5';
    setTimeout(() => {
        dishIdInput.style.backgroundColor = '';
    }, 500);
}

async function handleAddDish(event) {
    event.preventDefault();
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span style="margin-right: 8px;">⏳</span>Aggiunta in corso...';
    
    // Leggi l'ID dal campo o genera uno nuovo
    let dishId = document.getElementById('dish-id').value.trim();
    
    // Se l'utente ha inserito un ID, validalo
    if (dishId && !isValidUUID(dishId)) {
        showNotification('❌ ID piatto non valido. Inserisci un UUID valido o lascia vuoto per generarne uno automatico.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        return;
    }
    
    // Se vuoto, genera un UUID automatico
    if (!dishId) {
        dishId = generateUUID();
        console.log(`Generated automatic dish ID: ${dishId}`);
    } else {
        console.log(`Using user-provided dish ID: ${dishId}`);
    }
    
    const dishData = {
        dish_id: dishId,
        name: document.getElementById('dish-name').value,
        price: parseFloat(document.getElementById('dish-price').value),
        available_quantity: parseInt(document.getElementById('dish-quantity').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/menu/dishes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(dishData)
        });
        
        if (response.ok) {
            const dish = await response.json();
            const idInfo = document.getElementById('dish-id').value.trim() ? '' : ` (ID: ${formatOrderId(dish.dish_id)})`;
            showNotification(`✨ ${dish.name} aggiunto con successo!${idInfo}`, 'success');
            hideDishModal();
            loadMenu();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Errore sconosciuto'}`, 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error adding dish:', error);
        showNotification('Errore di connessione', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Kitchen Status functions
async function loadKitchenStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/kitchen`);
        const status = await response.json();
        
        if (response.ok) {
            displayKitchenStatus(status);
        } else {
            showNotification('Errore nel caricamento dello stato cucina', 'error');
        }
    } catch (error) {
        console.error('Error loading kitchen status:', error);
        showNotification('Errore di connessione', 'error');
    }
}

function displayKitchenStatus(status) {
    const operationalEl = document.getElementById('operational-status');
    const currentLoadEl = document.getElementById('current-load');
    const maxLoadEl = document.getElementById('max-load');
    const statusIndicator = document.getElementById('kitchen-status');
    
    operationalEl.textContent = status.is_operational ? '✅ Operativa' : '❌ Non Operativa';
    operationalEl.style.color = status.is_operational ? '#10b981' : '#ef4444';
    
    currentLoadEl.textContent = status.current_load;
    maxLoadEl.textContent = status.max_load;
    
    statusIndicator.className = `status-indicator ${status.is_operational ? 'online' : 'offline'}`;
}

async function toggleOperational() {
    try {
        // Prima ottieni lo stato attuale
        const statusResponse = await fetch(`${API_BASE_URL}/kitchen`);
        const currentStatus = await statusResponse.json();
        
        // Inverti lo stato
        const newStatus = !currentStatus.is_operational;
        
        const response = await fetch(`${API_BASE_URL}/kitchen?is_operational=${newStatus}`, {
            method: 'PATCH',
            headers: {
                'X-API-Key': API_KEY
            }
        });
        
        if (response.ok) {
            showNotification(`✅ Cucina ora ${newStatus ? 'operativa' : 'non operativa'}`, 'success');
            await loadKitchenStatus();
        } else {
            const error = await response.json();
            showNotification(`Errore: ${error.detail || 'Impossibile cambiare stato'}`, 'error');
        }
    } catch (error) {
        console.error('Error toggling operational status:', error);
        showNotification('Errore di connessione', 'error');
    }
}

// Helper functions
function getStatusInfo(status) {
    const statusMap = {
        'pending': { text: 'In Attesa', icon: '⏳', class: 'pending' },
        'received': { text: 'Ricevuto', icon: '✅', class: 'received' },
        'preparing': { text: 'In Preparazione', icon: '👨‍🍳', class: 'preparing' },
        'ready_for_pickup': { text: 'Pronto', icon: '🎉', class: 'ready' },
        'completed': { text: 'Completato', icon: '✨', class: 'completed' },
        'cancelled': { text: 'Annullato', icon: '❌', class: 'cancelled' }
    };
    return statusMap[status] || { text: status, icon: '❓', class: 'unknown' };
}

function formatOrderId(id) {
    if (!id) return 'N/A';
    const idStr = id.toString();
    return idStr.length > 12 ? idStr.substring(0, 8) + '...' + idStr.substring(idStr.length - 4) : idStr;
}

function showLoading(container) {
    container.innerHTML = '<div style="text-align: center; padding: 40px;"><div class="loading"></div><p style="margin-top: 10px; color: #6b7280;">Caricamento...</p></div>';
}

function showNotification(message, type = 'info') {
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

