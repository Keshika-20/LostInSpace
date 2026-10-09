
from types import SimpleNamespace

from mission.energy_manager import calculate_return_energy


class FakeKnownMap:
    def __init__(self, free_cells, zones):
        self.free_cells = set(free_cells)
        self.zones = list(zones)

    def is_known_free(self, cell):
        return cell in self.free_cells

    def known_zone_cells(self):
        return self.zones


def make_rover(zones):
    known_map = FakeKnownMap(
        free_cells={(0, 0), (0, 1), (0, 2)},
        zones=zones
    )

    return SimpleNamespace(
        position=(0, 0),
        energy=10.0,
        move_cost=1.0,
        known_map=known_map
    )


def test_calculates_energy_to_nearest_zone():
    rover = make_rover([(0, 2)])

    assert calculate_return_energy(rover) == 2.0


def test_returns_none_when_no_zone_is_known():
    rover = make_rover([])

    assert calculate_return_energy(rover) is None


def test_returns_zero_when_already_at_zone():
    rover = make_rover([(0, 0)])

    assert calculate_return_energy(rover) == 0.0

from mission.energy_manager import should_return


def test_returns_when_energy_is_at_safety_limit():
    rover = make_rover([(0, 2)])
    rover.energy = 3.0

    assert should_return(rover, safety_margin=1.0) is True


def test_continues_when_energy_is_sufficient():
    rover = make_rover([(0, 2)])
    rover.energy = 10.0

    assert should_return(rover, safety_margin=1.0) is False


def test_returns_when_no_zone_is_known():
    rover = make_rover([])

    assert should_return(rover) is True
