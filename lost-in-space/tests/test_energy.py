"""Stage 2 energy & movement tests."""
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.rover import Rover, MOVE_COST


def test_successful_move_cost():
    env = Environment(rows=10, cols=10, seed=1)
    exp = ExplorationMap(env)
    rover = Rover(env, exp, start=(5, 5))
    start_energy = rover.state.energy
    ok, _ = rover.move((5, 6))
    assert ok
    assert rover.state.energy == start_energy - MOVE_COST
    assert rover.state.position == (5, 6)


def test_illegal_move_no_change():
    env = Environment(rows=10, cols=10, seed=1)
    exp = ExplorationMap(env)
    rover = Rover(env, exp, start=(0, 0))
    energy = rover.state.energy
    # diagonal illegal
    ok, _ = rover.move((1, 1))
    assert not ok
    assert rover.state.position == (0, 0)
    assert rover.state.energy == energy


def test_no_negative_energy():
    env = Environment(rows=10, cols=10, seed=1)
    exp = ExplorationMap(env)
    rover = Rover(env, exp, start=(5, 5))
    rover.state.energy = 0.5
    ok, _ = rover.move((5, 6))
    assert not ok
    assert rover.state.energy == 0.5
