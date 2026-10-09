
import random
from simulation.models import Resource


class Environment:
    """Procedurally generated planetary surface."""

    def __init__(self, rows=48, cols=48, seed=17):
        self.rows = rows
        self.cols = cols
        self.seed = seed

        rng = random.Random(seed)
        self.base = (rows // 2, cols // 2)

        # 0 = traversable terrain, 1 = rock
        self.grid = [
            [0 for _ in range(cols)]
            for _ in range(rows)
        ]

        # Dense rocky terrain with a safe landing zone
        for r in range(rows):
            for c in range(cols):
                distance = math_distance(
                    (r, c), self.base
                )

                if distance > 4 and rng.random() < 0.16:
                    self.grid[r][c] = 1

        # Scientific samples distributed across the terrain
        self.resources = []
        used = {self.base}

        for i in range(36):
            for _ in range(500):
                position = (
                    rng.randrange(rows),
                    rng.randrange(cols)
                )
                r, c = position

                distance = (
                    abs(r - self.base[0])
                    + abs(c - self.base[1])
                )

                if (
                    position not in used
                    and self.grid[r][c] == 0
                    and distance > 5
                ):
                    used.add(position)

                    self.resources.append(
                        Resource(
                            position=position,
                            value=round(
                                rng.uniform(30, 100), 1
                            ),
                            data_size=round(
                                rng.uniform(5, 25), 1
                            ),
                            name=f"DATA-{i + 1:03d}"
                        )
                    )
                    break

        self.communication_zones = {
            self.base,
            (self.base[0] + 1, self.base[1]),
            (self.base[0], self.base[1] + 1)
        }

    def in_bounds(self, position):
        r, c = position
        return 0 <= r < self.rows and 0 <= c < self.cols

    def traversable(self, position):
        r, c = position
        return (
            self.in_bounds(position)
            and self.grid[r][c] == 0
        )


def math_distance(a, b):
    return (
        (a[0] - b[0]) ** 2
        + (a[1] - b[1]) ** 2
    ) ** 0.5