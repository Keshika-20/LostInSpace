
class TargetSelector:
    """Selects unexplored places using the known map."""

    def select_target(self, known_map, current_position):
        x, y = current_position

        # Check right, left, down, and up.
        neighbours = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        # Select a neighbouring cell not yet explored.
        for nx, ny in neighbours:
            if (nx, ny) not in known_map:
                return (nx, ny)

        # All neighbouring cells are already known.
        return None
