"""Environment: the true world the rover lives in.

Stage 1: stores grid dimensions and a placeholder grid only.
Coordinates are (row, col), zero-based. Rows grow downward, columns grow rightward.
"""

# Same alias as the shared models contract. Kept local so this file
# does not depend on Member 4's models.py being finished.
Position = tuple[int, int]

# Terrain codes for the true grid.
FREE = 0
OBSTACLE = 1


class Environment:
    def __init__(self, rows: int = 10, cols: int = 10):
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        self.rows = rows
        self.cols = cols
        # Placeholder grid: every cell is free. Real terrain comes in Stage 3.
        self.grid = [[FREE for _ in range(cols)] for _ in range(rows)]

    def in_bounds(self, pos: Position) -> bool:
        """True if (row, col) lies inside the grid."""
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_traversable(self, pos: Position) -> bool:
        """True if the rover may stand on this cell (inside the grid and not an obstacle)."""
        return self.in_bounds(pos) and self.grid[pos[0]][pos[1]] != OBSTACLE