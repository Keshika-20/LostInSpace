import random

from simulation.environment import Environment, OBSTACLE
from simulation.rover import Rover

# Mix of legal steps and illegal ones (diagonal, stay put, two cells).
MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (0, 0), (0, 2))


def test_random_moves_never_break_a_rule():
    for seed in range(10):
        env = Environment(10, 10)
        env.generate_obstacles(seed=seed, obstacle_rate=0.25)
        rover = Rover(env, energy=60.0)
        rng = random.Random(seed)
        for _ in range(300):
            row, col = rover.position
            d_row, d_col = rng.choice(MOVES)
            position_before = rover.position
            energy_before = rover.energy
            result = rover.move_to((row + d_row, col + d_col))

            assert env.is_traversable(rover.position)
            assert rover.energy >= 0
            if not result.success:
                assert rover.position == position_before
                assert rover.energy == energy_before

        assert rover.energy_used() == rover.moves * rover.move_cost


def test_known_map_never_contradicts_the_world():
    for seed in range(10):
        env = Environment(10, 10)
        env.generate_obstacles(seed=seed, obstacle_rate=0.25)
        rover = Rover(env, energy=200.0)
        rng = random.Random(seed)
        for _ in range(200):
            row, col = rover.position
            d_row, d_col = rng.choice(MOVES)
            rover.move_to((row + d_row, col + d_col))
        for r in range(env.rows):
            for c in range(env.cols):
                if rover.known_map.is_known_free((r, c)):
                    assert env.grid[r][c] != OBSTACLE
                if rover.known_map.is_known_obstacle((r, c)):
                    assert env.grid[r][c] == OBSTACLE