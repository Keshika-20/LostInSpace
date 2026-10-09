
from mission.pathfinder import Pathfinder


def test_finds_straight_path():
    finder = Pathfinder()

    path = finder.find_path((0, 0), (3, 0))

    assert path == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0)
    ]


def test_finds_path_around_obstacle():
    finder = Pathfinder()

    blocked = {(1, 0)}

    path = finder.find_path((0, 0), (2, 0), blocked)

    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)
    assert (1, 0) not in path


def test_returns_none_when_goal_is_blocked():
    finder = Pathfinder()

    path = finder.find_path(
        (0, 0),
        (2, 0),
        {(2, 0)}
    )

    assert path is None


def test_returns_single_position_when_already_at_goal():
    finder = Pathfinder()

    path = finder.find_path((2, 2), (2, 2))

    assert path == [(2, 2)]


def test_returns_none_when_start_is_blocked():
    finder = Pathfinder()

    path = finder.find_path(
        (0, 0),
        (2, 0),
        {(0, 0)}
    )

    assert path is None
