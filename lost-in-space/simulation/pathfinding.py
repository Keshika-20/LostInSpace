"""A* pathfinding on the known map only."""
from __future__ import annotations
from typing import List, Optional, Tuple, Dict
import heapq
from .models import Position
from .exploration_map import ExplorationMap

MOVE_COST = 1.0


def heuristic(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(start: Position, goal: Position, known_map: ExplorationMap) -> Optional[List[Position]]:
    """
    A* on known traversable cells.
    Returns list of positions including start and goal, or None if unreachable.
    """
    if start == goal:
        return [start]
    if not known_map.is_traversable(goal) and known_map.is_known(goal):
        # known obstacle or unknown that we treat as blocked for planning
        # (unknown cells are not traversable)
        return None

    open_set: List[Tuple[float, int, Position]] = []
    counter = 0
    heapq.heappush(open_set, (0.0 + heuristic(start, goal), counter, start))
    came_from: Dict[Position, Position] = {}
    g_score: Dict[Position, float] = {start: 0.0}
    closed: set = set()

    while open_set:
        _, _, current = heapq.heappop(open_set)
        if current in closed:
            continue
        closed.add(current)
        if current == goal:
            # reconstruct
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        r, c = current
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbour = (r + dr, c + dc)
            if neighbour in closed:
                continue
            if not known_map.is_traversable(neighbour) and neighbour != goal:
                # allow stepping onto goal even if marked unknown? no – only known traversable
                continue
            if not known_map.is_traversable(neighbour):
                continue
            tentative = g_score[current] + MOVE_COST
            if neighbour not in g_score or tentative < g_score[neighbour]:
                g_score[neighbour] = tentative
                came_from[neighbour] = current
                counter += 1
                f = tentative + heuristic(neighbour, goal)
                heapq.heappush(open_set, (f, counter, neighbour))
    return None


def estimate_route_energy(path: Optional[List[Position]]) -> float:
    if not path or len(path) < 2:
        return 0.0
    return (len(path) - 1) * MOVE_COST


def is_route_valid(path: Optional[List[Position]], known_map: ExplorationMap) -> bool:
    if path is None or len(path) == 0:
        return False
    for i, pos in enumerate(path):
        if i == 0:
            continue
        if not known_map.is_traversable(pos):
            return False
        # adjacency
        prev = path[i - 1]
        if abs(pos[0] - prev[0]) + abs(pos[1] - prev[1]) != 1:
            return False
    return True
