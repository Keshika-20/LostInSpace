
from simulation.pathfinding import route_to_nearest, route_cost


def calculate_return_energy(rover):
    """Calculate energy needed to reach a known communication zone."""

    known_map = rover.known_map
    known_zones = known_map.known_zone_cells()

    if not known_zones:
        return None

    route = route_to_nearest(
        rover.position,
        known_zones,
        known_map
    )

    if route is None:
        return None

    return route_cost(route, rover.move_cost)


def should_return(rover, safety_margin=1.0):
    """Decide whether the rover should return to a communication zone."""

    return_energy = calculate_return_energy(rover)

    # Without a known route, the rover should not keep exploring.
    if return_energy is None:
        return True

    required_energy = return_energy + safety_margin

    # Keep enough energy for the return trip and a safety margin.
    return rover.energy <= required_energy
