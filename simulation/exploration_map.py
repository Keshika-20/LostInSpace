"""ExplorationMap: the rover's own notebook of what it has seen so far.

Each cell is UNKNOWN, FREE or OBSTACLE. It also remembers the resources and
communication-zone cells the rover has seen. Planning code must read ONLY this
map, never the true world.
"""

from simulation.environment import DIRECTIONS, FREE, OBSTACLE, Environment, Position

UNKNOWN = -1


class ExplorationMap:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self._cells = [[UNKNOWN for _ in range(cols)] for _ in range(rows)]
        self._resources = {}      # position -> Resource that was seen
        self._zone_cells = set()  # communication-zone cells that were seen

    # ---------- read-only questions ----------

    def in_bounds(self, pos: Position) -> bool:
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def cell_at(self, pos: Position) -> int:
        """UNKNOWN, FREE or OBSTACLE for a cell inside the map."""
        if not self.in_bounds(pos):
            raise ValueError("position is outside the map")
        return self._cells[pos[0]][pos[1]]

    def is_known(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self._cells[pos[0]][pos[1]] != UNKNOWN

    def is_known_free(self, pos: Position) -> bool:
        """True only if the rover has seen this cell AND it is free.

        Unknown cells count as not free, so A* never walks into the fog.
        """
        return self.in_bounds(pos) and self._cells[pos[0]][pos[1]] == FREE

    def is_known_obstacle(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self._cells[pos[0]][pos[1]] == OBSTACLE

    def explored_count(self) -> int:
        """How many cells the rover has seen (free or obstacle)."""
        return sum(cell != UNKNOWN for row in self._cells for cell in row)

    def known_free_count(self) -> int:
        return sum(cell == FREE for row in self._cells for cell in row)

    def coverage_percent(self, env: Environment) -> float:
        """Known free cells as a percentage of all free cells. For reports only,
        never for decisions, because it looks at the true world."""
        total_free = env.free_cell_count()
        if total_free == 0:
            return 0.0
        return 100.0 * self.known_free_count() / total_free

    def frontiers(self) -> list:
        """Known free cells that touch at least one unknown cell (row by row order)."""
        result = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self._cells[row][col] != FREE:
                    continue
                for d_row, d_col in DIRECTIONS:
                    nxt = (row + d_row, col + d_col)
                    if self.in_bounds(nxt) and self._cells[nxt[0]][nxt[1]] == UNKNOWN:
                        result.append((row, col))
                        break
        return result

    def known_resources(self) -> list:
        """Resources the rover has seen and that are not collected yet (sorted by position).

        Treat these as read-only; collecting goes through Environment.collect_resource.
        """
        return [resource for _, resource in sorted(self._resources.items())
                if not resource.collected]

    def is_known_zone(self, pos: Position) -> bool:
        return pos in self._zone_cells

    def known_zone_cells(self) -> list:
        """Communication-zone cells the rover has seen (sorted)."""
        return sorted(self._zone_cells)

    # ---------- updates ----------

    def observe(self, env: Environment, center: Position, radius: int = 2) -> int:
        """Copy the square of cells around center from the true world into this map.

        Terrain, resources and zone cells inside the square are all refreshed.
        Returns how many cells were newly discovered.
        """
        if radius < 0:
            raise ValueError("radius cannot be negative")
        if env.rows != self.rows or env.cols != self.cols:
            raise ValueError("environment and map sizes do not match")
        center_row, center_col = center
        uncollected = {resource.position: resource
                       for resource in env.resources if not resource.collected}
        newly_seen = 0
        for row in range(max(0, center_row - radius), min(self.rows - 1, center_row + radius) + 1):
            for col in range(max(0, center_col - radius), min(self.cols - 1, center_col + radius) + 1):
                pos = (row, col)
                if self._cells[row][col] == UNKNOWN:
                    newly_seen += 1
                # Always refresh, so a cell that changed since last time is updated too.
                self._cells[row][col] = env.grid[row][col]

                resource = uncollected.get(pos)
                if resource is not None:
                    resource.discovered = True
                    self._resources[pos] = resource
                else:
                    self._resources.pop(pos, None)

                if pos in env.zone_cells:
                    self._zone_cells.add(pos)
                else:
                    self._zone_cells.discard(pos)
        return newly_seen

    def mark_obstacle(self, pos: Position) -> None:
        """Record that this cell is blocked (the rover bumped into it)."""
        if self.in_bounds(pos):
            self._cells[pos[0]][pos[1]] = OBSTACLE