"""Pygame interface for the rover simulation."""

import ctypes
import sys

import pygame

from application_controller import ApplicationController
from simulation.environment import Environment, OBSTACLE
from simulation.exploration_map import UNKNOWN
from ui import theme
from ui.controls import Controls
from ui.dashboard import draw_dashboard
from ui.map_renderer import draw_map


MOVEMENT_KEYS = {
    pygame.K_UP: (-1, 0),
    pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1),
    pygame.K_RIGHT: (0, 1),
    pygame.K_w: (-1, 0),
    pygame.K_s: (1, 0),
    pygame.K_a: (0, -1),
    pygame.K_d: (0, 1),
}
MOVEMENT_COMMANDS = {
    "MOVE_UP": MOVEMENT_KEYS[pygame.K_UP],
    "MOVE_DOWN": MOVEMENT_KEYS[pygame.K_DOWN],
    "MOVE_LEFT": MOVEMENT_KEYS[pygame.K_LEFT],
    "MOVE_RIGHT": MOVEMENT_KEYS[pygame.K_RIGHT],
}


def create_application(seed=2025):
    """Create a repeatable Stage 3-5 world for the interactive application."""
    environment = Environment(rows=10, cols=10, base=(0, 0))
    environment.generate_obstacles(seed=seed, obstacle_rate=0.15)
    environment.place_resources(count=7, seed=seed + 1)
    return ApplicationController(
        environment=environment,
        energy=100.0,
        vision_radius=2,
        capacity=12.0,
    )


def _move_rover(application, delta):
    if not application.is_running:
        return "Paused. Press START before moving."

    row, col = application.rover.position
    row_delta, col_delta = delta
    result = application.handle_command(
        "MOVE",
        (row + row_delta, col + col_delta),
    )
    if result.success:
        feedback = f"Moved to {application.rover.position}."
    else:
        reason = result.reason.replace("_", " ")
        feedback = f"Move rejected: {reason}."
    return feedback


def process_input_event(event, controls, application):
    """Apply one Pygame input event and return visible feedback, if any."""
    command = controls.handle_event(event)
    if command is not None:
        if command in MOVEMENT_COMMANDS:
            return _move_rover(application, MOVEMENT_COMMANDS[command])
        if command == "COLLECT":
            return _collect_resource(application)
        if command == "ROUTE":
            route = application.handle_command("PLAN_ROUTE")
            if route is None:
                return "No discovered resource has a known safe route."
            return f"Route preview: {len(route) - 1} steps to {application.planned_target}."

        application.handle_command(command)
        return {
            "START": "Simulation started.",
            "PAUSE": "Simulation paused.",
            "RESET": "Simulation reset.",
        }[command]

    if event.type != pygame.KEYDOWN:
        return None
    if event.key == pygame.K_c:
        return _collect_resource(application)
    if event.key == pygame.K_p:
        route = application.handle_command("PLAN_ROUTE")
        if route is None:
            return "No discovered resource has a known safe route."
        return f"Route preview: {len(route) - 1} steps to {application.planned_target}."
    if event.key not in MOVEMENT_KEYS:
        return None
    return _move_rover(application, MOVEMENT_KEYS[event.key])


def _collect_resource(application):
    if not application.is_running:
        return "Press START before collecting."
    result = application.handle_command("COLLECT")
    if result.success:
        resource = result.resource
        if resource is None:
            raise RuntimeError("successful collection did not return its resource")
        return (
            f"Collected {resource.value:.0f} science / "
            f"{resource.data_size:.1f} MB."
        )
    messages = {
        "paused": "Press START before collecting.",
        "no_resource": "No resource at this position.",
        "resource_not_discovered": "This resource has not been scanned yet.",
        "cargo_capacity": "Cargo full. Return to base before collecting more.",
    }
    return messages[result.reason]


def _set_windows_dpi_awareness():
    """Keep the native Pygame client size and mouse-event coordinates aligned."""
    if sys.platform != "win32":
        return

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    set_process_context = user32.SetProcessDpiAwarenessContext
    set_process_context.argtypes = [ctypes.c_void_p]
    set_process_context.restype = ctypes.c_bool
    if set_process_context(ctypes.c_void_p(-4)):
        return

    error = ctypes.get_last_error()
    if error != 5:
        raise ctypes.WinError(error)

    get_thread_context = user32.GetThreadDpiAwarenessContext
    get_thread_context.restype = ctypes.c_void_p
    get_awareness = user32.GetAwarenessFromDpiAwarenessContext
    get_awareness.argtypes = [ctypes.c_void_p]
    get_awareness.restype = ctypes.c_int
    if get_awareness(get_thread_context()) >= 2:
        return

    set_thread_context = user32.SetThreadDpiAwarenessContext
    set_thread_context.argtypes = [ctypes.c_void_p]
    set_thread_context.restype = ctypes.c_void_p
    if not set_thread_context(ctypes.c_void_p(-4)):
        raise ctypes.WinError(ctypes.get_last_error())


def main():
    _set_windows_dpi_awareness()
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Lost in Space — Rover Mission Control")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 25, bold=True)
    eyebrow_font = pygame.font.SysFont("arial", 11, bold=True)
    feedback_font = pygame.font.SysFont("arial", 14)
    controls = Controls()
    application = create_application()
    running = True
    feedback = "Start mission  ·  Explore with arrows/WASD  ·  Collect with C"

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                event_feedback = process_input_event(event, controls, application)
                if event_feedback is not None:
                    feedback = event_feedback

            environment = application.environment
            rover = application.rover
            known_map = {}
            for row in range(environment.rows):
                for col in range(environment.cols):
                    position = (row, col)
                    cell = rover.known_map.cell_at(position)
                    if cell == UNKNOWN:
                        known_map[position] = "unknown"
                    elif cell == OBSTACLE:
                        known_map[position] = "obstacle"
                    else:
                        known_map[position] = "free"

            screen.fill(theme.BACKGROUND)
            map_panel = pygame.Rect(32, 100, 568, 500)
            pygame.draw.rect(screen, theme.PANEL, map_panel, border_radius=16)
            pygame.draw.rect(screen, theme.PANEL_BORDER, map_panel, 1, border_radius=16)
            draw_map(
                screen,
                rover,
                environment.rows,
                environment.cols,
                known_map=known_map,
                resources=rover.known_map.known_resources(),
                base=environment.base,
                route=application.planned_route,
                target=application.planned_target,
            )
            screen.blit(
                eyebrow_font.render("MISSION CONTROL  /  SURFACE OPERATIONS", True, theme.ACCENT),
                (38, 20),
            )
            screen.blit(title_font.render("LOST IN SPACE", True, theme.TEXT), (38, 40))
            status_text = (
                f"SEED {environment.seed}  ·  "
                f"{'MISSION ACTIVE' if application.is_running else 'MISSION PAUSED'}"
            )
            screen.blit(
                eyebrow_font.render(status_text, True, theme.SUCCESS if application.is_running else theme.WARNING),
                (852, 47),
            )
            screen.blit(feedback_font.render(feedback, True, theme.ACCENT), (42, 79))
            screen.blit(
                eyebrow_font.render("UNKNOWN TERRAIN", True, theme.MUTED_TEXT),
                (54, 105),
            )
            screen.blit(
                eyebrow_font.render(
                    f"EXPLORED {rover.known_map.explored_count():02d} / "
                    f"{environment.rows * environment.cols:02d}",
                    True,
                    theme.MUTED_TEXT,
                ),
                (444, 105),
            )
            for legend_x, color, label in (
                (54, theme.ROVER, "ROVER"),
                (164, theme.OBSTACLE, "ROCK"),
                (272, theme.RESOURCE, "RESOURCE"),
                (414, theme.BASE, "BASE"),
            ):
                pygame.draw.circle(screen, color, (legend_x + 4, 582), 4)
                screen.blit(
                    eyebrow_font.render(label, True, theme.MUTED_TEXT),
                    (legend_x + 14, 576),
                )
            planned_resource = (
                environment.resource_at(application.planned_target)
                if application.planned_target is not None
                else None
            )
            draw_dashboard(
                screen,
                rover,
                application.is_running,
                moves=rover.moves,
                carried_data=rover.carried_data,
                environment=environment,
                capacity=rover.capacity,
                target=application.planned_target,
                target_value=planned_resource.value if planned_resource is not None else None,
            )
            control_panel = pygame.Rect(32, 610, 1216, 102)
            pygame.draw.rect(screen, theme.PANEL, control_panel, border_radius=16)
            pygame.draw.rect(screen, theme.PANEL_BORDER, control_panel, 1, border_radius=16)
            screen.blit(
                eyebrow_font.render("NAVIGATION", True, theme.MUTED_TEXT),
                (94, 614),
            )
            screen.blit(
                eyebrow_font.render("MISSION ACTIONS", True, theme.MUTED_TEXT),
                (390, 614),
            )
            current_resource = environment.resource_at(rover.position)
            collect_ready = (
                application.is_running
                and current_resource is not None
                and current_resource.discovered
                and rover.can_carry(current_resource.data_size)
            )
            route_ready = bool(rover.known_map.known_resources())
            controls.draw(
                screen,
                application.is_running,
                collect_ready=collect_ready,
                route_ready=route_ready,
            )
            screen.blit(
                eyebrow_font.render("ARROWS / WASD  MOVE", True, theme.MUTED_TEXT),
                (1005, 625),
            )
            screen.blit(
                eyebrow_font.render("C  COLLECT  ·  P  ROUTE", True, theme.MUTED_TEXT),
                (1005, 645),
            )
            screen.blit(
                eyebrow_font.render("ESC / WINDOW X  QUIT", True, theme.MUTED_TEXT),
                (1005, 665),
            )
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
