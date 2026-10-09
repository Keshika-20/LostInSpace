
from types import SimpleNamespace
from mission.mission_controller import MissionController


def test_controller_returns_move():
    rover = SimpleNamespace(x=0, y=0, energy=10)
    controller = MissionController(rover, None, target=(5, 5))

    action = controller.step()

    assert action == {"type": "MOVE", "dx": 1, "dy": 0}


def test_controller_waits_when_target_reached():
    rover = SimpleNamespace(x=5, y=5, energy=10)
    controller = MissionController(rover, None, target=(5, 5))

    action = controller.step()

    assert action == {"type": "WAIT"}


def test_controller_waits_when_energy_is_empty():
    rover = SimpleNamespace(x=0, y=0, energy=0)
    controller = MissionController(rover, None, target=(5, 5))

    action = controller.step()

    assert action == {"type": "WAIT"}


def test_controller_selects_new_target_after_reaching_target():
    rover = SimpleNamespace(x=1, y=0, energy=10)

    controller = MissionController(
        rover,
        None,
        target=(1, 0)
    )

    controller.known_map = {(1, 0)}
    controller.blocked = set()

    action = controller.explore_step()

    assert action["type"] == "MOVE"
