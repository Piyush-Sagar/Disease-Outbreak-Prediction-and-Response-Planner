"""Dijkstra's shortest path on the road graph (heap-based)."""

import heapq
import math

from .graph import Graph


def dijkstra(
    graph: Graph,
    start: str,
    goal: str,
    weight: str = "time",
) -> dict:
    """Shortest path from `start` to `goal` minimising edge weight.

    `weight` is "time" (minutes) or "distance" (km).
    Returns {path, total_weight, total_distance, total_time, unit, explored}.
    """
    key = 1 if weight == "distance" else 2  # edge tuple (node, distance, time)
    dist = {node: math.inf for node in graph.nodes}
    prev = {}
    dist[start] = 0.0
    heap = [(0.0, start)]
    explored = 0
    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist > dist[node]:
            continue
        if node == goal:
            break
        explored += 1
        for neighbor, distance_km, time_min in graph.adjacency.get(node, []):
            cost = distance_km if key == 1 else time_min
            candidate = current_dist + cost
            if candidate < dist[neighbor]:
                dist[neighbor] = candidate
                prev[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))
    return _reconstruct(graph, start, goal, prev, dist, weight)


def _reconstruct(graph, start, goal, prev, dist, weight) -> dict:
    if goal not in prev and start != goal:
        return {
            "path": [],
            "total_weight": None,
            "total_distance": None,
            "total_time": None,
            "unit": weight,
            "explored": len(dist),
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
        }
    segment = []
    node = goal
    while node != start:
        segment.append(node)
        node = prev[node]
    segment.append(start)
    segment.reverse()
    return _summarize(graph, segment, start, goal, weight, len(dist))


def _summarize(graph, segment, start, goal, weight, explored) -> dict:
    total_distance = 0.0
    total_time = 0.0
    for a, b in zip(segment, segment[1:]):
        for neighbor, distance_km, time_min in graph.adjacency.get(a, []):
            if neighbor == b:
                total_distance += distance_km
                total_time += time_min
                break
    total_weight = total_distance if weight == "distance" else total_time
    return {
        "path": segment,
        "total_weight": round(total_weight, 1),
        "total_distance": round(total_distance, 1),
        "total_time": round(total_time, 1),
        "unit": weight,
        "explored": explored,
        "error": None,
    }