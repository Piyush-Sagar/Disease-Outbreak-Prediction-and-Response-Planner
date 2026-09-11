"""Unit tests for the routing algorithms (Dijkstra vs A*)."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.routing.graph import build_graph, city_node_id  # noqa: E402
from app.services.routing.dijkstra import dijkstra  # noqa: E402
from app.services.routing.astar import astar  # noqa: E402


@pytest.fixture(scope="module")
def graph():
    return build_graph()


def test_graph_structure(graph):
    assert len(graph.nodes) >= 12
    assert len(graph.edges) >= 20


def test_city_resolution(graph):
    assert city_node_id(graph, "Chennai") == "city-chennai"
    assert city_node_id(graph, "Mumbai") == "city-mumbai"
    assert city_node_id(graph, "DoesNotExist") is None


@pytest.mark.parametrize("weight", ["time", "distance"])
def test_dijkstra_and_astar_agree(graph, weight):
    start, goal = "city-delhi", "city-kochi"
    d = dijkstra(graph, start, goal, weight=weight)
    a = astar(graph, start, goal, weight=weight)
    assert d["error"] is None
    assert a["error"] is None
    assert d["total_weight"] == pytest.approx(a["total_weight"], abs=0.01)
    assert d["path"][0] == start and d["path"][-1] == goal
    assert a["path"][0] == start and a["path"][-1] == goal


def test_astar_explores_no_more_than_dijkstra(graph):
    start, goal = "city-bengaluru", "city-guwahati"
    d = dijkstra(graph, start, goal, weight="time")
    a = astar(graph, start, goal, weight="time")
    assert a["explored"] <= d["explored"] + 1


def test_route_metric_time_is_smaller_than_distance_number():
    # time weights are minutes (100-500 scale) vs km (200-1900 scale)
    graph = build_graph()
    d_time = dijkstra(graph, "city-mumbai", "city-delhi", weight="time")
    d_dist = dijkstra(graph, "city-mumbai", "city-delhi", weight="distance")
    assert d_time["total_weight"] < d_dist["total_weight"]
    assert d_time["total_distance"] == pytest.approx(d_dist["total_distance"])