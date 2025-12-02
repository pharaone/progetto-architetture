import uuid
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from routing_service.service.MenuRoutingService import MenuRoutingService
from routing_service.service.KitchenRoutingService import KitchenRoutingService


@pytest.fixture
def mock_kitchen_service():
    """Mock per KitchenRoutingService."""
    service = MagicMock(spec=KitchenRoutingService)
    service.resolve_kitchen_neighborhood = MagicMock()
    service.shortest_distance = MagicMock()
    return service


@pytest.fixture
def mock_producer():
    """Mock per EventProducer."""
    producer = MagicMock()
    producer.publish_disponibilita = AsyncMock()
    producer.publish_conferma_ordine = AsyncMock()
    producer.publish_order_status = AsyncMock()
    return producer


@pytest.fixture
def menu_service(mock_kitchen_service, mock_producer):
    """Istanza di MenuRoutingService con dipendenze mockat."""
    return MenuRoutingService(
        kitchen_service=mock_kitchen_service,
        producer=mock_producer,
        window_ms=100  # Finestra breve per i test
    )


# ============================================================
# TEST: on_new_order
# ============================================================
@pytest.mark.asyncio
async def test_on_new_order(menu_service, mock_producer):
    """Test gestione nuovo ordine."""
    order = {
        "order_id": str(uuid.uuid4()),
        "dish_id": str(uuid.uuid4()),
        "user_neighborhood": "Centro",
        "customer_id": str(uuid.uuid4()),
        "delivery_address": "Via Roma 1"
    }
    
    await menu_service.on_new_order(order)
    
    # Verifica che sia stato pubblicato su Kafka
    mock_producer.publish_disponibilita.assert_called_once()
    
    # Verifica che l'ordine sia stato salvato
    order_id = uuid.UUID(order["order_id"])
    assert order_id in menu_service._orders


# ============================================================
# TEST: on_acceptance
# ============================================================
@pytest.mark.asyncio
async def test_on_acceptance_valid(menu_service):
    """Test accettazione candidatura cucina valida."""
    order_id = uuid.uuid4()
    kitchen_id = uuid.uuid4()
    
    # Prima crea un ordine
    await menu_service.on_new_order({
        "order_id": str(order_id),
        "dish_id": str(uuid.uuid4()),
        "user_neighborhood": "Centro"
    })
    
    # Poi simula accettazione
    payload = {
        "order_id": str(order_id),
        "kitchen_id": str(kitchen_id),
        "can_handle": True
    }
    
    await menu_service.on_acceptance(payload)
    
    # Verifica che il candidato sia stato aggiunto
    state = menu_service._orders.get(order_id)
    assert state is not None
    assert kitchen_id in state.candidates


@pytest.mark.asyncio
async def test_on_acceptance_cannot_handle(menu_service):
    """Test accettazione con can_handle=False."""
    order_id = uuid.uuid4()
    
    await menu_service.on_new_order({
        "order_id": str(order_id),
        "dish_id": str(uuid.uuid4()),
        "user_neighborhood": "Centro"
    })
    
    payload = {
        "order_id": str(order_id),
        "kitchen_id": str(uuid.uuid4()),
        "can_handle": False  # Non può gestire
    }
    
    await menu_service.on_acceptance(payload)
    
    # Verifica che non sia stato aggiunto ai candidati
    state = menu_service._orders.get(order_id)
    assert len(state.candidates) == 0


@pytest.mark.asyncio
async def test_on_acceptance_unknown_order(menu_service):
    """Test accettazione per ordine sconosciuto."""
    payload = {
        "order_id": str(uuid.uuid4()),  # Ordine mai creato
        "kitchen_id": str(uuid.uuid4()),
        "can_handle": True
    }
    
    # Non dovrebbe crashare
    await menu_service.on_acceptance(payload)


# ============================================================
# TEST: _choose_best
# ============================================================
def test_choose_best_single_candidate(menu_service, mock_kitchen_service):
    """Test selezione con un solo candidato."""
    kitchen_id = uuid.uuid4()
    
    mock_kitchen_service.resolve_kitchen_neighborhood.return_value = "Centro"
    mock_kitchen_service.shortest_distance.return_value = 1.0
    
    result = menu_service._choose_best("Stazione", [kitchen_id])
    
    assert result == kitchen_id


def test_choose_best_multiple_candidates(menu_service, mock_kitchen_service):
    """Test selezione della cucina più vicina."""
    kitchen_1 = uuid.uuid4()
    kitchen_2 = uuid.uuid4()
    kitchen_3 = uuid.uuid4()
    
    def resolve_neighborhood(kid):
        if kid == kitchen_1:
            return "Centro"
        elif kid == kitchen_2:
            return "Porta Sud"
        elif kid == kitchen_3:
            return "Nord"
        return None
    
    def calculate_distance(user_nb, kitchen_nb):
        distances = {
            ("Stazione", "Centro"): 1.0,
            ("Stazione", "Porta Sud"): 3.0,
            ("Stazione", "Nord"): 1.5
        }
        return distances.get((user_nb, kitchen_nb))
    
    mock_kitchen_service.resolve_kitchen_neighborhood.side_effect = resolve_neighborhood
    mock_kitchen_service.shortest_distance.side_effect = calculate_distance
    
    result = menu_service._choose_best("Stazione", [kitchen_1, kitchen_2, kitchen_3])
    
    assert result == kitchen_1  # Centro è il più vicino (1.0)


def test_choose_best_no_valid_candidates(menu_service, mock_kitchen_service):
    """Test selezione quando nessun candidato ha neighborhood."""
    kitchen_id = uuid.uuid4()
    
    mock_kitchen_service.resolve_kitchen_neighborhood.return_value = None  # Nessun neighborhood
    
    result = menu_service._choose_best("Stazione", [kitchen_id])
    
    assert result is None


def test_choose_best_empty_candidates(menu_service):
    """Test selezione con lista vuota."""
    result = menu_service._choose_best("Centro", [])
    
    assert result is None


# ============================================================
# TEST: get_assignment
# ============================================================
def test_get_assignment_unknown(menu_service):
    """Test recupero assegnazione ordine sconosciuto."""
    order_id = uuid.uuid4()
    
    result = menu_service.get_assignment(order_id)
    
    assert result == {"state": "unknown"}


@pytest.mark.asyncio
async def test_get_assignment_pending(menu_service):
    """Test recupero assegnazione ordine in attesa."""
    order_id = uuid.uuid4()
    
    await menu_service.on_new_order({
        "order_id": str(order_id),
        "dish_id": str(uuid.uuid4()),
        "user_neighborhood": "Centro"
    })
    
    result = menu_service.get_assignment(order_id)
    
    assert result == {"state": "pending"}


# ============================================================
# TEST: get_order_status & save_status
# ============================================================
def test_save_and_get_order_status(menu_service):
    """Test salvataggio e recupero stato ordine."""
    order_id = uuid.uuid4()
    
    menu_service.save_status(str(order_id), "preparing")
    
    result = menu_service.get_order_status(order_id)
    
    assert result is not None
    assert result["order_id"] == str(order_id)
    assert result["status"] == "preparing"


def test_get_order_status_not_found(menu_service):
    """Test recupero stato ordine non esistente."""
    order_id = uuid.uuid4()
    
    result = menu_service.get_order_status(order_id)
    
    assert result is None



