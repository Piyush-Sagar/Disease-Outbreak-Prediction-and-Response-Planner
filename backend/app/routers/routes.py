"""Routing endpoints: graph info + Dijkstra vs A* shortest paths."""

import re

from fastapi import APIRouter, HTTPException

from ..schemas import RouteRequest, RouteOut
from ..services.routing.astar import astar
from ..services.routing.dijkstra import dijkstra
from ..services.routing.graph import build_graph, city_node_id

router = APIRouter(prefix="/api", tags=["routes"])

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


@router.get("/route/graph")
def route_graph():
    g = _get_graph()
    return {
        "nodes": list(g.nodes.values()),
        "edges": g.edges,
        "counts": {"nodes": len(g.nodes), "edges": len(g.edges)},
    }


def _resolve(node_ref: str) -> str:
    g = _get_graph()
    ref = node_ref.strip()
    node_id = city_node_id(g, ref)
    if node_id:
        return node_id
    if ref in g.nodes:
        return ref
    raise HTTPException(status_code=404, detail=f"Unknown location: {node_ref}")


def _rebuild(node_ids: list[str]) -> list[dict]:
    g = _get_graph()
    return [
        {"id": nid, "name": g.nodes[nid]["name"], "latitude": g.nodes[nid]["latitude"],
         "longitude": g.nodes[nid]["longitude"]}
        for nid in node_ids if nid in g.nodes
    ]


def _edge_links(path: list[str]) -> list[dict]:
    g = _get_graph()
    links = []
    for a, b in zip(path, path[1:]):
        for edge in g.edges:
            if {edge["from"], edge["to"]} == {a, b}:
                links.append(edge)
                break
    return links


@router.post("/route", response_model=RouteOut)
def compute_route(body: RouteRequest):
    start = _resolve(body.start)
    goal = _resolve(body.goal)
    weight = "distance" if body.weight == "distance" else "time"

    d_result = dijkstra(_get_graph(), start, goal, weight=weight)
    a_result = astar(_get_graph(), start, goal, weight=weight)

    path = d_result["path"] or a_result["path"]
    return {
        "start_node": start,
        "goal_node": goal,
        "weight": weight,
        "dijkstra": dict(d_result),
        "astar": dict(a_result),
        "nodes": _rebuild(path),
        "edges": _edge_links(path),
        "comparison": {
            "dijkstra_explored": d_result.get("explored"),
            "astar_explored": a_result.get("explored"),
            "faster_algorithm": None,
        },
    }