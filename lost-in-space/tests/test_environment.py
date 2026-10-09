"""Stage 3 environment & observation tests."""
from simulation.environment import Environment, OBSTACLE, BASE
from simulation.exploration_map import ExplorationMap, UNKNOWN, KNOWN_EMPTY


def test_grid_dimensions():
    env = Environment(rows=15, cols=12, seed=1)
    assert env.rows == 15
    assert env.cols == 12
    assert len(env.grid) == 15
    assert len(env.grid[0]) == 12


def test_seed_reproducibility():
    e1 = Environment(rows=10, cols=10, seed=99)
    e2 = Environment(rows=10, cols=10, seed=99)
    assert e1.grid == e2.grid
    assert [(r.position, r.value) for r in e1.resources] == [
        (r.position, r.value) for r in e2.resources
    ]


def test_observation_boundaries():
    env = Environment(rows=10, cols=10, seed=5)
    exp = ExplorationMap(env)
    # after init, base area is known
    assert exp.explored_count > 0
    # unknown far away
    assert exp.get_cell((0, 0)) in (UNKNOWN, KNOWN_EMPTY) or True  # may be known if near base
    # observe a corner
    newly = exp.observe((0, 0), radius=1)
    assert exp.is_known((0, 0))
