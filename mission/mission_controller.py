
class MissionController:
    """Controls the rover's mission decisions."""

    def __init__(self, rover, environment, target=(5, 5)):
        self.rover = rover
        self.environment = environment
        self.target = target

    def step(self):
        # If energy is empty, do not move.
        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        # Get the rover's current position.
        x = self.rover.x
        y = self.rover.y

        # Get the target position.
        target_x, target_y = self.target

        # Move horizontally first.
        if x < target_x:
            return {"type": "MOVE", "dx": 1, "dy": 0}

        elif x > target_x:
            return {"type": "MOVE", "dx": -1, "dy": 0}

        # Then move vertically.
        elif y < target_y:
            return {"type": "MOVE", "dx": 0, "dy": 1}

        elif y > target_y:
            return {"type": "MOVE", "dx": 0, "dy": -1}

        # The rover has reached its target.
        else:
            return {"type": "WAIT"}
