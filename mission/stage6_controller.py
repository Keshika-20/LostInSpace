
from simulation.pathfinding import route_to_nearest, route_cost, route_is_valid


class Stage6Controller:
    """Plan routes to known communication zones and upload carried data."""

    def __init__(self, rover):
        self.rover = rover
        self.path = []

    def step(self):
        """Choose the next movement or upload action."""

        # 1. Stop if the rover has no energy.
        if self.rover.energy <= 0:
            return {"type": "WAIT"}

        # 2. Upload data when inside a communication zone.
        if self.rover.at_comm_zone():
            if self.rover.carried_data > 0:
                self.rover.uploaded_data += self.rover.unload()
                self.path = []
                return {"type": "WAIT"}

            # No data to upload.
            return {"type": "WAIT"}

        # 3. Find communication zones discovered by the rover.
        known_zones = self.rover.known_map.known_zone_cells()

        if not known_zones:
            return {"type": "WAIT"}

        # 4. Find a route using only the known map.
        current = self.rover.position

        route = route_to_nearest(
            current,
            known_zones,
            self.rover.known_map
        )

        if route is None or not route_is_valid(
            route, self.rover.known_map
        ):
            self.path = []
            return {"type": "WAIT"}

        # 5. Make sure the rover has enough energy for the route.
        required_energy = route_cost(route, self.rover.move_cost)

        if required_energy > self.rover.energy:
            self.path = []
            return {"type": "WAIT"}

        self.path = route

        # 6. Move one cell along the route.
        if len(route) < 2:
            return {"type": "WAIT"}

        next_position = route[1]

        return {
            "type": "MOVE",
            "dx": next_position[0] - current[0],
            "dy": next_position[1] - current[1]
        }
