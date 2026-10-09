"""Stage 4 A* tests."""
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap, KNOWN_EMPTY, KNOWN_OBSTACLE
from simulation.pathfinding import find_path, is_route_valid, estimate_route_energy


def _open_map(rows=8, cols=8):
    env = Environment(rows=rows, cols=cols, seed=1)
    exp = ExplorationMap(env)
    # force-reveal entire map as empty for unit tests
    for r in range(rows):
        for c in range(cols):
            exp.known[r][c] = KNOWN_EMPTY
    return exp


def test_direct_path():
    exp = _open_map()
    path = find_path((0, 0), (0, 3), exp)
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (0, 3)
    assert is_route_valid(path, exp)


def test_start_equals_goal():
    exp = _open_map()
    path = find_path((2, 2), (2, 2), exp)
    assert path == [(2, 2)]


def test_blocked_goal():
    exp = _open_map()
    exp.known[3][3] = KNOWN_OBSTACLE
    path = find_path((0, 0), (3, 3), exp)
    assert path is None


def test_detour():
    exp = _open_map()
    # wall
    for c in range(0, 5):
        exp.known[2][c] = KNOWN_OBSTACLE
    path = find_path((0, 0), (4, 0), exp)
    assert path is not None
    assert is_route_valid(path, exp)
    # must go around
    assert any(p[0] != 2 or p[1] >= 5 for p in path)


def test_energy_estimate():
    exp = _open_map()
    path = find_path((0, 0), (0, 4), exp)
    assert estimate_route_energy(path) == 4.0
