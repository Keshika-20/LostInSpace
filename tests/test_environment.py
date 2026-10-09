import pytest

from simulation.environment import Environment, OBSTACLE


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