import random

from simulation.environment import Environment
from simulation.models import Resource
from simulation.pathfinding import find_path, route_is_valid
from simulation.rover import Rover


def test_block_cell_blocks_a_free_cell():
    env = Environment(5, 5)
    assert env.block_cell((2, 2))
    assert not env.is_traversable((2, 2))


def test_block_cell_refuses_protected_cells():
    env = Environment(5, 5)
    env.resources.append(Resource(position=(3, 3), value=10.0, data_size=1.0))
    assert not env.block_cell(env.base)
    assert not env.block_cell((1, 1), rover_pos=(1, 1))
    assert not env.block_cell((3, 3))
    assert not env.block_cell((9, 9))
    assert env.is_traversable(env.base)
    assert env.is_traversable((1, 1))
    assert env.is_traversable((3, 3))


def test_block_cell_refuses_an_already_blocked_cell():
    env = Environment(5, 5)
    assert env.block_cell((2, 2))
    assert not env.block_cell((2, 2))


def test_block_cell_refuses_to_cut_the_rover_off():
    env = Environment(1, 5)
    assert not env.block_cell((0, 2), rover_pos=(0, 4))
    assert env.is_traversable((0, 2))


def test_block_cell_refuses_to_cut_every_zone():
    env = Environment(1, 5)
    env.zone_cells = {(0, 4)}
    assert not env.block_cell((0, 2))
    assert env.is_traversable((0, 2))
    assert env.zone_cells == {(0, 4)}


def test_block_cell_refuses_to_remove_the_only_zone_cell():
    env = Environment(1, 5)
    env.zone_cells = {(0, 2)}
    assert not env.block_cell((0, 2))
    assert env.is_traversable((0, 2))
    assert env.zone_cells == {(0, 2)}


def test_unblock_cell():
    env = Environment(5, 5)
    env.block_cell((2, 2))
    assert env.unblock_cell((2, 2))
    assert env.is_traversable((2, 2))
    assert not env.unblock_cell((2, 2))   # already free
    assert not env.unblock_cell((9, 9))   # outside the grid


def test_random_block_event_is_repeatable():
    first, second = Environment(10, 10), Environment(10, 10)
    cell_a = first.random_block_event(random.Random(1), rover_pos=(0, 0))
    cell_b = second.random_block_event(random.Random(1), rover_pos=(0, 0))
    assert cell_a is not None
    assert cell_a == cell_b
    assert first.grid == second.grid
    assert not first.is_traversable(cell_a)


def test_random_block_event_with_no_candidates():
    env = Environment(5, 5)
    assert env.random_block_event(random.Random(1), candidates=[]) is None


def test_stale_route_becomes_invalid_when_the_rover_looks_again():
    env = Environment(10, 10)
    rover = Rover(env)                       # at (0, 0), sees columns 0 to 2
    old_route = find_path((0, 0), (0, 2), rover.known_map)
    assert old_route == [(0, 0), (0, 1), (0, 2)]

    assert env.block_cell((0, 2), rover_pos=rover.position)
    # The world changed, but the rover has not looked yet: its notebook is stale.
    assert route_is_valid(old_route, rover.known_map)

    assert rover.move_to((0, 1)).success     # moving makes it look again
    assert not route_is_valid(old_route, rover.known_map)

    new_route = find_path((0, 1), (0, 3), rover.known_map)
    assert new_route is not None
    assert (0, 2) not in new_route
    assert len(new_route) - 1 == 4
    assert route_is_valid(new_route, rover.known_map)


def test_rover_refuses_to_step_into_a_newly_blocked_cell():
    env = Environment(10, 10)
    rover = Rover(env, vision_radius=0)      # sees only its own cell
    assert rover.move_to((0, 1)).success
    assert env.block_cell((0, 2), rover_pos=rover.position)
    energy_before = rover.energy
    result = rover.move_to((0, 2))
    assert not result.success
    assert result.reason == "blocked"
    assert rover.position == (0, 1)
    assert rover.energy == energy_before
    assert rover.known_map.is_known_obstacle((0, 2))