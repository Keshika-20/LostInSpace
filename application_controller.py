"""Application-level commands backed by the real simulation state and 3D autonomous missions."""

from copy import deepcopy
from dataclasses import dataclass

from mission.autonomous_mission import AutonomousMissionController, MissionState
from simulation.environment import Environment
from simulation.models import Position, Resource
from simulation.pathfinding import find_path
from simulation.rover import MoveResult, Rover


REGION_NAMES = [
    "Region 1: Ares Planitia",
    "Region 2: Chryse Basin",
    "Region 3: Elysium Mons",
    "Region 4: Valles Marineris",
    "Region 5: Olympus Plateau",
]


@dataclass(frozen=True)
class CollectionResult:
    """Outcome of loading a discovered resource into the rover."""

    success: bool
    reason: str
    resource: Resource | None = None


class ApplicationController:
    """Own the environment, rover, autonomous mission, and session history."""

    def __init__(
        self,
        rows: int = 14,
        cols: int = 14,
        base: Position = (0, 0),
        energy: float = 100.0,
        vision_radius: int = 2,
        capacity: float = 10.0,
        environment: Environment | None = None,
        seed: int | None = None,
        resource_count: int = 18,
    ):
        self.seed = seed if seed is not None else 2025
        self.resource_count = resource_count
        self.region_index = 0
        self.environment = (
            environment
            if environment is not None
            else Environment(rows=rows, cols=cols, base=base)
        )
        if environment is None and seed is not None:
            self.environment.generate_obstacles(seed=seed, obstacle_rate=0.15)
            self.environment.place_resources(count=self.resource_count, seed=seed + 1)
            self.environment.place_comm_zones(count=3, size_range=(1, 1), seed=seed + 2)

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

        self.autonomous_mission = AutonomousMissionController(self)
        self.is_running = False
        self.planned_route: list[Position] = []
        self.planned_target: Position | None = None

        # Session & Region tracking
        self.session_count = 1
        self.successful_sessions = 0
        self.failed_sessions = 0
        self.session_history = []
        self.useful_regions_count = 0
        self.region_yields = {}

    @property
    def region_name(self):
        return REGION_NAMES[self.region_index % len(REGION_NAMES)]

    def record_region_yield(self, amount: float):
        curr = self.region_yields.get(self.region_name, 0.0)
        self.region_yields[self.region_name] = curr + amount

    @property
    def most_resourceful_region(self):
        if not self.region_yields:
            return (self.region_name, 0.0)
        return max(self.region_yields.items(), key=lambda x: x[1])

    def start_autonomous_mission(self):
        """Trigger autonomous mission flow."""
        self.is_running = True
        self.autonomous_mission.start_mission()

    def update_tick(self):
        """Advance autonomous simulation by one frame/step if running."""
        if not self.is_running:
            return

        if self.autonomous_mission.state in (MissionState.SUCCESS, MissionState.FAILURE):
            self.is_running = False
            # Record session completion stats
            is_success = self.autonomous_mission.state == MissionState.SUCCESS
            if is_success:
                self.successful_sessions += 1
                if self.autonomous_mission.session_data_uploaded > 0:
                    self.useful_regions_count += 1
            else:
                self.failed_sessions += 1

            self.session_history.append({
                "session": self.session_count,
                "region": self.region_name,
                "status": self.autonomous_mission.state.value,
                "uploaded_mb": self.autonomous_mission.session_data_uploaded,
                "energy_left": self.rover.energy,
            })
            return

        self.autonomous_mission.step()
        self.planned_route = self.autonomous_mission.planned_path
        self.planned_target = self.autonomous_mission.current_target

    def explore_next_region(self):
        """Preserve previously explored planet tiles and energy reserve; transition to the next region."""
        self.region_index += 1
        self.session_count += 1

        # Keep existing explored cells in rover map and current energy level
        existing_map = deepcopy(self.rover.known_map)
        current_energy = self.rover.energy

        # Generate fresh environment for new region
        new_seed = self.seed + self.region_index * 10
        self.environment = Environment(
            rows=self.environment.rows,
            cols=self.environment.cols,
            base=self.environment.base,
        )
        self.environment.generate_obstacles(seed=new_seed, obstacle_rate=0.15)
        self.environment.place_resources(count=self.resource_count, seed=new_seed + 1)
        self.environment.place_comm_zones(count=3, size_range=(1, 1), seed=new_seed + 2)

        # Re-initialize rover with preserved map and preserved energy (no 100 energy refill)
        self.rover.env = self.environment
        self.rover.position = self.environment.base
        self.rover.energy = current_energy
        self.rover.carried_data = 0.0
        self.rover.known_map = existing_map
        self.rover.observe()

        # Reset mission controller state for new region
        self.autonomous_mission = AutonomousMissionController(self)
        self.is_running = False
        self.planned_route = []
        self.planned_target = None

    def collect_resource(self) -> CollectionResult:
        """Load the resource under the rover into cargo."""
        if not self.is_running:
            return CollectionResult(False, "paused")
        resource = self.environment.resource_at(self.rover.position)
        if resource is None:
            return CollectionResult(False, "no_resource")
        if not self.rover.can_carry(resource.data_size):
            return CollectionResult(False, "cargo_capacity")
        if not self.rover.load(resource.data_size):
            return CollectionResult(False, "cargo_capacity")

        collected = self.environment.collect_resource(self.rover.position)
        if collected is None:
            self.rover.carried_data -= resource.data_size
            return CollectionResult(False, "disappeared")

        self.rover.observe()
        return CollectionResult(True, "ok", collected)

    def plan_nearest_resource_route(self) -> list[Position] | None:
        """Preview shortest known safe path to nearest discovered resource."""
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

    def handle_command(self, command: str, destination: Position | None = None):
        """Execute lifecycle and navigation commands."""
        if command == "MOVE":
            if destination is None:
                raise ValueError("MOVE requires a destination")
            res = self.rover.move_to(destination)
            if res.success and self.planned_target is not None:
                route = find_path(
                    self.rover.position,
                    self.planned_target,
                    self.rover.known_map,
                )
                self.planned_route = route or []
            return res

        if command == "COLLECT":
            return self.collect_resource()

        if command == "PLAN_ROUTE":
            return self.plan_nearest_resource_route()

        if command == "START":
            self.start_autonomous_mission()
        elif command == "PAUSE":
            self.is_running = False
        elif command == "EXPLORE_NEXT":
            self.explore_next_region()
        elif command == "RESET":
            self.environment = deepcopy(self._initial_environment)
            self.rover = Rover(self.environment, **self._initial_rover_config)
            self.autonomous_mission = AutonomousMissionController(self)
            self.is_running = False
            self.planned_route = []
            self.planned_target = None

        return None
