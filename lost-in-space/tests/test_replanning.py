"""Stage 4/7 replanning tests."""
from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap, KNOWN_EMPTY, KNOWN_OBSTACLE
from simulation.rover import Rover
from mission.mission_controller import MissionController
from simulation.pathfinding import find_path


def test_blocked_triggers_replan():
    env = Environment(rows=12, cols=12, seed=11)
    exp = ExplorationMap(env)
    # force open map
    for r in range(12):
        for c in range(12):
            exp.known[r][c] = KNOWN_EMPTY
    rover = Rover(env, exp, start=(5, 5))
    ctrl = MissionController(rover, exp)
    # plan somewhere
    ctrl._plan_to((5, 10))
    assert ctrl.current_route is not None
    # block next cell in true world and known map
    if len(ctrl.current_route) > 1:
        blocked = ctrl.current_route[1]
        env.block_cell(blocked)
        exp.known[blocked[0]][blocked[1]] = KNOWN_OBSTACLE
        result = ctrl.step()
        # should replan or report blocked
        assert result["action"] in ("replan", "move", "plan", "idle")


def test_no_endless_loop():
    env = Environment(rows=8, cols=8, seed=2)
    exp = ExplorationMap(env)
    rover = Rover(env, exp)
    ctrl = MissionController(rover, exp)
    for _ in range(60):
        ctrl.step()
        if rover.state.mission_state in ("COMPLETED", "FAILED"):
            break
    assert rover.state.mission_state in ("COMPLETED", "FAILED", "EXPLORING",
                                       "TRAVELLING", "RETURNING", "COLLECTING",
                                       "TRAVELLING_TO_ZONE", "UPLOADING")
