"""Stage 5 collection tests."""
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.rover import Rover
from mission.mission_controller import MissionController


def test_collect_once():
    env = Environment(rows=20, cols=20, seed=42)
    exp = ExplorationMap(env)
    # pick first resource and teleport rover there
    res = env.resources[0]
    res.discovered = True
    exp.known_resources.append(res)
    rover = Rover(env, exp, start=res.position)
    ok, msg, size = rover.try_collect()
    assert ok
    assert size == res.data_size
    assert rover.state.carried_data == res.data_size
    # second attempt fails
    ok2, _, _ = rover.try_collect()
    assert not ok2
    assert rover.state.carried_data == res.data_size


def test_hidden_resource_not_collected():
    env = Environment(rows=20, cols=20, seed=42)
    exp = ExplorationMap(env)
    res = env.resources[0]
    # Force undiscovered even if observe already ran near base
    res.discovered = False
    rover = Rover(env, exp, start=env.base_pos)
    rover.state.position = res.position
    ok, msg, _ = rover.try_collect()
    assert not ok
    assert msg == "not_discovered"
