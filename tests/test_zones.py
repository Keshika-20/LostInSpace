from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import route_is_valid, route_to_nearest
from simulation.rover import Rover


def fully_known(env):
    known = ExplorationMap(env.rows, env.cols)
    known.observe(env, (0, 0), radius=max(env.rows, env.cols))
    return known


def test_place_comm_zones_creates_free_reachable_cells():
    env = Environment(12, 12)
    env.generate_obstacles(seed=3, obstacle_rate=0.2)
    env.place_comm_zones(count=2, seed=5)
    reachable = env.reachable_cells(env.base)
    assert len(env.zone_cells) > 0
    for cell in env.zone_cells:
        assert env.is_traversable(cell)
        assert cell in reachable
        assert cell != env.base


def test_same_seed_same_zones():
    first, second = Environment(12, 12), Environment(12, 12)
    first.place_comm_zones(count=2, seed=8)
    second.place_comm_zones(count=2, seed=8)
    assert first.zone_cells == second.zone_cells


def test_in_comm_zone():
    env = Environment(10, 10)
    env.zone_cells = {(4, 4), (4, 5)}
    assert env.in_comm_zone((4, 4))
    assert not env.in_comm_zone((0, 0))
    assert not env.in_comm_zone((-1, -1))


def test_zone_hidden_until_observed():
    env = Environment(10, 10)
    env.zone_cells = {(6, 6)}
    known = ExplorationMap(10, 10)
    known.observe(env, (0, 0), radius=2)
    assert known.known_zone_cells() == []
    known.observe(env, (5, 5), radius=2)
    assert known.known_zone_cells() == [(6, 6)]
    assert known.is_known_zone((6, 6))


def test_rover_knows_when_it_is_in_a_zone():
    env = Environment(10, 10)
    env.zone_cells = {(0, 1)}
    rover = Rover(env)
    assert not rover.at_comm_zone()
    rover.move_to((0, 1))
    assert rover.at_comm_zone()


def test_route_to_nearest_picks_the_cheapest_goal():
    env = Environment(5, 5)
    known = fully_known(env)
    route = route_to_nearest((0, 0), [(0, 3), (2, 0)], known)
    assert route[-1] == (2, 0)
    assert len(route) - 1 == 2
    assert route_is_valid(route, known)


def test_route_to_nearest_when_already_there():
    env = Environment(5, 5)
    known = fully_known(env)
    assert route_to_nearest((1, 1), [(1, 1), (4, 4)], known) == [(1, 1)]


def test_route_to_nearest_without_goals():
    env = Environment(5, 5)
    known = fully_known(env)
    assert route_to_nearest((0, 0), [], known) is None


def test_route_to_nearest_unreachable():
    env = Environment(5, 5)
    for row in range(5):
        env.grid[row][2] = 1   # a full wall
    known = fully_known(env)
    assert route_to_nearest((0, 0), [(0, 4)], known) is None


def test_route_to_nearest_ignores_unseen_goals():
    env = Environment(5, 5)
    known = ExplorationMap(5, 5)
    known.observe(env, (0, 0), radius=1)
    assert route_to_nearest((0, 0), [(4, 4)], known) is None