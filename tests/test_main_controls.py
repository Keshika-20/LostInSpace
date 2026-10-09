import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import main
from application_controller import ApplicationController
from main import create_application, process_input_event
from simulation.environment import Environment
from simulation.models import Resource
from ui.controls import Controls


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def click_button(controls, command):
    position = controls.buttons[command].center
    return (
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position),
        pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position),
    )


def key_press(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def test_windows_dpi_awareness_uses_per_monitor_v2(monkeypatch):
    calls = []

    class FakeFunction:
        def __call__(self, context):
            calls.append(context.value)
            return True

    class FakeUser32:
        SetProcessDpiAwarenessContext = FakeFunction()

    monkeypatch.setattr(main.sys, "platform", "win32")
    monkeypatch.setattr(
        main.ctypes,
        "WinDLL",
        lambda name, use_last_error: FakeUser32(),
        raising=False,
    )

    main._set_windows_dpi_awareness()

    assert calls == [main.ctypes.c_void_p(-4).value]


def test_button_commands_change_controller_state(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)

    start_down, start_up = click_button(controls, "START")
    assert process_input_event(start_down, controls, application) == "Simulation started."
    assert process_input_event(start_up, controls, application) is None
    assert application.is_running

    pause_down, pause_up = click_button(controls, "PAUSE")
    assert process_input_event(pause_down, controls, application) == "Simulation paused."
    assert process_input_event(pause_up, controls, application) is None
    assert not application.is_running

    application.handle_command("MOVE", (0, 1))
    reset_down, reset_up = click_button(controls, "RESET")
    assert process_input_event(reset_down, controls, application) == "Simulation reset."
    assert process_input_event(reset_up, controls, application) is None
    assert application.rover.position == (0, 0)
    assert application.rover.moves == 0
    assert application.rover.energy == 100.0
    assert not application.is_running


def test_every_control_hitbox_is_visible_in_application_window(pygame_init):
    controls = Controls()

    assert set(controls.buttons) == {
        "START",
        "PAUSE",
        "RESET",
        "COLLECT",
        "ROUTE",
        "MOVE_UP",
        "MOVE_LEFT",
        "MOVE_DOWN",
        "MOVE_RIGHT",
    }
    assert all(
        rect.left >= 0
        and rect.top >= 0
        and rect.right <= 1280
        and rect.bottom <= 720
        for rect in controls.buttons.values()
    )


def test_arrow_keys_move_rover_while_running(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    start_down, start_up = click_button(controls, "START")
    process_input_event(start_down, controls, application)
    process_input_event(start_up, controls, application)

    assert process_input_event(key_press(pygame.K_DOWN), controls, application) == "Moved to (1, 0)."
    assert process_input_event(key_press(pygame.K_RIGHT), controls, application) == "Moved to (1, 1)."
    assert application.rover.position == (1, 1)
    assert application.rover.moves == 2
    assert application.rover.energy == 98.0


def test_wasd_keys_move_rover_while_running(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    application.handle_command("START")

    assert process_input_event(key_press(pygame.K_s), controls, application) == "Moved to (1, 0)."
    assert process_input_event(key_press(pygame.K_d), controls, application) == "Moved to (1, 1)."
    assert application.rover.position == (1, 1)


def test_direction_button_moves_rover_while_running(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    start_down, start_up = click_button(controls, "START")
    process_input_event(start_down, controls, application)
    process_input_event(start_up, controls, application)

    down, up = click_button(controls, "MOVE_DOWN")
    assert process_input_event(down, controls, application) == "Moved to (1, 0)."
    assert process_input_event(up, controls, application) is None
    assert application.rover.position == (1, 0)
    assert application.rover.moves == 1
    assert application.rover.energy == 99.0


def test_collect_button_loads_current_discovered_resource(pygame_init):
    environment = Environment(5, 5)
    resource = Resource(position=(0, 1), value=42.0, data_size=2.0)
    environment.resources.append(resource)
    controls = Controls()
    application = ApplicationController(environment=environment, capacity=5.0)
    application.handle_command("START")
    assert application.rover.move_to((0, 1)).success

    collect_down, collect_up = click_button(controls, "COLLECT")

    assert process_input_event(collect_down, controls, application) == (
        "Collected 42 science / 2.0 MB."
    )
    assert process_input_event(collect_up, controls, application) is None
    assert application.rover.carried_data == 2.0
    assert resource.collected
    assert application.rover.known_map.known_resources() == []


def test_collect_rejects_resource_that_exceeds_capacity(pygame_init):
    environment = Environment(5, 5)
    resource = Resource(position=(0, 1), value=42.0, data_size=2.0)
    environment.resources.append(resource)
    application = ApplicationController(environment=environment, capacity=1.0)
    application.handle_command("START")
    assert application.rover.move_to((0, 1)).success

    feedback = process_input_event(key_press(pygame.K_c), Controls(), application)

    assert feedback == "Cargo full. Return to base before collecting more."
    assert application.rover.carried_data == 0.0
    assert not resource.collected


def test_collect_is_rejected_while_mission_is_paused(pygame_init):
    environment = Environment(5, 5)
    resource = Resource(position=(0, 1), value=42.0, data_size=2.0)
    environment.resources.append(resource)
    application = ApplicationController(environment=environment)
    assert application.rover.move_to((0, 1)).success

    result = application.collect_resource()

    assert not result.success
    assert result.reason == "paused"
    assert not resource.collected
    assert application.rover.carried_data == 0.0


def test_route_button_previews_path_to_nearest_known_resource(pygame_init):
    environment = Environment(5, 5)
    environment.resources.append(
        Resource(position=(1, 0), value=42.0, data_size=2.0)
    )
    controls = Controls()
    application = ApplicationController(environment=environment)
    route_down, _ = click_button(controls, "ROUTE")

    assert process_input_event(route_down, controls, application) == (
        "Route preview: 1 steps to (1, 0)."
    )
    assert application.planned_route == [(0, 0), (1, 0)]


def test_application_starts_with_repeatable_stage_five_world(pygame_init):
    first = create_application(seed=103)
    second = create_application(seed=103)

    first_world = (
        first.environment.grid,
        [
            (r.position, r.value, r.data_size)
            for r in first.environment.resources
        ],
    )
    second_world = (
        second.environment.grid,
        [
            (r.position, r.value, r.data_size)
            for r in second.environment.resources
        ],
    )

    assert first_world == second_world
    assert len(first.environment.resources) == 7
    assert first.rover.known_map.explored_count() > 0


def test_direction_button_reports_paused_state(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    down, _ = click_button(controls, "MOVE_RIGHT")

    assert process_input_event(down, controls, application) == (
        "Paused. Press START before moving."
    )
    assert application.rover.position == (0, 0)


def test_rejected_movement_reports_reason(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    start_down, start_up = click_button(controls, "START")
    process_input_event(start_down, controls, application)
    process_input_event(start_up, controls, application)

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


def test_start_click_enables_focused_arrow_key_movement(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)

    paused_feedback = process_input_event(
        key_press(pygame.K_DOWN), controls, application
    )
    started_feedback = process_input_event(
        click_button(controls, "START")[0], controls, application
    )
    moving_feedback = process_input_event(
        key_press(pygame.K_DOWN), controls, application
    )

    assert paused_feedback == "Paused. Press START before moving."
    assert started_feedback == "Simulation started."
    assert moving_feedback == "Moved to (1, 0)."
    assert application.rover.position == (1, 0)
    assert application.rover.moves == 1


def test_button_release_works_when_press_event_was_missed(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    release = pygame.event.Event(
        pygame.MOUSEBUTTONUP,
        button=1,
        pos=controls.buttons["START"].center,
    )

    assert process_input_event(release, controls, application) == "Simulation started."
    assert application.is_running


def test_dragging_into_button_does_not_activate_it(pygame_init):
    controls = Controls()
    application = ApplicationController(rows=5, cols=5)
    down_outside = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        button=1,
        pos=(500, 500),
    )
    release_on_start = pygame.event.Event(
        pygame.MOUSEBUTTONUP,
        button=1,
        pos=controls.buttons["START"].center,
    )

    assert process_input_event(down_outside, controls, application) is None
    assert process_input_event(release_on_start, controls, application) is None
    assert not application.is_running
