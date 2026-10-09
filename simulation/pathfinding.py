"""A* pathfinding on the rover's KNOWN map.

Only cells the rover has seen and found free can be walked on.
Unknown cells and known obstacles both count as walls.
"""

import heapq
import math

from simulation.environment import DIRECTIONS, Position
from simulation.exploration_map import ExplorationMap


def manhattan(a: Position, b: Position) -> int:
    """Distance on a 4-direction grid. Never overestimates, so A* stays optimal."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(start: Position, goal: Position, known_map: ExplorationMap):
    """Shortest route from start to goal as a list of (row, col), or None.

    The list includes both start and goal. If start == goal the answer is [start].
    """
    if not known_map.is_known_free(start) or not known_map.is_known_free(goal):
        return None
    if start == goal:
        return [start]

    # Heap items are (f, g, cell): f = steps so far + estimated steps left.
    open_heap = [(manhattan(start, goal), 0, start)]
    best_steps = {start: 0}
    came_from = {}

    while open_heap:
        _, steps, current = heapq.heappop(open_heap)

        # A cheaper way into this cell was found after this entry was pushed.
        if steps > best_steps.get(current, math.inf):
            continue

        if current == goal:
            return _rebuild_route(came_from, current)

        for d_row, d_col in DIRECTIONS:
            nxt = (current[0] + d_row, current[1] + d_col)
            if not known_map.is_known_free(nxt):
                continue
            new_steps = steps + 1
            if new_steps < best_steps.get(nxt, math.inf):
                best_steps[nxt] = new_steps
                came_from[nxt] = current
                priority = new_steps + manhattan(nxt, goal)
                heapq.heappush(open_heap, (priority, new_steps, nxt))

    return None  # the whole reachable area was searched; the goal is not in it


def _rebuild_route(came_from: dict, end: Position) -> list:
    route = [end]
    while end in came_from:
        end = came_from[end]
        route.append(end)
    route.reverse()
    return route


def route_cost(route, move_cost: float = 1.0) -> float:
    """Energy needed to walk the route. No route (None or empty) costs infinity."""
    if not route:
        return math.inf
    return (len(route) - 1) * move_cost


def route_is_valid(route, known_map: ExplorationMap) -> bool:
    """True if every cell is known free and each step moves exactly one cell."""
    if not route:
        return False
    if not all(known_map.is_known_free(cell) for cell in route):
        return False
    for previous, current in zip(route, route[1:]):
        if manhattan(previous, current) != 1:
            return False
    return True