"""Application-level commands backed by the real simulation state."""

from copy import deepcopy
from dataclasses import dataclass

from simulation.environment import Environment
from simulation.models import Position, Resource
from simulation.pathfinding import find_path
from simulation.rover import MoveResult, Rover


@dataclass(frozen=True)
class CollectionResult:
    """Outcome of loading a discovered resource into the rover."""

    success: bool
    reason: str
    resource: Resource | None = None


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
        self.planned_route: list[Position] = []
        self.planned_target: Position | None = None

    def collect_resource(self) -> CollectionResult:
        """Load the resource under the rover if it is known and fits in cargo."""
        if not self.is_running:
            return CollectionResult(False, "paused")
        resource = self.environment.resource_at(self.rover.position)
        if resource is None:
            return CollectionResult(False, "no_resource")
        if resource not in self.rover.known_map.known_resources():
            return CollectionResult(False, "resource_not_discovered")
        if not self.rover.can_carry(resource.data_size):
            return CollectionResult(False, "cargo_capacity")
        if not self.rover.load(resource.data_size):
            return CollectionResult(False, "cargo_capacity")

        collected = self.environment.collect_resource(self.rover.position)
        if collected is None:
            self.rover.carried_data -= resource.data_size
            raise RuntimeError("resource disappeared while the rover was collecting it")
        self.rover.observe()
        if self.planned_target == collected.position:
            self.planned_route = []
            self.planned_target = None
        return CollectionResult(True, "ok", collected)

    def plan_nearest_resource_route(self) -> list[Position] | None:
        """Preview the shortest known-safe route to the nearest discovered resource."""
        candidates = []
        for resource in self.rover.known_map.known_resources():
            route = find_path(
                self.rover.position,
                resource.position,
                self.rover.known_map,
            )
            if route is not None:
                candidates.append((len(route), resource.position, route))

        if not candidates:
            self.planned_route = []
            self.planned_target = None
            return None

        _, self.planned_target, self.planned_route = min(candidates)
        return self.planned_route.copy()

    def handle_command(
        self,
        command: str,
        destination: Position | None = None,
    ) -> MoveResult | CollectionResult | list[Position] | None:
        """Handle lifecycle, movement, resource collection, and route commands."""
        if command == "MOVE":
            if destination is None:
                raise ValueError("MOVE requires a destination")
            result = self.rover.move_to(destination)
            if result.success and self.planned_target is not None:
                route = find_path(
                    self.rover.position,
                    self.planned_target,
                    self.rover.known_map,
                )
                self.planned_route = route or []
            return result

        if command == "COLLECT":
            if destination is not None:
                raise ValueError("destination is not valid for COLLECT")
            return self.collect_resource()

        if command == "PLAN_ROUTE":
            if destination is not None:
                raise ValueError("destination is not valid for PLAN_ROUTE")
            return self.plan_nearest_resource_route()

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
            self.planned_route = []
            self.planned_target = None
        else:
            raise ValueError(f"unsupported command: {command}")
        return None
