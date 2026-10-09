"""Stage 8 — optional batch runs with fixed seeds."""
from __future__ import annotations
from typing import List, Dict, Any
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.rover import Rover
from mission.mission_controller import MissionController


def run_one(seed: int, max_steps: int = 400) -> Dict[str, Any]:
    env = Environment(rows=20, cols=20, seed=seed)
    exp = ExplorationMap(env)
    rover = Rover(env, exp)
    ctrl = MissionController(rover, exp)
    for _ in range(max_steps):
        if rover.state.mission_state in ("COMPLETED", "FAILED"):
            break
        ctrl.step()
    return ctrl.get_report()


def run_batch(seeds: List[int], max_steps: int = 400) -> List[Dict[str, Any]]:
    return [run_one(s, max_steps) for s in seeds]
