"""Environment: the true world the rover lives in.

Stage 2: adds a fixed test layout with obstacles.
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
        # Every cell starts free. Random terrain comes in Stage 3.
        self.grid = [[FREE for _ in range(cols)] for _ in range(rows)]

    def in_bounds(self, pos: Position) -> bool:
        """True if (row, col) lies inside the grid."""
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_traversable(self, pos: Position) -> bool:
        """True if the rover may stand on this cell (inside the grid and not an obstacle)."""
        return self.in_bounds(pos) and self.grid[pos[0]][pos[1]] != OBSTACLE

    def load_test_layout(self) -> None:
        """Fixed layout for Stage 2 testing: a vertical wall in column 5, rows 2 to 7.

        The gaps at rows 0-1 and rows 8-9 let a later A* path go around the wall.
        Needs a grid with at least 8 rows and 6 columns (the default 10x10 works).
        """
        if self.rows < 8 or self.cols < 6:
            raise ValueError("test layout needs at least 8 rows and 6 columns")
        for row in range(2, 8):
            self.grid[row][5] = OBSTACLE