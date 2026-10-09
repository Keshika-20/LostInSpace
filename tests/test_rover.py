import pytest

from simulation.environment import Environment
from simulation.rover import Rover


def make_rover(start=(0, 0), energy=100.0):
    env = Environment(10, 10)
    env.load_test_layout()
    return Rover(env, start=start, energy=energy)


def test_legal_move_changes_position_and_energy():
    rover = make_rover()
    result = rover.move_to((0, 1))
    assert result.success
    assert result.reason == "ok"
    assert result.energy_spent == 1.0
    assert rover.position == (0, 1)
    assert rover.energy == 99.0


def test_out_of_bounds_move_rejected():
    rover = make_rover()
    result = rover.move_to((-1, 0))
    assert not result.success
    assert result.reason == "out_of_bounds"
    assert rover.position == (0, 0)
    assert rover.energy == 100.0


def test_obstacle_move_rejected():
    rover = make_rover(start=(3, 4))
    result = rover.move_to((3, 5))  # inside the wall
    assert not result.success
    assert result.reason == "blocked"
    assert rover.position == (3, 4)
    assert rover.energy == 100.0


def test_diagonal_move_rejected():
    rover = make_rover()
    result = rover.move_to((1, 1))
    assert not result.success
    assert result.reason == "not_adjacent"
    assert rover.position == (0, 0)
    assert rover.energy == 100.0


def test_two_cell_jump_rejected():
    rover = make_rover()
    result = rover.move_to((0, 2))
    assert not result.success
    assert result.reason == "not_adjacent"
    assert rover.energy == 100.0


def test_staying_in_place_rejected():
    rover = make_rover()
    result = rover.move_to((0, 0))
    assert not result.success
    assert result.reason == "not_adjacent"
    assert rover.energy == 100.0


def test_zero_energy_cannot_move():
    rover = make_rover(energy=0.0)
    result = rover.move_to((0, 1))
    assert not result.success
    assert result.reason == "insufficient_energy"
    assert rover.position == (0, 0)
    assert rover.energy == 0.0


def test_energy_never_goes_negative():
    rover = make_rover(energy=2.0)
    assert rover.move_to((0, 1)).success
    assert rover.move_to((0, 2)).success
    assert not rover.move_to((0, 3)).success
    assert rover.energy == 0.0


def test_reset_restores_start_and_energy():
    rover = make_rover()
    rover.move_to((0, 1))
    rover.move_to((0, 2))
    rover.reset()
    assert rover.position == (0, 0)
    assert rover.energy == 100.0


def test_start_on_obstacle_rejected():
    env = Environment(10, 10)
    env.load_test_layout()
    with pytest.raises(ValueError):
        Rover(env, start=(3, 5))


def test_test_layout_wall():
    env = Environment(10, 10)
    env.load_test_layout()
    assert not env.is_traversable((2, 5))
    assert not env.is_traversable((7, 5))
    assert env.is_traversable((1, 5))
    assert env.is_traversable((8, 5))