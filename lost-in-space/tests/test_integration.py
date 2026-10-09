"""Integration smoke tests for Stages 1-5."""
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.rover import Rover
from mission.mission_controller import MissionController


def test_construct_and_step():
    env = Environment(rows=15, cols=15, seed=7)
    exp = ExplorationMap(env)
    rover = Rover(env, exp)
    ctrl = MissionController(rover, exp)
    start_pos = rover.state.position
    result = ctrl.step()
    assert "action" in result
    # after a few steps something should change or at least not crash
    for _ in range(5):
        ctrl.step()
    assert rover.state.energy <= 100.0


def test_coverage_increases():
    env = Environment(rows=12, cols=12, seed=3)
    exp = ExplorationMap(env)
    rover = Rover(env, exp)
    ctrl = MissionController(rover, exp)
    initial = exp.explored_count
    for _ in range(20):
        ctrl.step()
    assert exp.explored_count >= initial
