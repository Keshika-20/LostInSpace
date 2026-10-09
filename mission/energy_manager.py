
from simulation.pathfinding import route_to_nearest, route_cost


def calculate_return_energy(rover):
    """
    Calculate the energy needed to reach a known
    communication zone.

    Return None if no reachable zone is known.
    """

    current_position = rover.position
    known_map = rover.known_map

    known_zones = known_map.known_zone_cells()

    if not known_zones:
        return None

    route = route_to_nearest(
        current_position,
        known_zones,
        known_map
    )

    if route is None:
        return None

    required_energy = route_cost(
        route,
        rover.move_cost
    )

    return required_energy

def should_return(rover, safety_margin=1.0):
    """
    Decide whether the rover should return to a
    known communication zone.

    The safety margin reserves extra energy.
    """

    return_energy = calculate_return_energy(rover)

    # No known safe route: do not continue exploring.
    if return_energy is None:
        return True

    required_energy = return_energy + safety_margin

    # Return before energy becomes too low.
    if rover.energy <= required_energy:
        return True

    return False
