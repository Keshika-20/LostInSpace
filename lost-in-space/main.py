"""
Lost in Space - Stages 1-9 complete.
True isometric 3D planetary surface UI + full working mission.
"""
from __future__ import annotations
import sys
import pygame

from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.rover import Rover
from mission.mission_controller import MissionController
from ui.theme import Theme
from ui.map_renderer import MapRenderer
from ui.dashboard import Dashboard
from ui.controls import Controls


def build_world(seed: int = 42):
    env = Environment(rows=18, cols=18, seed=seed)
    exp_map = ExplorationMap(env)
    rover = Rover(env, exp_map)
    controller = MissionController(rover, exp_map)
    return env, exp_map, rover, controller


def main():
    pygame.init()
    Theme.init_fonts()

    env, exp_map, rover, controller = build_world(seed=42)
    map_renderer = MapRenderer(env.rows, env.cols)
    map_w, map_h = map_renderer.map_pixel_size()

    panel_w = Theme.PANEL_WIDTH
    win_w = map_w + panel_w + 24
    win_h = max(map_h + 110, 720)

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("LOST IN SPACE — 3D Planetary Surface Mission")
    clock = pygame.time.Clock()

    dashboard = Dashboard(map_w + 12, 10, panel_w - 8, win_h - 120)
    controls = Controls(map_w + 12, win_h - 100, panel_w - 8)

    running = True
    sim_paused = True
    tick_ms = 240
    accumulator = 0
    report_shown = False

    while running:
        dt = clock.tick(60)
        accumulator += dt
        map_renderer.tick()

        for event in pygame.event.get():
            cmd = controls.handle_event(event)
            if cmd == "QUIT":
                running = False
            elif cmd == "START":
                sim_paused = False
                controls.set_running(True)
                dashboard.hide_report()
                report_shown = False
            elif cmd == "PAUSE":
                sim_paused = True
                controls.set_running(False)
            elif cmd == "RESET":
                env, exp_map, rover, controller = build_world(seed=42)
                map_renderer = MapRenderer(env.rows, env.cols)
                sim_paused = True
                controls.set_running(False)
                accumulator = 0
                dashboard.hide_report()
                report_shown = False
                dashboard.notifications.clear()

        if not sim_paused and accumulator >= tick_ms:
            accumulator = 0
            if rover.state.mission_state not in ("COMPLETED", "FAILED"):
                result = controller.step()
                if result.get("collected"):
                    dashboard.push_notification(
                        result.get("message", "Sample collected"), "collect"
                    )
                if result.get("uploaded"):
                    dashboard.push_notification(
                        result.get("message", "Upload complete"), "upload"
                    )
                if result.get("action") == "replan":
                    dashboard.push_notification(
                        "Route blocked - replanning", "replan"
                    )
                if result.get("action") == "energy_abort":
                    dashboard.push_notification(
                        "Critical energy - returning", "energy"
                    )
                if result.get("pulse_pos"):
                    map_renderer.add_pulse(
                        result["pulse_pos"],
                        result.get("pulse_color") or (255, 80, 60),
                    )
            elif not report_shown:
                report_shown = True
                dashboard.show_end_report(controller.get_report())
                sim_paused = True
                controls.set_running(False)

        screen.fill(Theme.BG_SPACE)
        route = controller.current_route
        map_renderer.draw(
            screen,
            exp_map,
            rover.state.position,
            route=route,
            target=rover.state.target,
            resources=exp_map.known_resources,
            mission_state=rover.state.mission_state,
        )
        metrics = controller.metrics.snapshot()
        metrics.cells_explored = exp_map.explored_count
        dashboard.draw(
            screen,
            rover.state,
            metrics,
            coverage=exp_map.coverage(),
            events=controller.events,
            route_len=len(route) if route else 0,
        )
        controls.draw(screen)

        footer = Theme.FONT_TINY.render(
            "LOST IN SPACE  |  3D Isometric Planetary Surface  |  [SPACE]  [R]  [ESC]",
            True,
            Theme.TEXT_MUTED,
        )
        screen.blit(footer, (12, win_h - 18))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
