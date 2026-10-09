from simulation.environment import Environment
from simulation.exploration_map import UNKNOWN
from simulation.pathfinding import find_path, route_cost
from simulation.rover import Rover


def see_everything(rover):
    rover.known_map.observe(
        rover.env, rover.position, radius=max(rover.env.rows, rover.env.cols)
    )


def test_walking_a_route_spends_exactly_its_cost():
    env = Environment(6, 6)
    rover = Rover(env, energy=50.0, move_cost=1.0)
    see_everything(rover)
    route = find_path(rover.position, (5, 5), rover.known_map)
    for cell in route[1:]:
        assert rover.move_to(cell).success
    assert rover.position == (5, 5)
    assert rover.energy_used() == route_cost(route, rover.move_cost)
    assert rover.moves == len(route) - 1


def test_cost_scales_with_move_cost():
    env = Environment(6, 6)
    rover = Rover(env, energy=100.0, move_cost=2.0)
    see_everything(rover)
    route = find_path(rover.position, (5, 5), rover.known_map)
    for cell in route[1:]:
        assert rover.move_to(cell).success
    assert route_cost(route, 2.0) == 20.0
    assert rover.energy_used() == 20.0


def test_only_successful_moves_are_counted():
    rover = Rover(Environment(5, 5))
    rover.move_to((1, 1))      # diagonal, rejected
    rover.move_to((0, 1))      # fine
    assert rover.moves == 1
    assert rover.energy_used() == 1.0


def test_reset_clears_the_counters():
    rover = Rover(Environment(5, 5))
    rover.move_to((0, 1))
    rover.reset()
    assert rover.moves == 0
    assert rover.energy_used() == 0.0


def test_explored_count_matches_a_manual_count():
    env = Environment(8, 8)
    env.generate_obstacles(seed=2, obstacle_rate=0.2)
    rover = Rover(env)
    manual = sum(
        1 for row in range(8) for col in range(8)
        if rover.known_map.cell_at((row, col)) != UNKNOWN
    )
    assert rover.known_map.explored_count() == manual


def test_full_view_gives_full_coverage():
    env = Environment(8, 8)
    env.generate_obstacles(seed=6, obstacle_rate=0.2)
    rover = Rover(env)
    see_everything(rover)
    assert rover.known_map.coverage_percent(env) == 100.0