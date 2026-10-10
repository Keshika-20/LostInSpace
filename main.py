"""Pygame main entry point for Lost in Space — 3D Autonomous Rover Mission Control."""

import ctypes
import sys
import time
import pygame

from application_controller import ApplicationController
from simulation.satellite_renderer import draw_satellite_map, draw_satellite_zoom_intro
from ui import theme
from ui.controls import Controls
from ui.dashboard import draw_dashboard, get_fullscreen_toggle_rect


def create_application(seed=2025, resource_count=7):
    """Create a repeatable application instance with slow energy reduction."""
    app = ApplicationController(seed=seed, resource_count=resource_count)
    app.rover.move_cost = 0.35
    return app


def process_input_event(event, controls, application):
    """Process single input event for test suite compatibility."""
    command = controls.handle_event(event)
    if command is not None:
        if command in ("START", "PAUSE", "RESET", "EXPLORE_NEXT"):
            application.handle_command(command)
            messages = {
                "START": "Simulation started.",
                "PAUSE": "Simulation paused.",
                "RESET": "Simulation reset.",
                "EXPLORE_NEXT": "Advanced to next region.",
            }
            return messages.get(command)
        if command in ("COLLECT", "ROUTE", "MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"):
            if command == "COLLECT":
                res = application.collect_resource()
                if res.success:
                    return f"Collected {res.resource.value:.0f} science / {res.resource.data_size:.1f} MB."
                messages = {
                    "paused": "Press START before collecting.",
                    "no_resource": "No resource at this position.",
                    "cargo_capacity": "Cargo full. Return to base before collecting more.",
                }
                return messages.get(res.reason, "Collection failed.")
            if command == "ROUTE":
                application.handle_command("PLAN_ROUTE")
                if application.planned_target:
                    return f"Route preview: {len(application.planned_route) - 1} steps to {application.planned_target}."
                return "No discovered resource has a known safe route."
            dir_map = {
                "MOVE_UP": (-1, 0),
                "MOVE_DOWN": (1, 0),
                "MOVE_LEFT": (0, -1),
                "MOVE_RIGHT": (0, 1),
            }
            if not application.is_running:
                return "Paused. Press START before moving."
            d_row, d_col = dir_map[command]
            r, c = application.rover.position
            res = application.handle_command("MOVE", (r + d_row, c + d_col))
            if res and res.success:
                return f"Moved to {application.rover.position}."
            elif res:
                return f"Move rejected: {res.reason.replace('_', ' ')}."

    if event.type == pygame.KEYDOWN:
        movement_keys = {
            pygame.K_UP: (-1, 0),
            pygame.K_DOWN: (1, 0),
            pygame.K_LEFT: (0, -1),
            pygame.K_RIGHT: (0, 1),
            pygame.K_w: (-1, 0),
            pygame.K_s: (1, 0),
            pygame.K_a: (0, -1),
            pygame.K_d: (0, 1),
        }
        if event.key == pygame.K_c:
            res = application.collect_resource()
            if res.success:
                return f"Collected {res.resource.value:.0f} science / {res.resource.data_size:.1f} MB."
            elif res.reason == "cargo_capacity":
                return "Cargo full. Return to base before collecting more."
            elif res.reason == "paused":
                return "Press START before collecting."
        if event.key in movement_keys:
            if not application.is_running:
                return "Paused. Press START before moving."
            d_row, d_col = movement_keys[event.key]
            r, c = application.rover.position
            res = application.handle_command("MOVE", (r + d_row, c + d_col))
            if res and res.success:
                return f"Moved to {application.rover.position}."
            elif res:
                return f"Move rejected: {res.reason.replace('_', ' ')}."

    return None


def _set_windows_dpi_awareness():
    """Keep Pygame client dimensions aligned on Windows systems."""
    if sys.platform != "win32":
        return

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        set_process_context = user32.SetProcessDpiAwarenessContext
        set_process_context.argtypes = [ctypes.c_void_p]
        set_process_context.restype = ctypes.c_bool
        set_process_context(ctypes.c_void_p(-4))
    except Exception:
        pass


def main():
    _set_windows_dpi_awareness()
    pygame.init()
    
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    is_fullscreen = True
    fullscreen_console = False

    try:
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.RESIZABLE)
    except Exception:
        screen_width, screen_height = 1280, 800
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

    pygame.display.set_caption("Lost in Space — 3D Autonomous Rover Mission Control")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("segoe ui", 23, bold=True)
    eyebrow_font = pygame.font.SysFont("segoe ui", 12, bold=True)
    feedback_font = pygame.font.SysFont("segoe ui", 15, bold=True)
    legend_font = pygame.font.SysFont("segoe ui", 12, bold=True)

    controls = Controls()
    application = ApplicationController(seed=2025, resource_count=18)

    running = True
    intro_phase = True
    intro_start_time = time.time()
    intro_duration = 2.8  # seconds for planet zoom sequence

    tick_timer = 0
    tick_delay = 450  # milliseconds per autonomous step for smooth, comfortable pace
    time_sec = 0.0

    feedback = "3D Planet Landing Complete  ·  Press START for Autonomous Exploration"

    try:
        while running:
            dt = clock.tick(60)
            time_sec += dt / 1000.0
            
            # 1. Handle Planet Zoom Intro Sequence
            if intro_phase:
                elapsed = time.time() - intro_start_time
                progress = min(1.0, elapsed / intro_duration)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        # Skip zoom intro on user input
                        intro_phase = False
                
                if progress >= 1.0:
                    intro_phase = False
                
                draw_satellite_zoom_intro(screen, progress, time_sec=time_sec)
                pygame.display.flip()
                continue

            # 2. Main Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_TAB, pygame.K_F10):
                        fullscreen_console = not fullscreen_console
                        continue
                    elif event.key == pygame.K_F11:
                        is_fullscreen = not is_fullscreen
                        if is_fullscreen:
                            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN | pygame.RESIZABLE)
                        else:
                            screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        if fullscreen_console:
                            fullscreen_console = False
                            continue
                        else:
                            running = False
                            continue

                # Mouse click toggling fullscreen output screen
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    toggle_rect = get_fullscreen_toggle_rect(screen.get_width(), screen.get_height(), fullscreen_console)
                    if toggle_rect.collidepoint(event.pos):
                        fullscreen_console = not fullscreen_console
                        continue

                # UI Button interactions (in standard view)
                if not fullscreen_console:
                    command = controls.handle_event(event)
                    if command is not None:
                        if command == "START":
                            application.handle_command("START")
                            feedback = "AUTONOMOUS MISSION LAUNCHED: Rover mineral scanning & exploration..."
                        elif command == "PAUSE":
                            application.handle_command("PAUSE")
                            feedback = "Simulation Paused."
                        elif command == "RESET":
                            application.handle_command("RESET")
                            feedback = "Simulation Reset to baseline."
                        elif command == "EXPLORE_NEXT":
                            application.handle_command("EXPLORE_NEXT")
                            feedback = f"Advanced to {application.region_name}! Explored tiles preserved."

            # 3. Autonomous Simulation Step Ticking
            if application.is_running:
                tick_timer += dt
                if tick_timer >= tick_delay:
                    tick_timer = 0
                    application.update_tick()
                    
                    state = application.autonomous_mission.state
                    if state.name == "SUCCESS":
                        feedback = "MISSION SUCCESSFUL! High-value data uploaded & returned safely to Base!"
                    elif state.name == "FAILURE":
                        feedback = "MISSION FAILURE: Rover energy depleted."
                    else:
                        feedback = f"AUTONOMOUS PHASE: {state.value}..."

                    if application.autonomous_mission.logs and "If reached, mission failure may occur" in application.autonomous_mission.logs[-1]:
                        feedback = "⚠️ ALERT: If reached, mission failure may occur · Unsafe area exploration avoided!"

            # 4. Rendering Phase
            screen.fill((7, 12, 22))

            if fullscreen_console:
                # Full Screen Mission Control Output Terminal View
                draw_dashboard(screen, application, time_sec=time_sec, fullscreen_console=True)
            else:
                # Dual View: Satellite Orbital Map + Telemetry Dashboard + Controls
                map_rect = draw_satellite_map(
                    screen,
                    application.environment,
                    application.rover,
                    route=application.planned_route,
                    target=application.planned_target,
                    session_info={"useful_cells": application.autonomous_mission.useful_cells},
                    time_sec=time_sec,
                )

                # Draw Header Bar
                screen.blit(
                    eyebrow_font.render("SATELLITE ORBITAL RECONNAISSANCE & MISSION CONTROL", True, (0, 230, 255)),
                    (38, 14),
                )
                screen.blit(title_font.render("LOST IN SPACE — SATELLITE ROVER MISSION CONTROL", True, theme.TEXT), (38, 30))
                screen.blit(feedback_font.render(feedback, True, (255, 215, 0)), (38, 62))

                # Draw Telemetry Dashboard with Enlarged Output Console
                draw_dashboard(screen, application, time_sec=time_sec, fullscreen_console=False)

                # Draw Control Buttons (docked at the base of the minimized dashboard)
                controls.draw(
                    screen,
                    simulation_running=application.is_running,
                    active_state=application.autonomous_mission.state.name,
                )

                # Legend overlay under satellite map frame
                legend_y = min(screen.get_height() - 26, map_rect.bottom + 8)
                for offset_x, color, label in (
                    (0, (245, 185, 75), "ROVER 01"),
                    (85, (180, 70, 50), "CRATER"),
                    (160, (255, 215, 0), "MINERAL"),
                    (240, (0, 220, 255), "3 COMM STNS"),
                    (345, (80, 240, 180), "BASE HAB"),
                ):
                    lx = map_rect.left + offset_x
                    pygame.draw.circle(screen, color, (lx + 4, legend_y + 6), 5)
                    screen.blit(
                        legend_font.render(label, True, theme.MUTED_TEXT),
                        (lx + 13, legend_y),
                    )

            pygame.display.flip()

    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
