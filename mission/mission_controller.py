
from mission.pathfinder import Pathfinder


class MissionController:
    """Controls the rover's mission decisions."""

    def __init__(self, rover, environment, target=(5, 5)):
        self.rover = rover
        self.environment = environment
        self.target = target

        self.pathfinder = Pathfinder()
        self.path = []
        self.blocked = set()

    def step(self):
        # Stop if the rover has no energy.
        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        current = (self.rover.x, self.rover.y)

        # If the rover reaches the target, stop.
        if current == self.target:
            self.path = []
            return {"type": "WAIT"}

        # Replan if there is no path or the rover's position
        # no longer matches the first cell in the path.
        if not self.path or self.path[0] != current:
            self.path = self.pathfinder.find_path(
                current, self.target, self.blocked
            )

        # No route exists.
        if self.path is None:
            return {"type": "WAIT"}

        # Replan if the next cell is blocked.
        if len(self.path) < 2 or self.path[1] in self.blocked:
            self.path = self.pathfinder.find_path(
                current, self.target, self.blocked
            )

        # No usable route exists.
        if self.path is None or len(self.path) < 2:
            return {"type": "WAIT"}

        # Follow the next step of the route.
        next_x, next_y = self.path[1]

        return {
            "type": "MOVE",
            "dx": next_x - current[0],
            "dy": next_y - current[1]
        }
