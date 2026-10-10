"""Autonomous Mission Controller for Lost in Space.

Executes autonomous multi-phase mission:
1. EXPLORING & SCANNING for high-value data
2. COLLECTING science resources
3. NAVIGATING to Communication Zone
4. UPLOADING transmitted data
5. RETURNING safely to Starting Point (0,0)
6. EVALUATING Mission Success/Failure
"""

from enum import Enum
from simulation.pathfinding import find_path


class MissionState(Enum):
    IDLE = "IDLE"
    EXPLORING = "EXPLORING HIGH-VALUE"
    NAVIGATING_COMM_ZONE = "NAVIGATING TO COMM ZONE"
    UPLOADING = "UPLOADING DATA"
    RETURNING_TO_BASE = "RETURNING TO BASE"
    SUCCESS = "MISSION SUCCESS"
    FAILURE = "MISSION FAILURE"


def get_data_type(value: float) -> str:
    if value >= 70:
        return "Gold Ore (Rare Isotope)"
    elif value >= 50:
        return "Copper Deposit (Hydrated)"
    elif value >= 30:
        return "Titanium Ore (Basalt)"
    else:
        return "Lithium Core (Regolith)"


class AutonomousMissionController:
    """Automates rover exploration, data collection, comm zone transmission, and safe return."""

    def __init__(self, application_controller):
        self.app = application_controller
        self.state = MissionState.IDLE
        self.current_target = None
        self.planned_path = []
        self.session_data_collected = 0.0
        self.session_data_uploaded = 0.0
        self.useful_cells = set()
        self.logs = []

    def log(self, message):
        self.logs.append(message)
        if len(self.logs) > 6:
            self.logs.pop(0)

    def start_mission(self):
        """Reset mission state for active autonomous run."""
        self.state = MissionState.EXPLORING
        self.current_target = None
        self.planned_path = []
        self.session_data_collected = 0.0
        self.session_data_uploaded = 0.0
        self.log("Autonomous Mission Launched!")

    def step(self):
        """Execute one autonomous turn tick."""
        rover = self.app.rover
        env = self.app.environment

        if rover.energy <= 0:
            self.state = MissionState.FAILURE
            self.log("CRITICAL: Out of energy!")
            return False

        if self.state in (MissionState.IDLE, MissionState.SUCCESS, MissionState.FAILURE):
            return False

        # Check energy reservation required to return to base
        dist_to_base = abs(rover.position[0] - env.base[0]) + abs(rover.position[1] - env.base[1])
        energy_safety_margin = dist_to_base * rover.move_cost + 5.0

        # State 1: EXPLORING & COLLECTING
        if self.state == MissionState.EXPLORING:
            # Auto-collect resource under rover if standing on one
            res_here = env.resource_at(rover.position)
            if res_here and res_here.discovered and not res_here.collected:
                if rover.can_carry(res_here.data_size):
                    res_col = self.app.collect_resource()
                    if res_col.success:
                        self.session_data_collected += res_here.value
                        self.useful_cells.add(rover.position)
                        data_type = get_data_type(res_here.value)
                        self.log(f"IDENTIFIED: {data_type} ({res_here.value:.0f} MB)")

            # Decide if we need to switch to Comm Zone upload
            has_cargo = rover.carried_data > 0
            low_energy_for_explore = rover.energy <= energy_safety_margin + 15.0
            all_known_collected = not any(
                r for r in rover.known_map.known_resources() if not r.collected
            )

            if has_cargo and (low_energy_for_explore or all_known_collected or rover.carried_data >= rover.capacity * 0.8):
                self.state = MissionState.NAVIGATING_COMM_ZONE
                self.current_target = None
                self.planned_path = []
                self.log("Cargo loaded -> Head to Comm Zone")
                return True

            # Target Selection: Prioritize high-value undiscovered/uncollected resources
            if not self.current_target or self.current_target == rover.position or not self.planned_path:
                known_res = rover.known_map.known_resources()
                uncollected = [r for r in known_res if not r.collected]

                if uncollected:
                    # Sort by scientific value / distance ratio
                    uncollected.sort(
                        key=lambda r: r.value / max(1, abs(r.position[0] - rover.position[0]) + abs(r.position[1] - rover.position[1])),
                        reverse=True,
                    )
                    best_res = uncollected[0]
                    target_candidate = best_res.position
                else:
                    # Frontier exploration
                    frontiers = rover.known_map.frontiers()
                    if frontiers:
                        frontiers.sort(
                            key=lambda f: abs(f[0] - rover.position[0]) + abs(f[1] - rover.position[1])
                        )
                        target_candidate = frontiers[0]
                    else:
                        target_candidate = env.base

                # Pre-calculate roundtrip energy needed for this candidate target
                dist_tgt = abs(target_candidate[0] - rover.position[0]) + abs(target_candidate[1] - rover.position[1])
                dist_cz = min(abs(target_candidate[0] - z[0]) + abs(target_candidate[1] - z[1]) for z in env.zone_cells) if env.zone_cells else 0
                dist_base = abs(target_candidate[0] - env.base[0]) + abs(target_candidate[1] - env.base[1])
                energy_needed = (dist_tgt + dist_cz + dist_base) * rover.move_cost + 4.0

                if rover.energy < energy_needed and rover.carried_data > 0:
                    self.log(f"⚠️ PRE-CALC: Power low to reach target ({rover.energy:.0f} < {energy_needed:.0f}). Head to Comm Zone!")
                    self.state = MissionState.NAVIGATING_COMM_ZONE
                    self.current_target = None
                    self.planned_path = []
                    return True

                self.current_target = target_candidate
                self.planned_path = find_path(rover.position, self.current_target, rover.known_map) or []

            # Execute step along planned path
            return self._follow_path()

        # State 2: NAVIGATING TO COMM ZONE
        elif self.state == MissionState.NAVIGATING_COMM_ZONE:
            if rover.at_comm_zone():
                self.state = MissionState.UPLOADING
                self.log("Arrived at Comm Zone -> Transmitting...")
                return True

            # Find nearest known comm zone cell
            known_zones = rover.known_map.known_zone_cells()
            if not known_zones:
                # If not seen yet, explore towards unvisited area
                frontiers = rover.known_map.frontiers()
                if frontiers:
                    target_zone = frontiers[0]
                else:
                    target_zone = env.base
            else:
                known_zones.sort(
                    key=lambda z: abs(z[0] - rover.position[0]) + abs(z[1] - rover.position[1])
                )
                target_zone = known_zones[0]

            self.current_target = target_zone
            self.planned_path = find_path(rover.position, self.current_target, rover.known_map) or []
            return self._follow_path()

        # State 3: UPLOADING DATA
        elif self.state == MissionState.UPLOADING:
            uploaded_amount = rover.unload()
            self.session_data_uploaded += uploaded_amount
            rover.uploaded_data += uploaded_amount
            if hasattr(self.app, "record_region_yield"):
                self.app.record_region_yield(uploaded_amount)
            self.log(f"SUCCESS: Uploaded {uploaded_amount:.1f} MB Data!")
            self.state = MissionState.RETURNING_TO_BASE
            self.current_target = env.base
            self.planned_path = find_path(rover.position, env.base, rover.known_map) or []
            return True

        # State 4: RETURNING TO BASE
        elif self.state == MissionState.RETURNING_TO_BASE:
            if rover.position == env.base:
                if self.session_data_uploaded > 0 or self.session_data_collected > 0:
                    self.state = MissionState.SUCCESS
                    self.log("MISSION ACCOMPLISHED: Returned to Base!")
                else:
                    self.state = MissionState.SUCCESS
                    self.log("Returned to Base safely.")
                return True

            self.current_target = env.base
            self.planned_path = find_path(rover.position, env.base, rover.known_map) or []
            return self._follow_path()

        return False

    def _follow_path(self):
        rover = self.app.rover
        if not self.planned_path or len(self.planned_path) < 2:
            return False

        next_pos = self.planned_path[1]
        res = self.app.handle_command("MOVE", next_pos)
        
        if res.success:
            self.planned_path.pop(0)
            return True
        else:
            # Replan on obstacle/blocked cell
            self.log("Obstacle encountered -> Replanning path...")
            self.planned_path = find_path(rover.position, self.current_target, rover.known_map) or []
            return False
