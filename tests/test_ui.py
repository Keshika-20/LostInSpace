import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from simulation.environment import OBSTACLE, Environment
from simulation.rover import Rover
from ui.map_renderer import draw_map, get_position
from ui.dashboard import _position, draw_dashboard
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


def test_dashboard_coverage_uses_free_cells_and_displays_percentage(monkeypatch):
    environment = Environment(3, 3)
    environment.grid[2][2] = OBSTACLE
    rover = Rover(environment, vision_radius=0)
    rover.move_to((0, 1))
    rendered_text = []

    class CapturingFont:
        def render(self, text, antialias, color):
            rendered_text.append(text)
            return pygame.Surface((1, 1))

    monkeypatch.setattr(pygame.font, "SysFont", lambda *args, **kwargs: CapturingFont())
    draw_dashboard(
        pygame.Surface((900, 650)),
        rover,
        False,
        environment=environment,
    )

    assert environment.free_cell_count() == 8
    assert rover.known_map.known_free_count() == 2
    assert "Explored: 2/8 (25%)" in rendered_text


def test_dashboard_coverage_handles_world_with_no_free_cells(monkeypatch):
    environment = Environment(3, 3)
    rover = Rover(environment, vision_radius=0)
    monkeypatch.setattr(environment, "free_cell_count", lambda: 0)
    rendered_text = []

    class CapturingFont:
        def render(self, text, antialias, color):
            rendered_text.append(text)
            return pygame.Surface((1, 1))

    monkeypatch.setattr(pygame.font, "SysFont", lambda *args, **kwargs: CapturingFont())
    draw_dashboard(
        pygame.Surface((900, 650)),
        rover,
        False,
        environment=environment,
    )

    assert "Explored: 1/0 (0%)" in rendered_text
