"""Core network topology and state models for the software-only simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeRole(str, Enum):
    ROUTER = "router"
    HOST = "host"


class LinkState(str, Enum):
    UP = "up"
    DOWN = "down"


class RouteType(str, Enum):
    PRIMARY = "PRIMARY"
    BACKUP = "BACKUP"
    DEGRADED = "DEGRADED"
    NONE = "NONE"


@dataclass
class Interface:
    name: str
    ip: str
    peer_node: str
    peer_interface: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ip": self.ip,
            "peer_node": self.peer_node,
            "peer_interface": self.peer_interface,
        }


@dataclass
class Node:
    id: str
    role: NodeRole
    interfaces: List[Interface] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "interfaces": [iface.to_dict() for iface in self.interfaces],
        }


@dataclass
class Link:
    id: str
    source: str
    target: str
    source_interface: str
    target_interface: str
    cost: int
    state: LinkState = LinkState.UP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "source_interface": self.source_interface,
            "target_interface": self.target_interface,
            "cost": self.cost,
            "state": self.state.value,
        }


@dataclass
class Route:
    path: List[str]
    total_cost: int
    route_type: RouteType

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "total_cost": self.total_cost,
            "route_type": self.route_type.value,
        }

