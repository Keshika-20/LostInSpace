"""Rover's known map — only observed cells are visible to the planner."""
from __future__ import annotations
from typing import List, Optional, Set, Tuple
from .models import Position, Resource
from .environment import Environment, EMPTY, OBSTACLE, BASE, COMM_ZONE

# Known-cell states
UNKNOWN = -1
KNOWN_EMPTY = 0
KNOWN_OBSTACLE = 1
KNOWN_BASE = 2
KNOWN_ZONE = 3


class ExplorationMap:
    """Partial knowledge the rover and mission controller are allowed to use."""

    def __init__(self, env: Environment):
        self.rows = env.rows
        self.cols = env.cols
        self._env = env  # only for observation; never for decisions
        self.known: List[List[int]] = [[UNKNOWN for _ in range(self.cols)] for _ in range(self.rows)]
        self.explored_count = 0
        self.known_resources: List[Resource] = []  # copies of discovered resources
        self.known_zones: List[Position] = []
        self.base_known = False
        # initial observation around base
        self.observe(env.base_pos, radius=2)

    def is_known(self, pos: Position) -> bool:
        r, c = pos
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return False
        return self.known[r][c] != UNKNOWN

    def is_traversable(self, pos: Position) -> bool:
        """Safe read-only: only known traversable cells."""
        r, c = pos
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return False
        cell = self.known[r][c]
        return cell in (KNOWN_EMPTY, KNOWN_BASE, KNOWN_ZONE)

    def get_cell(self, pos: Position) -> int:
        r, c = pos
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return KNOWN_OBSTACLE
        return self.known[r][c]

    def observe(self, centre: Position, radius: int = 1) -> List[Position]:
        """Reveal cells within Chebyshev distance `radius`. Returns newly revealed positions."""
        newly: List[Position] = []
        cr, cc = centre
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                r, c = cr + dr, cc + dc
                if not (0 <= r < self.rows and 0 <= c < self.cols):
                    continue
                if self.known[r][c] != UNKNOWN:
                    continue
                true_type = self._env.get_cell_type((r, c))
                if true_type == OBSTACLE:
                    self.known[r][c] = KNOWN_OBSTACLE
                elif true_type == BASE:
                    self.known[r][c] = KNOWN_BASE
                    self.base_known = True
                elif true_type == COMM_ZONE:
                    self.known[r][c] = KNOWN_ZONE
                    if (r, c) not in self.known_zones:
                        self.known_zones.append((r, c))
                else:
                    self.known[r][c] = KNOWN_EMPTY
                self.explored_count += 1
                newly.append((r, c))

                # Reveal resource if present
                res = self._env.get_resource_at((r, c))
                if res and not res.discovered:
                    res.discovered = True
                    # store a reference so UI can read it
                    self.known_resources.append(res)
        return newly

    def coverage(self) -> float:
        total = self.rows * self.cols
        return (self.explored_count / total * 100.0) if total else 0.0

    def get_frontier(self) -> List[Position]:
        """Adjacent unknown cells that border known traversable cells."""
        frontier: List[Position] = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.known[r][c] != UNKNOWN:
                    continue
                # check if any neighbour is known traversable
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.is_traversable((nr, nc)):
                            frontier.append((r, c))
                            break
        return frontier
