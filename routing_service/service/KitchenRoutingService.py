from __future__ import annotations
import uuid
from typing import Dict, List, Optional, Any, Tuple

from routing_service.utils.MockDataLoader import WeightedGraph, build_mock_graph


class KitchenRoutingService:
    def __init__(self, graph: Optional[WeightedGraph] = None) -> None:
        self._kitchen_positions: Dict[uuid.UUID, str] = {}
        self._graph: WeightedGraph = graph if graph is not None else build_mock_graph()

    # --- Cucine ---
    def set_kitchen_location(self, kitchen_id: uuid.UUID, neighborhood: str) -> None:
        # assicura che il quartiere esista nel grafo
        self._graph.add_node(neighborhood)
        self._kitchen_positions[kitchen_id] = neighborhood

    def list_kitchens(self) -> List[Dict[str, str]]:
        return [{"kitchen_id": str(k), "neighborhood": nb} for k, nb in self._kitchen_positions.items()]

    def delete_kitchen_location(self, kitchen_id: uuid.UUID) -> bool:
        return self._kitchen_positions.pop(kitchen_id, None) is not None

    def resolve_kitchen_neighborhood(self, kitchen_id: uuid.UUID) -> Optional[str]:
        return self._kitchen_positions.get(kitchen_id)

    # --- Grafo ---
    def get_graph_snapshot(self) -> Dict[str, Any]:
        nodes = sorted(self._graph.nodes())
        edges: List[Dict[str, Any]] = []
        seen: set[Tuple[str, str]] = set()
        for a in self._graph.nodes():
            for b, w in self._graph.neighbors(a).items():
                edge = tuple(sorted((a, b)))
                if edge in seen:
                    continue
                seen.add(edge)
                edges.append({"da": edge[0], "a": edge[1], "peso": w})
        return {"graph": {"quartieri": nodes, "archi": edges}, "kitchens": self.list_kitchens()}

    # --- Distanze ---
    def shortest_distance(self, src: str, dst: str) -> Optional[float]:
        if src == dst:
            return 0.0
        return self._graph.dijkstra_distance(src, dst)
