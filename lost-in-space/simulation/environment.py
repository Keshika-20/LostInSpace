"""True world generation — obstacles, base, resources, communication zones.
The true world is separate from the rover's known map.
"""
from __future__ import annotations
import random
from typing import List, Optional, Set, Tuple
from .models import Position, Resource

# Cell types in true world
EMPTY = 0
OBSTACLE = 1
BASE = 2
COMM_ZONE = 3


class Environment:
    """Holds the true generated world. Rover never reads this directly for decisions."""

    def __init__(self, rows: int = 20, cols: int = 20, seed: Optional[int] = 42):
        self.rows = rows
        self.cols = cols
        self.seed = seed
        self.grid: List[List[int]] = []
        self.resources: List[Resource] = []
        self.base_pos: Position = (rows // 2, cols // 2)
        self.comm_zones: List[Position] = []
        self._rng = random.Random(seed)
        self._generate()

    def _generate(self) -> None:
        """Create a fixed but interesting planetary layout."""
        self.grid = [[EMPTY for _ in range(self.cols)] for _ in range(self.rows)]

        # Place base near centre
        br, bc = self.base_pos
        self.grid[br][bc] = BASE

        # Scatter some rock / crater obstacles (deterministic)
        num_obstacles = int(self.rows * self.cols * 0.12)
        placed = 0
        attempts = 0
        while placed < num_obstacles and attempts < num_obstacles * 10:
            r = self._rng.randint(0, self.rows - 1)
            c = self._rng.randint(0, self.cols - 1)
            if (r, c) != self.base_pos and self.grid[r][c] == EMPTY:
                # Prefer clusters for a more natural look
                self.grid[r][c] = OBSTACLE
                placed += 1
                # occasional neighbour
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.grid[nr][nc] == EMPTY and self._rng.random() < 0.35:
                            self.grid[nr][nc] = OBSTACLE
                            placed += 1
            attempts += 1

        # Communication zones (a few open cells)
        zone_candidates = [
            (2, 2), (2, self.cols - 3), (self.rows - 3, 2),
            (self.rows - 3, self.cols - 3), (br - 3, bc + 3)
        ]
        for pos in zone_candidates:
            r, c = pos
            if 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == EMPTY:
                self.grid[r][c] = COMM_ZONE
                self.comm_zones.append(pos)

        # Resources — scientifically interesting sites
        resource_specs = [
            ((3, 8), 85.0, 12.5),
            ((7, 15), 60.0, 8.0),
            ((14, 4), 95.0, 18.0),
            ((16, 12), 45.0, 6.5),
            ((5, 3), 70.0, 10.0),
            ((11, 17), 55.0, 7.0),
            ((18, 8), 80.0, 14.0),
        ]
        for (r, c), value, size in resource_specs:
            if 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == EMPTY:
                self.resources.append(Resource(position=(r, c), value=value, data_size=size))

    def is_inside(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_traversable_true(self, pos: Position) -> bool:
        """True world traversability (for movement validation only)."""
        if not self.is_inside(pos):
            return False
        r, c = pos
        return self.grid[r][c] != OBSTACLE

    def get_cell_type(self, pos: Position) -> int:
        if not self.is_inside(pos):
            return OBSTACLE
        r, c = pos
        return self.grid[r][c]

    def get_resource_at(self, pos: Position) -> Optional[Resource]:
        for res in self.resources:
            if res.position == pos:
                return res
        return None

    def block_cell(self, pos: Position) -> None:
        """Dynamic event: turn a cell into an obstacle (Stage 7 ready)."""
        if self.is_inside(pos) and pos != self.base_pos:
            r, c = pos
            self.grid[r][c] = OBSTACLE
