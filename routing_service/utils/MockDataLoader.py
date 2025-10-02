from typing import Dict, Tuple, List, Optional
import heapq

class WeightedGraph:
    def __init__(self) -> None:
        # es: {"Centro": {"Porta Sud": 2.0, "Stazione": 1.0}, ...}
        self.adj: Dict[str, Dict[str, float]] = {}

    def add_node(self, n: str) -> None:
        self.adj.setdefault(n, {})

    def add_edge(self, a: str, b: str, w: float) -> None:
        """Arco NON orientato con peso w."""
        self.add_node(a)
        self.add_node(b)
        self.adj[a][b] = float(w)
        self.adj[b][a] = float(w)

    def nodes(self) -> List[str]:
        return list(self.adj.keys())

    def neighbors(self, n: str) -> Dict[str, float]:
        return self.adj.get(n, {})

    def dijkstra_distance(self, src: str, dst: str) -> Optional[float]:
        """Distanza minima (somma dei pesi) da src a dst. None se non raggiungibile."""
        if src not in self.adj or dst not in self.adj:
            return None
        if src == dst:
            return 0.0

        dist: Dict[str, float] = {src: 0.0}
        pq: List[Tuple[float, str]] = [(0.0, src)]
        visited: set[str] = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            if u == dst:
                return d
            for v, w in self.adj[u].items():
                if v in visited:
                    continue
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return None


def build_mock_graph() -> WeightedGraph:
    g = WeightedGraph()
    edges = [
        ("Centro", "Porta Sud", 2.0),
        ("Centro", "Quartiere Verde", 2.5),
        ("Centro", "Stazione", 1.0),
        ("Stazione", "Nord", 1.8),
        ("Porta Sud", "Quartiere Verde", 1.2),
        ("Quartiere Verde", "Nord", 2.2),
    ]
    for a, b, w in edges:
        g.add_edge(a, b, w)
    return g
