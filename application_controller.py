"""Application-level commands backed by the real simulation state."""

from copy import deepcopy

from simulation.environment import Environment
from simulation.models import Position
from simulation.rover import MoveResult, Rover


class ApplicationController:
    """Own the environment and rover used by the application."""

    def __init__(
        self,
        rows: int = 10,
        cols: int = 10,
        base: Position = (0, 0),
        energy: float = 100.0,
        vision_radius: int = 2,
        capacity: float = 10.0,
        environment: Environment | None = None,
    ):
        self.environment = (
            environment
            if environment is not None
            else Environment(rows=rows, cols=cols, base=base)
        )
        self.rover = Rover(
            self.environment,
            start=self.environment.base,
            energy=energy,
            vision_radius=vision_radius,
            capacity=capacity,
        )
        self._initial_environment = deepcopy(self.environment)
        self._initial_rover_config = {
            "start": self.rover.start,
            "energy": self.rover.initial_energy,
            "move_cost": self.rover.move_cost,
            "vision_radius": self.rover.vision_radius,
            "capacity": self.rover.capacity,
        }
        self.is_running = False

    def handle_command(
        self,
        command: str,
        destination: Position | None = None,
    ) -> MoveResult | None:
        """Handle START, PAUSE, RESET, and MOVE commands."""
        if command == "MOVE":
            if destination is None:
                raise ValueError("MOVE requires a destination")
            return self.rover.move_to(destination)

        if destination is not None:
            raise ValueError("destination is only valid for MOVE")
        if command == "START":
            self.is_running = True
        elif command == "PAUSE":
            self.is_running = False
        elif command == "RESET":
            self.environment = deepcopy(self._initial_environment)
            self.rover = Rover(self.environment, **self._initial_rover_config)
            self.is_running = False
        else:
            raise ValueError(f"unsupported command: {command}")
        return None
