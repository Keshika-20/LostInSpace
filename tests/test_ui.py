import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from ui.map_renderer import draw_map, get_position
from ui.dashboard import _position
from ui.controls import Controls


class State:
    def __init__(self, position=(0, 0), energy=100):
        self.position = position
        self.energy = energy
        self.carried_data = 0.0


@pytest.fixture(autouse=True)
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def test_position_formats():
    assert get_position(State((2, 4))) == (2, 4)
    assert get_position((3, 5)) == (3, 5)
    class RC:
        row, col = 2, 7
    class XY:
        x, y = 4, 1
    assert get_position(RC()) == (2, 7)
    assert get_position(XY()) == (1, 4)
    assert _position((3, 6)) == (3, 6)


def test_draw_map_returns_grid_rect():
    surface = pygame.Surface((900, 650))
    rect = draw_map(surface, State(), rows=10, cols=10,
                    obstacles={(2, 3)}, known_map={(0, 0), (0, 1)},
                    route=[(0, 0), (0, 1), (1, 1)], target=(9, 9),
                    resources=[{"position": (1, 1), "value": 2, "data_size": 1,
                                "discovered": True, "collected": False}])
    assert rect.topleft == (50, 80)
    assert rect.size == (480, 480)


def test_invalid_grid_dimensions_raise():
    with pytest.raises(ValueError):
        draw_map(pygame.Surface((900, 650)), State(), rows=0, cols=10)


def test_controls_return_command_without_mutating_state():
    controls = Controls()
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                               pos=controls.buttons["START"].center)
    assert controls.handle_event(event) == "START"
    assert controls.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)) is None
