import pytest

from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.models import Resource
from simulation.rover import Rover


def make_env():
    env = Environment(10, 10)
    env.generate_obstacles(seed=4, obstacle_rate=0.15)
    return env


def test_place_resources_count_and_cells():
    env = make_env()
    env.place_resources(5, seed=1)
    positions = [resource.position for resource in env.resources]
    reachable = env.reachable_cells(env.base)
    assert len(env.resources) == 5
    assert len(set(positions)) == 5
    assert env.base not in positions
    assert all(pos in reachable for pos in positions)


def test_resource_values_and_sizes_in_range():
    env = make_env()
    env.place_resources(6, seed=2, value_range=(10, 100), size_range=(1, 5))
    for resource in env.resources:
        assert 10 <= resource.value <= 100
        assert 1 <= resource.data_size <= 5
        assert not resource.discovered
        assert not resource.collected


def test_same_seed_same_resources():
    first, second = make_env(), make_env()
    first.place_resources(5, seed=9)
    second.place_resources(5, seed=9)
    assert first.resources == second.resources


def test_too_many_resources_rejected():
    env = Environment(3, 3)
    with pytest.raises(ValueError):
        env.place_resources(20, seed=1)


def test_resource_hidden_until_observed():
    env = Environment(10, 10)
    resource = Resource(position=(5, 5), value=50.0, data_size=2.0)
    env.resources.append(resource)
    known = ExplorationMap(10, 10)
    known.observe(env, (0, 0), radius=2)
    assert known.known_resources() == []
    assert not resource.discovered
    known.observe(env, (4, 4), radius=2)
    assert known.known_resources() == [resource]
    assert resource.discovered


def test_collect_resource_only_once():
    env = Environment(10, 10)
    resource = Resource(position=(2, 2), value=40.0, data_size=3.0)
    env.resources.append(resource)
    assert env.resource_at((2, 2)) is resource
    assert env.collect_resource((2, 2)) is resource
    assert resource.collected
    assert env.collect_resource((2, 2)) is None
    assert env.resource_at((2, 2)) is None


def test_collected_resource_leaves_the_known_list():
    env = Environment(10, 10)
    resource = Resource(position=(2, 2), value=40.0, data_size=3.0)
    env.resources.append(resource)
    known = ExplorationMap(10, 10)
    known.observe(env, (2, 2), radius=1)
    assert known.known_resources() == [resource]
    env.collect_resource((2, 2))
    assert known.known_resources() == []
    known.observe(env, (2, 2), radius=1)
    assert known.known_resources() == []


def test_rover_sees_a_nearby_resource_at_start():
    env = Environment(10, 10)
    env.resources.append(Resource(position=(0, 2), value=30.0, data_size=1.0))
    rover = Rover(env)
    assert len(rover.known_map.known_resources()) == 1


def test_reset_resources():
    env = Environment(5, 5)
    resource = Resource(position=(1, 1), value=10.0, data_size=1.0)
    resource.discovered = True
    resource.collected = True
    env.resources.append(resource)
    env.reset_resources()
    assert not resource.discovered
    assert not resource.collected


def test_capacity_rules():
    env = Environment(5, 5)
    rover = Rover(env, capacity=10.0)
    assert rover.load(6.0)
    assert not rover.load(5.0)          # 11 MB would not fit
    assert rover.carried_data == 6.0
    assert rover.load(4.0)
    assert rover.carried_data == 10.0
    assert rover.unload() == 10.0
    assert rover.carried_data == 0.0


def test_negative_load_rejected():
    rover = Rover(Environment(5, 5))
    with pytest.raises(ValueError):
        rover.load(-1.0)


def test_rover_reset_clears_cargo_and_resources():
    env = Environment(10, 10)
    resource = Resource(position=(0, 1), value=20.0, data_size=2.0)
    env.resources.append(resource)
    rover = Rover(env)
    env.collect_resource((0, 1))
    rover.load(2.0)
    rover.reset()
    assert rover.carried_data == 0.0
    assert not resource.collected