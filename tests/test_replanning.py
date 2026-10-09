
from types import SimpleNamespace
from mission.mission_controller import MissionController


def test_controller_follows_path_around_obstacle():
    rover = SimpleNamespace(x=0, y=0, energy=10)
    controller = MissionController(
        rover, None, target=(2, 0)
    )

    controller.blocked.add((1, 0))

    action = controller.step()

    assert action["type"] == "MOVE"
    assert (action["dx"], action["dy"]) != (1, 0)


def test_controller_waits_when_target_is_unreachable():
    rover = SimpleNamespace(x=0, y=0, energy=10)
    controller = MissionController(
        rover, None, target=(1, 0)
    )

    controller.blocked = {
        (1, 0),
        (0, 1),
        (0, -1),
        (-1, 0)
    }

    action = controller.step()

    assert action == {"type": "WAIT"}


def test_controller_waits_when_energy_is_empty():
    rover = SimpleNamespace(x=0, y=0, energy=0)
    controller = MissionController(rover, None)

    action = controller.step()

    assert action == {"type": "WAIT"}
