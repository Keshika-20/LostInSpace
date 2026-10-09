
from types import SimpleNamespace

from mission.stage8_controller import Stage8Controller


class FakeExplorationController:
    def __init__(self):
        self.calls = 0

    def explore_step(self):
        self.calls += 1
        return {"type": "EXPLORE"}


class FakeReturnController:
    def __init__(self, rover, actions=None):
        self.rover = rover
        self.actions = list(actions or [])
        self.calls = 0

    def step(self):
        self.calls += 1

        if self.actions:
            action = self.actions.pop(0)

            if action.get("type") == "ARRIVE":
                self.rover.zone = True
                return {"type": "WAIT"}

            return action

        return {"type": "WAIT"}


def make_rover(energy=10.0, zone=False):
    return SimpleNamespace(
        energy=energy,
        zone=zone,
        at_comm_zone=lambda: rover.zone,
    )


def test_stops_when_energy_is_empty():
    rover = SimpleNamespace(
        energy=0,
        at_comm_zone=lambda: False,
    )
    explorer = FakeExplorationController()
    controller = Stage8Controller(rover, explorer)

    assert controller.step() == {"type": "WAIT"}
    assert explorer.calls == 0


def test_explores_when_return_is_not_needed(monkeypatch):
    import mission.stage8_controller as stage8

    monkeypatch.setattr(stage8, "should_return", lambda rover: False)

    rover = SimpleNamespace(
        energy=10,
        at_comm_zone=lambda: False,
    )
    explorer = FakeExplorationController()
    controller = Stage8Controller(rover, explorer)

    assert controller.step() == {"type": "EXPLORE"}
    assert explorer.calls == 1


def test_switches_to_return_mode_when_needed(monkeypatch):
    import mission.stage8_controller as stage8

    monkeypatch.setattr(stage8, "should_return", lambda rover: True)

    rover = SimpleNamespace(
        energy=2,
        at_comm_zone=lambda: False,
        known_map=None,
        position=(0, 0),
        move_cost=1.0,
        carried_data=0,
        uploaded_data=0,
    )

    explorer = FakeExplorationController()
    controller = Stage8Controller(rover, explorer)

    # Replace the real controller so this test checks
    # the Stage 8 decision without requiring a real map.
    controller.return_controller = FakeReturnController(rover)

    action = controller.step()

    assert controller.returning is True
    assert action == {"type": "WAIT"}
    assert explorer.calls == 0

def test_stays_in_return_mode_until_zone_is_reached(monkeypatch):
    import mission.stage8_controller as stage8

    monkeypatch.setattr(stage8, "should_return", lambda rover: True)

    rover = SimpleNamespace(
        energy=2,
        zone=False,
        at_comm_zone=lambda: rover.zone,
    )
    explorer = FakeExplorationController()
    controller = Stage8Controller(rover, explorer)

    controller.return_controller = FakeReturnController(
        rover,
        actions=[
            {"type": "WAIT"},
            {"type": "ARRIVE"},
        ],
    )

    controller.step()
    assert controller.returning is True

    controller.step()
    assert controller.returning is False
    assert explorer.calls == 0
