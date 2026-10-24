"""Automated tests for network topology, deterministic routing, failure, and recovery."""

from aur_edge_ops.models.topology import LinkState, NodeRole, RouteType
from aur_edge_ops.simulation.network import NetworkSimulator


def test_topology_node_and_link_structure():
    """Verify exact 4 routers, 2 hosts, and 6 links with expected assignments."""
    sim = NetworkSimulator()
    assert len(sim.nodes) == 6
    assert len(sim.links) == 6

    # Verify routers and hosts
    routers = [n for n in sim.nodes.values() if n.role == NodeRole.ROUTER]
    hosts = [n for n in sim.nodes.values() if n.role == NodeRole.HOST]
    assert {r.id for r in routers} == {"R1", "R2", "R3", "R4"}
    assert {h.id for h in hosts} == {"H1", "H2"}

    # Verify links
    assert set(sim.links.keys()) == {"L1", "L2", "L3", "L4", "L5", "L6"}
    for link in sim.links.values():
        assert link.state == LinkState.UP


def test_baseline_primary_route():
    """Verify that with all links UP, the primary route R1->R2->R4 is chosen with cost 22."""
    sim = NetworkSimulator()
    route = sim.get_active_route()

    assert route.route_type == RouteType.PRIMARY
    assert route.path == ["H1", "R1", "R2", "R4", "H2"]
    assert route.total_cost == 22


def test_primary_failure_switches_to_backup():
    """Verify that failing link L2 (R1-R2) triggers deterministic failover to backup path."""
    sim = NetworkSimulator()
    sim.fail_link("L2")

    assert sim.links["L2"].state == LinkState.DOWN

    route = sim.get_active_route()
    assert route.route_type == RouteType.BACKUP
    assert route.path == ["H1", "R1", "R3", "R4", "H2"]
    assert route.total_cost == 42


def test_recovery_restores_baseline():
    """Verify that recovering all links restores primary route."""
    sim = NetworkSimulator()
    sim.fail_link("L2")
    assert sim.get_active_route().route_type == RouteType.BACKUP

    sim.recover_all()
    assert sim.links["L2"].state == LinkState.UP

    route = sim.get_active_route()
    assert route.route_type == RouteType.PRIMARY
    assert route.path == ["H1", "R1", "R2", "R4", "H2"]
    assert route.total_cost == 22

