
from mission.stage6_controller import Stage6Controller


class FakeKnownMap:
    def __init__(self, free_cells, zones):
        self.free_cells = set(free_cells)
        self.zones = list(zones)

    def is_known_free(self, cell):
        return cell in self.free_cells

    def known_zone_cells(self):
        return self.zones


class FakeRover:
    def __init__(self):
        self.position = (0, 0)
        self.energy = 10.0
        self.move_cost = 1.0
        self.carried_data = 4.0
        self.uploaded_data = 0.0
        self.in_zone = False

        self.known_map = FakeKnownMap(
            free_cells={(0, 0), (0, 1), (0, 2)},
            zones=[(0, 2)]
        )

    def at_comm_zone(self):
        return self.in_zone

    def unload(self):
        data = self.carried_data
        self.carried_data = 0.0
        return data


def test_routes_toward_known_communication_zone():
    rover = FakeRover()
    controller = Stage6Controller(rover)

    action = controller.step()

    assert action == {"type": "MOVE", "dx": 0, "dy": 1}


def test_uploads_data_inside_communication_zone():
    rover = FakeRover()
    rover.in_zone = True
    controller = Stage6Controller(rover)

    action = controller.step()

    assert action == {"type": "WAIT"}
    assert rover.uploaded_data == 4.0
    assert rover.carried_data == 0.0


def test_waits_when_no_communication_zone_is_known():
    rover = FakeRover()
    rover.known_map.zones = []
    controller = Stage6Controller(rover)

    assert controller.step() == {"type": "WAIT"}


def test_waits_when_energy_is_insufficient():
    rover = FakeRover()
    rover.energy = 1.0
    controller = Stage6Controller(rover)

    assert controller.step() == {"type": "WAIT"}

