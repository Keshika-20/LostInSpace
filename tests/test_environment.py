import pytest

from simulation.environment import FREE, OBSTACLE, Environment
from simulation.exploration_map import UNKNOWN, ExplorationMap


# ---------- Stage 1: basic grid ----------

def test_dimensions_stored():
    env = Environment(10, 12)
    assert env.rows == 10
    assert env.cols == 12
    assert len(env.grid) == 10
    assert len(env.grid[0]) == 12


def test_in_bounds():
    env = Environment(10, 10)
    assert env.in_bounds((0, 0))
    assert env.in_bounds((9, 9))
    assert not env.in_bounds((-1, 0))
    assert not env.in_bounds((10, 0))
    assert not env.in_bounds((0, 10))


def test_is_traversable():
    env = Environment(5, 5)
    assert env.is_traversable((2, 2))
    env.grid[2][2] = OBSTACLE
    assert not env.is_traversable((2, 2))
    assert not env.is_traversable((9, 9))  # out of bounds


def test_invalid_size_rejected():
    with pytest.raises(ValueError):
        Environment(0, 5)


# ---------- Stage 3: generation ----------

def test_base_out_of_bounds_rejected():
    with pytest.raises(ValueError):
        Environment(5, 5, base=(5, 0))


def test_invalid_obstacle_rate_rejected():
    env = Environment(5, 5)
    with pytest.raises(ValueError):
        env.generate_obstacles(seed=1, obstacle_rate=1.5)


def test_same_seed_same_world():
    first = Environment(15, 15)
    second = Environment(15, 15)
    first.generate_obstacles(seed=7)
    second.generate_obstacles(seed=7)
    assert first.grid == second.grid


def test_different_seed_different_world():
    first = Environment(20, 20)
    second = Environment(20, 20)
    first.generate_obstacles(seed=1)
    second.generate_obstacles(seed=2)
    assert first.grid != second.grid


def test_base_always_free():
    env = Environment(10, 10)
    env.generate_obstacles(seed=3, obstacle_rate=1.0)
    assert env.grid[0][0] == FREE
    assert env.free_cell_count() == 1


def test_no_unreachable_pockets():
    for seed in range(10):
        env = Environment(12, 12)
        env.generate_obstacles(seed=seed, obstacle_rate=0.35)
        reachable = env.reachable_cells(env.base)
        assert env.free_cell_count() == len(reachable)


# ---------- Stage 3: observation ----------

def test_observe_reveals_square_around_center():
    env = Environment(10, 10)
    known = ExplorationMap(10, 10)
    newly_seen = known.observe(env, (5, 5), radius=2)
    assert newly_seen == 25
    assert known.is_known((3, 3))
    assert known.is_known((7, 7))
    assert not known.is_known((2, 5))
    assert not known.is_known((5, 8))


def test_observe_clipped_at_corner():
    env = Environment(10, 10)
    known = ExplorationMap(10, 10)
    assert known.observe(env, (0, 0), radius=2) == 9


def test_observe_twice_reveals_nothing_new():
    env = Environment(10, 10)
    known = ExplorationMap(10, 10)
    known.observe(env, (4, 4), radius=2)
    assert known.observe(env, (4, 4), radius=2) == 0


def test_hidden_obstacle_revealed_only_in_range():
    env = Environment(10, 10)
    env.grid[5][7] = OBSTACLE   # within radius 2 of (5, 5)
    env.grid[5][9] = OBSTACLE   # too far away
    known = ExplorationMap(10, 10)
    known.observe(env, (5, 5), radius=2)
    assert known.cell_at((5, 7)) == OBSTACLE
    assert known.is_known_obstacle((5, 7))
    assert known.cell_at((5, 9)) == UNKNOWN
    assert not known.is_known((5, 9))


def test_negative_radius_rejected():
    env = Environment(5, 5)
    known = ExplorationMap(5, 5)
    with pytest.raises(ValueError):
        known.observe(env, (2, 2), radius=-1)


def test_coverage_percent():
    env = Environment(4, 4)
    known = ExplorationMap(4, 4)
    known.observe(env, (0, 0), radius=1)  # reveals a 2x2 block = 4 of 16 cells
    assert known.coverage_percent(env) == 25.0


def test_frontiers():
    env = Environment(5, 5)
    known = ExplorationMap(5, 5)
    known.observe(env, (0, 0), radius=1)  # known block: (0,0) (0,1) (1,0) (1,1)
    assert known.frontiers() == [(0, 1), (1, 0), (1, 1)]


def test_mark_obstacle():
    known = ExplorationMap(5, 5)
    assert not known.is_known((2, 2))
    known.mark_obstacle((2, 2))
    assert known.is_known_obstacle((2, 2))
    assert not known.is_known_free((2, 2))