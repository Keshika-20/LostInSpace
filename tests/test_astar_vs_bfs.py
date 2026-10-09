import random

from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import find_path, route_is_valid, route_to_nearest


def test_astar_matches_bfs_on_random_worlds():
    for seed in range(20):
        env = Environment(12, 12)
        env.generate_obstacles(seed=seed, obstacle_rate=0.25)
        known = ExplorationMap(12, 12)
        known.observe(env, (0, 0), radius=12)
        free = sorted(env.reachable_cells(env.base))
        rng = random.Random(seed)
        for _ in range(10):
            start = rng.choice(free)
            goal = rng.choice(free)
            astar = find_path(start, goal, known)
            bfs = route_to_nearest(start, [goal], known)
            assert astar is not None
            assert bfs is not None
            assert len(astar) == len(bfs)
            assert route_is_valid(astar, known)