
from mission.energy_manager import should_return
from mission.stage6_controller import Stage6Controller


class Stage8Controller:
    """Coordinate exploration, safe return, and communication uploads."""

    def __init__(self, rover, exploration_controller):
        self.rover = rover
        self.exploration_controller = exploration_controller
        self.return_controller = Stage6Controller(rover)
        self.returning = False

    def step(self):
        """Choose whether to explore or return to a communication zone."""

        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        # Once returning, keep returning until the mission reaches a zone.
        if self.returning:
            action = self.return_controller.step()

            if self.rover.at_comm_zone():
                self.returning = False

            return action

        # Check energy before taking another exploration step.
        if should_return(self.rover):
            self.returning = True
            return self.return_controller.step()

        # Continue the existing exploration strategy.
        return self.exploration_controller.explore_step()
