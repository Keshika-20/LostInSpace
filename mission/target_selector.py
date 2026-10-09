
class TargetSelector:
    """Selects useful unexplored locations for the rover."""

    def select_target(
        self,
        known_map,
        current_position,
        blocked=None,
        goal=None
    ):
        if blocked is None:
            blocked = set()

        x, y = current_position

        neighbours = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        candidates = []

        for position in neighbours:
            if position in known_map:
                continue

            if position in blocked:
                continue

            candidates.append(position)

        if not candidates:
            return None

        # Prefer the candidate closest to the goal.
        if goal is not None:
            candidates.sort(
                key=lambda position:
                    abs(position[0] - goal[0])
                    + abs(position[1] - goal[1])
            )

        return candidates[0]
