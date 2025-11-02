import uuid
import pytest
from typing import Optional

from routing_service.service.KitchenRoutingService import KitchenRoutingService
from routing_service.utils.MockDataLoader import WeightedGraph


@pytest.fixture
def mock_graph():
    """Crea un grafo mock per i test."""
    graph = WeightedGraph()
    graph.add_edge("Centro", "Stazione", 1.0)
    graph.add_edge("Centro", "Porta Sud", 2.0)
    graph.add_edge("Stazione", "Nord", 1.5)
    return graph


@pytest.fixture
def kitchen_service(mock_graph):
    """Istanza di KitchenRoutingService con grafo mockato."""
    return KitchenRoutingService(graph=mock_graph)


# ============================================================
# TEST: set_kitchen_location & resolve_kitchen_neighborhood
# ============================================================
def test_set_kitchen_location(kitchen_service):
    """Test assegnazione posizione cucina."""
    kitchen_id = uuid.uuid4()
    neighborhood = "Centro"
    
    kitchen_service.set_kitchen_location(kitchen_id, neighborhood)
    
    result = kitchen_service.resolve_kitchen_neighborhood(kitchen_id)
    assert result == neighborhood


def test_resolve_kitchen_neighborhood_not_found(kitchen_service):
    """Test risoluzione posizione cucina non registrata."""
    kitchen_id = uuid.uuid4()
    
    result = kitchen_service.resolve_kitchen_neighborhood(kitchen_id)
    
    assert result is None


# ============================================================
# TEST: list_kitchens
# ============================================================
def test_list_kitchens(kitchen_service):
    """Test elenco di tutte le cucine registrate."""
    kitchen_1 = uuid.uuid4()
    kitchen_2 = uuid.uuid4()
    
    kitchen_service.set_kitchen_location(kitchen_1, "Centro")
    kitchen_service.set_kitchen_location(kitchen_2, "Stazione")
    
    result = kitchen_service.list_kitchens()
    
    assert len(result) == 2
    kitchen_ids = [k["kitchen_id"] for k in result]
    assert str(kitchen_1) in kitchen_ids
    assert str(kitchen_2) in kitchen_ids


def test_list_kitchens_empty(kitchen_service):
    """Test elenco quando non ci sono cucine."""
    result = kitchen_service.list_kitchens()
    
    assert result == []


# ============================================================
# TEST: delete_kitchen_location
# ============================================================
def test_delete_kitchen_location_success(kitchen_service):
    """Test rimozione posizione cucina."""
    kitchen_id = uuid.uuid4()
    kitchen_service.set_kitchen_location(kitchen_id, "Centro")
    
    result = kitchen_service.delete_kitchen_location(kitchen_id)
    
    assert result is True
    assert kitchen_service.resolve_kitchen_neighborhood(kitchen_id) is None


def test_delete_kitchen_location_not_found(kitchen_service):
    """Test rimozione posizione cucina non esistente."""
    kitchen_id = uuid.uuid4()
    
    result = kitchen_service.delete_kitchen_location(kitchen_id)
    
    assert result is False


# ============================================================
# TEST: shortest_distance
# ============================================================
def test_shortest_distance_same_node(kitchen_service):
    """Test distanza tra lo stesso nodo."""
    result = kitchen_service.shortest_distance("Centro", "Centro")
    
    assert result == 0.0


def test_shortest_distance_direct_edge(kitchen_service):
    """Test distanza tra nodi direttamente connessi."""
    result = kitchen_service.shortest_distance("Centro", "Stazione")
    
    assert result == 1.0


def test_shortest_distance_indirect_path(kitchen_service):
    """Test distanza con percorso indiretto."""
    result = kitchen_service.shortest_distance("Centro", "Nord")
    
    # Centro -> Stazione (1.0) -> Nord (1.5) = 2.5
    assert result == 2.5


def test_shortest_distance_unreachable(kitchen_service):
    """Test distanza tra nodi non connessi."""
    # Aggiungiamo un nodo isolato
    kitchen_service._graph.add_node("Isolato")
    
    result = kitchen_service.shortest_distance("Centro", "Isolato")
    
    assert result is None


def test_shortest_distance_node_not_in_graph(kitchen_service):
    """Test distanza con nodo non esistente."""
    result = kitchen_service.shortest_distance("Centro", "NonEsistente")
    
    assert result is None


# ============================================================
# TEST: get_graph_snapshot
# ============================================================
def test_get_graph_snapshot(kitchen_service):
    """Test recupero snapshot del grafo."""
    kitchen_id = uuid.uuid4()
    kitchen_service.set_kitchen_location(kitchen_id, "Centro")
    
    result = kitchen_service.get_graph_snapshot()
    
    assert "graph" in result
    assert "kitchens" in result
    assert "quartieri" in result["graph"]
    assert "archi" in result["graph"]
    assert len(result["kitchens"]) == 1

