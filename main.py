"""Pygame main entry point for Lost in Space — 3D Autonomous Rover Mission Control."""

import ctypes
import sys
import time
import pygame

from application_controller import ApplicationController
from simulation.satellite_renderer import draw_satellite_map, draw_satellite_zoom_intro
from ui import theme
from ui.controls import Controls
from ui.dashboard import draw_dashboard


def create_application(seed=2025):
    """Create a repeatable application instance with slow energy reduction."""
    app = ApplicationController(seed=seed)
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
    
    screen_width, screen_height = 1280, 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Lost in Space — 3D Autonomous Rover Mission Control")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 22, bold=True)
    eyebrow_font = pygame.font.SysFont("arial", 11, bold=True)
    feedback_font = pygame.font.SysFont("arial", 13)

    controls = Controls()
    application = ApplicationController(seed=2025)

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
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue

                # UI Button interactions
                command = controls.handle_event(event)
                if command is not None:
                    if command == "START":
                        application.handle_command("START")
                        feedback = "AUTONOMOUS MISSION LAUNCHED: Rover target scanning & exploring..."
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

            # 4. Rendering Phase
            screen.fill((7, 12, 22))

            # Draw Photorealistic Satellite Orbital Map
            draw_satellite_map(
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

            # Draw Telemetry Dashboard
            draw_dashboard(screen, application, time_sec=time_sec)

            # Draw Control Buttons
            controls.draw(
                screen,
                simulation_running=application.is_running,
                active_state=application.autonomous_mission.state.name,
            )

            # Legend overlay under satellite map frame (left side, no overlap with buttons)
            legend_y = 658
            for legend_x, color, label in (
                (50, (245, 185, 75), "ROVER 01"),
                (135, (180, 70, 50), "CRATER"),
                (210, (255, 215, 0), "MINERAL"),
                (290, (0, 220, 255), "COMM STN"),
                (380, (80, 240, 180), "BASE HAB"),
            ):
                pygame.draw.circle(screen, color, (legend_x + 4, legend_y + 6), 5)
                screen.blit(
                    eyebrow_font.render(label, True, theme.MUTED_TEXT),
                    (legend_x + 13, legend_y),
                )

            pygame.display.flip()

    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
