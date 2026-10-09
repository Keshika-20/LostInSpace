
from mission.target_selector import TargetSelector


def test_selects_unknown_neighbour():
    selector = TargetSelector()

    known_map = {(0, 0), (-1, 0), (0, 1), (0, -1)}

    target = selector.select_target(known_map, (0, 0))

    assert target == (1, 0)


def test_returns_none_when_all_neighbours_are_known():
    selector = TargetSelector()

    known_map = {
        (0, 0),
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    }

    target = selector.select_target(known_map, (0, 0))

    assert target is None


def test_does_not_select_known_neighbour():
    selector = TargetSelector()

    known_map = {(0, 0), (1, 0)}

    target = selector.select_target(known_map, (0, 0))

    assert target == (-1, 0)




def test_selector_avoids_blocked_location():
    selector = TargetSelector()

    target = selector.select_target(
        known_map={(0, 0)},
        current_position=(0, 0),
        blocked={(1, 0)}
    )

    assert target != (1, 0)
    assert target is not None


def test_selector_prefers_candidate_closer_to_goal():
    selector = TargetSelector()

    target = selector.select_target(
        known_map={(0, 0)},
        current_position=(0, 0),
        goal=(5, 0)
    )

    assert target == (1, 0)


def test_selector_returns_none_when_all_neighbours_blocked():
    selector = TargetSelector()

    target = selector.select_target(
        known_map={(0, 0)},
        current_position=(0, 0),
        blocked={
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1)
        }
    )

    assert target is None
