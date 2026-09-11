"""A* search on the road graph with an admissible haversine heuristic.

The heuristic lower-bounds the remaining travel time using the fastest edge
speed on the network, guaranteeing A* returns the optimal path while
typically exploring fewer nodes than plain Dijkstra.
"""

import heapq
import math

from .graph import Graph, haversine_km, max_speed_km_per_min


def astar(
    graph: Graph,
    start: str,
    goal: str,
    weight: str = "time",
) -> dict:
    """Shortest path via A*. `weight` is "time" or "distance".

    Returns the same result shape as `dijkstra` plus nodes visited, so the
    frontend can compare the two algorithms side by side.
    """
    use_time = weight == "time"
    vmax = max_speed_km_per_min(graph)  # admissible heuristic speed
    dist = {node: math.inf for node in graph.nodes}
    prev = {}
    dist[start] = 0.0
    heap = [(0.0, start)]
    explored = 0
    nodes_visited = 0
    while heap:
        f_score, node = heapq.heappop(heap)
        if node == goal:
            break
        nodes_visited += 1
        explored += 1
        for neighbor, distance_km, time_min in graph.adjacency.get(node, []):
            step = distance_km if not use_time else time_min
            candidate = dist[node] + step
            if candidate < dist[neighbor]:
                dist[neighbor] = candidate
                prev[neighbor] = node
                if use_time:
                    h = haversine_km(
                        graph.nodes[neighbor]["latitude"],
                        graph.nodes[neighbor]["longitude"],
                        graph.nodes[goal]["latitude"],
                        graph.nodes[goal]["longitude"],
                    ) / vmax  # lower bound in minutes
                else:
                    h = haversine_km(
                        graph.nodes[neighbor]["latitude"],
                        graph.nodes[neighbor]["longitude"],
                        graph.nodes[goal]["latitude"],
                        graph.nodes[goal]["longitude"],
                    )
                heapq.heappush(heap, (candidate + h, neighbor))
    return _reconstruct(graph, start, goal, prev, dist, weight, explored, nodes_visited)


def _reconstruct(graph, start, goal, prev, dist, weight, explored, nodes_visited) -> dict:
    if goal not in prev and start != goal:
        return {
            "path": [],
            "total_weight": None,
            "total_distance": None,
            "total_time": None,
            "unit": weight,
            "explored": explored,
            "nodes_visited": nodes_visited,
            "error": "No path found",
        }
    if start == goal:
        return {
            "path": [start],
            "total_weight": 0.0,
            "total_distance": 0.0,
            "total_time": 0.0,
            "unit": weight,
            "explored": 1,
            "nodes_visited": 1,
            "error": None,
        }
    segment = []
    node = goal
    while node != start:
        segment.append(node)
        node = prev[node]
    segment.append(start)
    segment.reverse()

    from .dijkstra import _summarize

    result = _summarize(graph, segment, start, goal, weight, explored)
    result["nodes_visited"] = nodes_visited
    result["error"] = None
    return result