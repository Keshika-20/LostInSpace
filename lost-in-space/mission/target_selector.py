"""Target selection using only known map information."""
from __future__ import annotations
from typing import Optional, List, Tuple
from simulation.models import Position, Resource
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import find_path, estimate_route_energy


class TargetSelector:
    def __init__(self, exp_map: ExplorationMap):
        self.exp_map = exp_map

    def choose_exploration_frontier(self, current: Position) -> Optional[Position]:
        """Simple nearest frontier cell."""
        frontier = self.exp_map.get_frontier()
        if not frontier:
            return None
        # pick closest by Manhattan
        frontier.sort(key=lambda p: abs(p[0] - current[0]) + abs(p[1] - current[1]))
        return frontier[0]

    def score_resource(self, res: Resource, current: Position, energy: float) -> float:
        """Higher is better. Considers value vs travel cost."""
        path = find_path(current, res.position, self.exp_map)
        if path is None:
            return -1.0
        cost = estimate_route_energy(path)
        if cost > energy * 0.7:  # leave reserve
            return -1.0
        # simple score: value / (cost + 1)
        return res.value / (cost + 1.0)

    def choose_best_resource(self, current: Position, energy: float) -> Optional[Resource]:
        candidates = [r for r in self.exp_map.known_resources if not r.collected]
        if not candidates:
            return None
        best = None
        best_score = -1.0
        for res in candidates:
            s = self.score_resource(res, current, energy)
            if s > best_score:
                best_score = s
                best = res
        return best if best_score > 0 else None

    def choose_nearest_zone(self, current: Position) -> Optional[Position]:
        zones = self.exp_map.known_zones
        if not zones:
            return None
        zones = sorted(zones, key=lambda p: abs(p[0] - current[0]) + abs(p[1] - current[1]))
        for z in zones:
            path = find_path(current, z, self.exp_map)
            if path is not None:
                return z
        return None
