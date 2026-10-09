
from simulation.pathfinding import find_path
from mission.target_selector import choose_target


class MissionController:
    def __init__(self, environment, rover, known_map):
        self.environment = environment
        self.rover = rover
        self.known_map = known_map

        self.route = []
        self.target = None
        self.events = [
            "LANDER LINK ESTABLISHED",
            "AUTONOMOUS SYSTEMS ONLINE"
        ]
        self.last_event = "Systems nominal"

    def step(self):
        state = self.rover.state

        # Continuously scan nearby terrain
        self.known_map.observe(
            self.environment,
            state.position,
            radius=5
        )

        # Choose another target when necessary
        if self.target is None or self.target.collected:
            self.target = choose_target(
                list(self.known_map.resources.values()),
                state.position,
                state.energy
            )

        if self.target is None:
            self.route = []
            self.last_event = "SEARCHING FOR SCIENTIFIC DATA"
            return {"ok": True, "event": self.last_event}

        # Plan a route through known safe cells
        path = find_path(
            state.position,
            self.target.position,
            self.known_map
        )

        if not path:
            self.last_event = "TARGET UNREACHABLE; RESELECTING"
            self.events.append(self.last_event)
            self.target = None
            self.route = []
            return {"ok": True, "event": self.last_event}

        self.route = path

        # Move autonomously along the calculated route
        if len(path) > 1:
            destination = path[1]
            ok, message = self.rover.move_to(destination)

            if not ok:
                self.last_event = f"REPLANNING: {message}"
                self.target = None
                return {"ok": True, "event": self.last_event}

        # Scan the new position after movement
        self.known_map.observe(
            self.environment,
            state.position,
            radius=5
        )

        # Automatically collect data at the target
        if state.position == self.target.position:
            if not self.target.collected:
                self.target.collected = True
                state.carried_data += self.target.data_size

                self.last_event = (
                    f"DATA RECOVERED +{self.target.data_size:.1f} MB"
                )
                self.events.append(self.last_event)

            self.target = None
            self.route = []

        else:
            self.last_event = (
                f"NAVIGATING TO {self.target.name}"
            )

        return {"ok": True, "event": self.last_event}