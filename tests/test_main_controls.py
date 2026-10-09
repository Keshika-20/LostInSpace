import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from application_controller import ApplicationController
from main import process_input_event
from ui.controls import Controls


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def click_button(controls, command):
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        button=1,
        pos=controls.buttons[command].center,
    )


def key_press(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def test_button_commands_change_controller_state(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)

    assert process_input_event(
        click_button(controls, "START"), controls, application
    ) == "Simulation started."
    assert application.is_running

    assert process_input_event(
        click_button(controls, "PAUSE"), controls, application
    ) == "Simulation paused."
    assert not application.is_running

    application.handle_command("MOVE", (0, 1))
    assert process_input_event(
        click_button(controls, "RESET"), controls, application
    ) == "Simulation reset."
    assert application.rover.position == (0, 0)
    assert application.rover.moves == 0
    assert application.rover.energy == 100.0
    assert not application.is_running


def test_arrow_keys_move_rover_while_running(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    process_input_event(click_button(controls, "START"), controls, application)

    assert process_input_event(key_press(pygame.K_DOWN), controls, application) == "Moved to (1, 0)."
    assert process_input_event(key_press(pygame.K_RIGHT), controls, application) == "Moved to (1, 1)."
    assert application.rover.position == (1, 1)
    assert application.rover.moves == 2
    assert application.rover.energy == 98.0


def test_rejected_movement_reports_reason(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    process_input_event(click_button(controls, "START"), controls, application)

    assert process_input_event(key_press(pygame.K_UP), controls, application) == (
        "Move rejected: out of bounds."
    )
    assert application.rover.position == (0, 0)
    assert application.rover.energy == 100.0
    assert application.rover.moves == 0


def test_movement_while_paused_reports_that_start_is_needed(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)

    assert process_input_event(
        key_press(pygame.K_RIGHT), controls, application
    ) == "Paused. Press START before moving."
    assert application.rover.position == (0, 0)
