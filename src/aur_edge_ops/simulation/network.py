"""Software-only network simulator and deterministic routing engine."""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from aur_edge_ops.models.topology import (
    Interface,
    Link,
    LinkState,
    Node,
    NodeRole,
    Route,
    RouteType,
)


class NetworkSimulator:
    """In-memory network simulator with deterministic shortest-path routing."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[str, Link] = {}
        self._build_canonical_topology()

    def _build_canonical_topology(self) -> None:
        """Constructs the exact 6-node (4 routers, 2 hosts), 6-link topology."""
        self.nodes = {
            "H1": Node(
                id="H1",
                role=NodeRole.HOST,
                interfaces=[Interface("h1-eth0", "10.0.1.10/24", "R1", "r1-eth0")],
            ),
            "H2": Node(
                id="H2",
                role=NodeRole.HOST,
                interfaces=[Interface("h2-eth0", "10.0.4.10/24", "R4", "r4-eth2")],
            ),
            "R1": Node(
                id="R1",
                role=NodeRole.ROUTER,
                interfaces=[
                    Interface("r1-eth0", "10.0.1.1/24", "H1", "h1-eth0"),
                    Interface("r1-eth1", "10.0.12.1/24", "R2", "r2-eth0"),
                    Interface("r1-eth2", "10.0.13.1/24", "R3", "r3-eth0"),
                ],
            ),
            "R2": Node(
                id="R2",
                role=NodeRole.ROUTER,
                interfaces=[
                    Interface("r2-eth0", "10.0.12.2/24", "R1", "r1-eth1"),
                    Interface("r2-eth1", "10.0.24.2/24", "R4", "r4-eth0"),
                ],
            ),
            "R3": Node(
                id="R3",
                role=NodeRole.ROUTER,
                interfaces=[
                    Interface("r3-eth0", "10.0.13.3/24", "R1", "r1-eth2"),
                    Interface("r3-eth1", "10.0.34.3/24", "R4", "r4-eth1"),
                ],
            ),
            "R4": Node(
                id="R4",
                role=NodeRole.ROUTER,
                interfaces=[
                    Interface("r4-eth0", "10.0.24.4/24", "R2", "r2-eth1"),
                    Interface("r4-eth1", "10.0.34.4/24", "R3", "r3-eth1"),
                    Interface("r4-eth2", "10.0.4.1/24", "H2", "h2-eth0"),
                ],
            ),
        }

        self.links = {
            "L1": Link("L1", "H1", "R1", "h1-eth0", "r1-eth0", cost=1),
            "L2": Link("L2", "R1", "R2", "r1-eth1", "r2-eth0", cost=10),
            "L3": Link("L3", "R2", "R4", "r2-eth1", "r4-eth0", cost=10),
            "L4": Link("L4", "R1", "R3", "r1-eth2", "r3-eth0", cost=20),
            "L5": Link("L5", "R3", "R4", "r3-eth1", "r4-eth1", cost=20),
            "L6": Link("L6", "R4", "H2", "r4-eth2", "h2-eth0", cost=1),
        }

    def get_adjacency(self) -> Dict[str, List[Tuple[str, int, str]]]:
        """Returns adjacency list of operational (UP) links: {src: [(dst, cost, link_id)]}."""
        adj: Dict[str, List[Tuple[str, int, str]]] = {node_id: [] for node_id in self.nodes}
        for link in self.links.values():
            if link.state == LinkState.UP:
                adj[link.source].append((link.target, link.cost, link.id))
                adj[link.target].append((link.source, link.cost, link.id))
        return adj

    def compute_shortest_path(self, source: str = "H1", target: str = "H2") -> Optional[Tuple[List[str], int]]:
        """Dijkstra shortest path with deterministic lexicographic tie-breaking."""
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Unknown node: source={source}, target={target}")

        adj = self.get_adjacency()
        # Heap tuple: (cost, current_node, path)
        heap: List[Tuple[int, str, List[str]]] = [(0, source, [source])]
        min_costs: Dict[str, int] = {}

        while heap:
            cost, curr, path = heapq.heappop(heap)
            if curr in min_costs and min_costs[curr] <= cost:
                continue
            min_costs[curr] = cost

            if curr == target:
                return path, cost

            for neighbor, weight, _ in adj.get(curr, []):
                next_cost = cost + weight
                if neighbor not in min_costs or next_cost < min_costs[neighbor]:
                    heapq.heappush(heap, (next_cost, neighbor, path + [neighbor]))

        return None

    def get_active_route(self) -> Route:
        """Determines the current operational route between H1 and H2."""
        result = self.compute_shortest_path("H1", "H2")
        if not result:
            return Route(path=[], total_cost=float("inf"), route_type=RouteType.NONE)  # type: ignore[arg-type]

        path, cost = result
        if path == ["H1", "R1", "R2", "R4", "H2"]:
            rtype = RouteType.PRIMARY
        elif path == ["H1", "R1", "R3", "R4", "H2"]:
            rtype = RouteType.BACKUP
        else:
            rtype = RouteType.DEGRADED

        return Route(path=path, total_cost=cost, route_type=rtype)

    def fail_link(self, link_id: str) -> None:
        """Sets a link state to DOWN."""
        if link_id not in self.links:
            raise ValueError(f"Unknown link ID: {link_id}")
        self.links[link_id].state = LinkState.DOWN

    def recover_link(self, link_id: str) -> None:
        """Sets a link state to UP."""
        if link_id not in self.links:
            raise ValueError(f"Unknown link ID: {link_id}")
        self.links[link_id].state = LinkState.UP

    def recover_all(self) -> None:
        """Restores all links to UP state (baseline)."""
        for link in self.links.values():
            link.state = LinkState.UP

    def get_state(self) -> Dict[str, Any]:
        """Returns structured simulation state."""
        active = self.get_active_route()
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [link.to_dict() for link in self.links.values()],
            "active_route": active.to_dict(),
            "primary_route": {
                "path": ["H1", "R1", "R2", "R4", "H2"],
                "total_cost": 22,
                "route_type": "PRIMARY",
            },
            "backup_route": {
                "path": ["H1", "R1", "R3", "R4", "H2"],
                "total_cost": 42,
                "route_type": "BACKUP",
            },
            "simulated": True,
        }

