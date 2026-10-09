import math

from simulation.environment import OBSTACLE, Environment
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import find_path, manhattan, route_cost, route_is_valid


def fully_known(env):
    """A map where the rover has seen the whole grid (makes path tests simple)."""
    known = ExplorationMap(env.rows, env.cols)
    known.observe(env, (0, 0), radius=max(env.rows, env.cols))
    return known


def test_direct_path_in_open_grid():
    env = Environment(5, 5)
    known = fully_known(env)
    path = find_path((0, 0), (0, 4), known)
    assert path[0] == (0, 0)
    assert path[-1] == (0, 4)
    assert len(path) == 5
    assert route_is_valid(path, known)


def test_detour_around_the_wall():
    env = Environment(10, 10)
    env.load_test_layout()          # wall in column 5, rows 2-7
    known = fully_known(env)
    path = find_path((4, 4), (4, 6), known)
    assert path is not None
    assert len(path) - 1 == 8       # 3 up, 2 across, 3 down
    assert route_is_valid(path, known)
    assert all(env.is_traversable(cell) for cell in path)


def test_start_equals_goal():
    env = Environment(5, 5)
    known = fully_known(env)
    assert find_path((2, 2), (2, 2), known) == [(2, 2)]


def test_blocked_goal_returns_none():
    env = Environment(5, 5)
    env.grid[3][3] = OBSTACLE
    known = fully_known(env)
    assert find_path((0, 0), (3, 3), known) is None


def test_unreachable_goal_returns_none():
    env = Environment(5, 5)
    for row in range(5):
        env.grid[row][2] = OBSTACLE   # a full wall splits the grid in two
    known = fully_known(env)
    assert find_path((0, 0), (0, 4), known) is None


def test_unknown_goal_returns_none():
    env = Environment(5, 5)
    known = ExplorationMap(5, 5)
    known.observe(env, (0, 0), radius=1)
    assert find_path((0, 0), (4, 4), known) is None   # goal not seen yet


def test_start_not_known_free_returns_none():
    env = Environment(5, 5)
    known = ExplorationMap(5, 5)   # nothing seen at all
    assert find_path((0, 0), (0, 1), known) is None


def test_replan_after_a_cell_becomes_known_blocked():
    env = Environment(5, 5)
    known = fully_known(env)
    old_route = find_path((0, 0), (0, 2), known)
    assert old_route == [(0, 0), (0, 1), (0, 2)]

    known.mark_obstacle((0, 1))
    assert not route_is_valid(old_route, known)

    new_route = find_path((0, 0), (0, 2), known)
    assert new_route is not None
    assert (0, 1) not in new_route
    assert len(new_route) - 1 == 4
    assert route_is_valid(new_route, known)


def test_same_input_gives_same_route():
    env = Environment(10, 10)
    env.generate_obstacles(seed=5, obstacle_rate=0.2)
    known = fully_known(env)
    first = find_path((0, 0), (9, 9), known)
    second = find_path((0, 0), (9, 9), known)
    assert first == second


def test_route_cost():
    assert route_cost([(0, 0), (0, 1), (0, 2)]) == 2.0
    assert route_cost([(0, 0), (0, 1), (0, 2)], move_cost=1.5) == 3.0
    assert route_cost([(0, 0)]) == 0.0


def test_route_cost_without_route_is_infinite():
    assert route_cost(None) == math.inf
    assert route_cost([]) == math.inf


def test_route_is_valid_rejects_jumps():
    env = Environment(5, 5)
    known = fully_known(env)
    assert not route_is_valid([(0, 0), (0, 2)], known)
    assert not route_is_valid(None, known)
    assert manhattan((0, 0), (3, 4)) == 7