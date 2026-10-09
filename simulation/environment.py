"""Environment: the true world the rover lives in.

Stage 3: seeded obstacles and a flood fill from the base.
Stage 5: science resources.
Stage 6: communication zones.
Stage 7: blocking and unblocking cells while a mission runs.
Coordinates are (row, col), zero-based. Rows grow downward, columns grow rightward.
The rover must NOT read this world to make decisions - it uses its own ExplorationMap.
"""

import random
from collections import deque

from simulation.models import Position, Resource

# Terrain codes for the true grid.
FREE = 0
OBSTACLE = 1

# Up, down, left, right. A fixed order keeps every search repeatable.
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Environment:
    def __init__(self, rows: int = 10, cols: int = 10, base: Position = (0, 0)):
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        self.rows = rows
        self.cols = cols
        if not self.in_bounds(base):
            raise ValueError("base must be inside the grid")
        self.base = base
        self.seed = None
        self.grid = [[FREE for _ in range(cols)] for _ in range(rows)]
        self.resources = []        # Resource objects (Stage 5)
        self.zone_cells = set()    # cells inside a communication zone (Stage 6)

    # ---------- basic questions ----------

    def in_bounds(self, pos: Position) -> bool:
        """True if (row, col) lies inside the grid."""
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_traversable(self, pos: Position) -> bool:
        """True if the rover may stand on this cell (inside the grid and not an obstacle)."""
        return self.in_bounds(pos) and self.grid[pos[0]][pos[1]] != OBSTACLE

    def free_cell_count(self) -> int:
        """How many cells are not obstacles (used for the coverage percentage)."""
        return sum(cell == FREE for row in self.grid for cell in row)

    def reachable_cells(self, start: Position) -> set:
        """Flood fill (BFS): every free cell that can be walked to from start."""
        if not self.is_traversable(start):
            return set()
        seen = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for d_row, d_col in DIRECTIONS:
                nxt = (row + d_row, col + d_col)
                if nxt not in seen and self.is_traversable(nxt):
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    # ---------- Stage 3: terrain ----------

    def generate_obstacles(self, seed=None, obstacle_rate: float = 0.2) -> None:
        """Fill the grid with random obstacles. The same seed gives the same world.

        The base cell is always free. Any free cell the base cannot reach
        is turned into an obstacle, so no sealed-off pockets exist.
        """
        if not 0.0 <= obstacle_rate <= 1.0:
            raise ValueError("obstacle_rate must be between 0 and 1")
        rng = random.Random(seed)
        self.seed = seed
        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) == self.base:
                    self.grid[row][col] = FREE
                elif rng.random() < obstacle_rate:
                    self.grid[row][col] = OBSTACLE
                else:
                    self.grid[row][col] = FREE
        self._seal_unreachable_pockets()

    def _seal_unreachable_pockets(self) -> None:
        reachable = self.reachable_cells(self.base)
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == FREE and (row, col) not in reachable:
                    self.grid[row][col] = OBSTACLE

    def load_test_layout(self) -> None:
        """Fixed layout for testing: a vertical wall in column 5, rows 2 to 7.

        The gaps at rows 0-1 and rows 8-9 let a path go around the wall.
        Needs a grid with at least 8 rows and 6 columns (the default 10x10 works).
        """
        if self.rows < 8 or self.cols < 6:
            raise ValueError("test layout needs at least 8 rows and 6 columns")
        for row in range(2, 8):
            self.grid[row][5] = OBSTACLE

    # ---------- Stage 5: resources ----------

    def place_resources(self, count: int, seed=None,
                        value_range=(10, 100), size_range=(1, 5)) -> None:
        """Scatter science resources on free cells the base can reach.

        Each resource gets its own scientific value and its own data size (MB).
        The same seed gives the same resources.
        """
        if count < 0:
            raise ValueError("count cannot be negative")
        rng = random.Random(seed)
        reachable = self.reachable_cells(self.base)
        taken = {resource.position for resource in self.resources}
        candidates = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if (row, col) in reachable and (row, col) != self.base and (row, col) not in taken
        ]
        if count > len(candidates):
            raise ValueError("not enough free cells for that many resources")
        for pos in rng.sample(candidates, count):
            value = float(rng.randint(*value_range))
            data_size = float(rng.randint(*size_range))
            self.resources.append(Resource(position=pos, value=value, data_size=data_size))

    def resource_at(self, pos: Position):
        """The uncollected resource on this cell, or None."""
        for resource in self.resources:
            if resource.position == pos and not resource.collected:
                return resource
        return None

    def collect_resource(self, pos: Position):
        """Mark the resource on this cell as collected and return it.

        Returns None if there is nothing to collect, so a second call on the
        same cell can never hand out the same data twice.
        """
        resource = self.resource_at(pos)
        if resource is None:
            return None
        resource.collected = True
        return resource

    def reset_resources(self) -> None:
        """Make every resource uncollected and undiscovered again."""
        for resource in self.resources:
            resource.discovered = False
            resource.collected = False

    # ---------- Stage 6: communication zones ----------

    def place_comm_zones(self, count: int = 2, size_range=(3, 5), seed=None) -> None:
        """Create large communication zones, each a square patch of free cells.

        A zone is centred on a random reachable free cell. Side length is random
        within size_range. Obstacle cells and the base are not part of a zone.
        """
        if count < 0:
            raise ValueError("count cannot be negative")
        rng = random.Random(seed)
        reachable = self.reachable_cells(self.base)
        centres = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if (row, col) in reachable and (row, col) != self.base
        ]
        if count > 0 and not centres:
            raise ValueError("no free cells available for a communication zone")
        for _ in range(count):
            centre = rng.choice(centres)
            size = rng.randint(*size_range)
            top = centre[0] - size // 2
            left = centre[1] - size // 2
            for row in range(max(0, top), min(self.rows, top + size)):
                for col in range(max(0, left), min(self.cols, left + size)):
                    if self.grid[row][col] == FREE and (row, col) != self.base:
                        self.zone_cells.add((row, col))

    def in_comm_zone(self, pos: Position) -> bool:
        """True if this cell is inside a communication zone."""
        return pos in self.zone_cells

    # ---------- Stage 7: dynamic events ----------

    def block_cell(self, pos: Position, rover_pos=None) -> bool:
        """Turn a free cell into an obstacle while the mission runs.

        Returns True if it was blocked. It refuses (and changes nothing) when:
        the cell is outside the grid or already blocked, it is the base, the
        rover is standing on it, an uncollected resource lies on it, or blocking
        it would cut the rover off from the base or cut the base off from every
        communication zone.
        """
        if not self.in_bounds(pos) or self.grid[pos[0]][pos[1]] != FREE:
            return False
        if pos == self.base or pos == rover_pos or self.resource_at(pos) is not None:
            return False

        had_zones = bool(self.zone_cells)
        was_zone_cell = pos in self.zone_cells

        # Try it, then check the world is still connected.
        self.grid[pos[0]][pos[1]] = OBSTACLE
        self.zone_cells.discard(pos)
        reachable = self.reachable_cells(self.base)

        rover_cut_off = rover_pos is not None and rover_pos not in reachable
        zones_cut_off = had_zones and not (self.zone_cells & reachable)
        if rover_cut_off or zones_cut_off:
            self.grid[pos[0]][pos[1]] = FREE
            if was_zone_cell:
                self.zone_cells.add(pos)
            return False
        return True

    def unblock_cell(self, pos: Position) -> bool:
        """Clear an obstacle. Returns True if a blocked cell was freed."""
        if not self.in_bounds(pos) or self.grid[pos[0]][pos[1]] != OBSTACLE:
            return False
        self.grid[pos[0]][pos[1]] = FREE
        return True

    def random_block_event(self, rng, rover_pos=None, candidates=None):
        """Block one random cell and return it, or None if nothing could be blocked.

        rng is a random.Random owned by the caller, so a mission seed makes the
        events repeatable. candidates limits which cells may be chosen (for
        example only cells the rover already knows); default is every free cell.
        """
        if candidates is not None:
            pool = sorted(candidates)
        else:
            pool = [(row, col) for row in range(self.rows) for col in range(self.cols)
                    if self.grid[row][col] == FREE]
        rng.shuffle(pool)
        for pos in pool[:20]:
            if self.block_cell(pos, rover_pos):
                return pos
        return None