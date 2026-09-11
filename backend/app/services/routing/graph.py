"""Road network graph built from `data/roads.json`.

Nodes are Indian cities plus synthetic highway junctions. Edges carry
distance (km) and travel time (minutes). The graph powers both Dijkstra and
A* shortest-path calculators used by the response routing endpoint.
"""

import json
import math
from dataclasses import dataclass, field

from ... import config


@dataclass
class Graph:
    adjacency: dict[str, list[tuple[str, float, float]]] = field(default_factory=dict)
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)


def _load_roads() -> dict:
    with open(config.REPO_ROOT + "/data/roads.json", encoding="utf-8") as fh:
        return json.load(fh)


def build_graph() -> Graph:
    raw = _load_roads()
    graph = Graph()
    for node in raw["nodes"]:
        graph.nodes[node["id"]] = {
            "id": node["id"],
            "name": node["name"],
            "latitude": node["latitude"],
            "longitude": node["longitude"],
        }
        graph.adjacency[node["id"]] = []
    for edge in raw["edges"]:
        a, b = edge["from"], edge["to"]
        for src, dst in ((a, b), (b, a)):
            graph.adjacency.setdefault(src, []).append(
                (dst, float(edge["distance_km"]), float(edge["travel_time_min"]))
            )
        graph.edges.append(
            {"from": a, "to": b, "distance_km": edge["distance_km"], "travel_time_min": edge["travel_time_min"]}
        )
    return graph


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates, in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def max_speed_km_per_min(graph: Graph) -> float:
    """Fastest observed edge speed, used to build an admissible A* heuristic."""
    speeds = [d / t for _, d, t in _iter_edges(graph) if t > 0]
    return max(speeds) if speeds else 1.0


def _iter_edges(graph: Graph):
    for edge in graph.edges:
        yield edge["from"], float(edge["distance_km"]), float(edge["travel_time_min"])


def city_node_id(graph: Graph, region_name: str) -> str | None:
    """Map a region/city display name to a road-graph node id."""
    slug = region_name.strip().lower().replace(" ", "-")
    candidate = f"city-{slug}"
    if candidate in graph.nodes:
        return candidate
    for node in graph.nodes.values():
        if node["name"].lower() == region_name.strip().lower():
            return node["id"]
    return None