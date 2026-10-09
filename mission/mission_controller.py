
from mission.pathfinder import Pathfinder
from mission.target_selector import TargetSelector


class MissionController:
    """Controls the rover's mission decisions."""

    def __init__(self, rover, environment, target=(5, 5)):
        self.rover = rover
        self.environment = environment
        self.target = target

        self.pathfinder = Pathfinder()
        self.target_selector = TargetSelector()

        self.path = []
        self.blocked = set()
        self.known_map = {(rover.x, rover.y)}

    def _move_toward_target(self, current):
        """Find a path and return the next movement action."""
        if not self.path or self.path[0] != current:
            self.path = self.pathfinder.find_path(
                current,
                self.target,
                self.blocked
            )

        if self.path is None:
            return {"type": "WAIT"}

        if len(self.path) < 2 or self.path[1] in self.blocked:
            self.path = self.pathfinder.find_path(
                current,
                self.target,
                self.blocked
            )

        if self.path is None or len(self.path) < 2:
            return {"type": "WAIT"}

        next_x, next_y = self.path[1]

        return {
            "type": "MOVE",
            "dx": next_x - current[0],
            "dy": next_y - current[1]
        }

    def step(self):
        """Perform one step toward the current mission target."""

        # Stop if the rover has no energy.
        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        current = (self.rover.x, self.rover.y)
        self.known_map.add(current)

        # Preserve the original behavior when the target is reached.
        if current == self.target:
            self.path = []
            return {"type": "WAIT"}

        # If the target is blocked, try selecting an unexplored target.
        if self.target in self.blocked:
            new_target = self.target_selector.select_target(
                self.known_map,
                current,
                self.blocked,
                goal=(5, 5)
            )

            if new_target is None:
                return {"type": "WAIT"}

            self.target = new_target
            self.path = []

        return self._move_toward_target(current)

    def explore_step(self):
        """Select an unexplored neighbour and move toward it."""

        # Stop if the rover has no energy.
        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        current = (self.rover.x, self.rover.y)

        # Record the current position as explored.
        self.known_map.add(current)

        # Select a new unexplored, unblocked neighbouring cell.
        new_target = self.target_selector.select_target(
            self.known_map,
            current,
            self.blocked,
            goal=(5, 5)
        )

        if new_target is None:
            return {"type": "WAIT"}

        # Update the target and calculate a route.
        self.target = new_target
        self.path = []

        return self._move_toward_target(current)
