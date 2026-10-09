"""Environment: the true world the rover lives in.

Stage 3: seeded obstacle generation and a flood fill from the base.
Coordinates are (row, col), zero-based. Rows grow downward, columns grow rightward.
The rover must NOT read this grid to make decisions - it uses its own ExplorationMap.
"""

import random
from collections import deque

# Same alias as the shared models contract. Kept local so this file
# does not depend on Member 4's models.py being finished.
Position = tuple[int, int]

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
        # Every cell starts free until a layout is generated or loaded.
        self.grid = [[FREE for _ in range(cols)] for _ in range(rows)]

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