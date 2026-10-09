
import pygame
import sys
import math
import random

from simulation.environment import Environment
from simulation.exploration_map import ExplorationMap
from simulation.models import RoverState
from simulation.rover import Rover
from mission.mission_controller import MissionController
from ui.map_renderer import MapRenderer
from ui.dashboard import Dashboard
from ui.controls import Controls
from ui import theme

W, H = 1280, 800


def draw_surface_background(screen):
    w, h = screen.get_size()
    horizon = int(h * 0.36)

    for y in range(h):
        t = y / h
        color = (
            int(7 + 18 * t),
            int(15 + 13 * t),
            int(23 + 7 * t)
        )
        pygame.draw.line(screen, color, (0, y), (w, y))

    pygame.draw.rect(
        screen, (47, 38, 37),
        (0, horizon, w, h - horizon)
    )

    for layer in range(4):
        points = [(0, h)]

        for x in range(0, w + 20, 20):
            y = horizon + layer * 28 + int(
                22 * math.sin(x * 0.009 + layer * 1.6)
                + 12 * math.sin(x * 0.023 + layer)
            )
            points.append((x, y))

        points.extend([(w, h), (0, h)])

        colors = [
            (61, 54, 53),
            (75, 54, 46),
            (103, 63, 46),
            (126, 70, 46)
        ]
        pygame.draw.polygon(screen, colors[layer], points)

    rng = random.Random(9)

    for _ in range(220):
        x = rng.randrange(w)
        y = rng.randrange(horizon, h)
        size = rng.randrange(1, 4)
        color = rng.choice([
            (145, 83, 53),
            (85, 55, 45),
            (171, 98, 57),
            (52, 43, 39)
        ])
        pygame.draw.ellipse(
            screen, color,
            (x, y, size * 2, size)
        )


def create_mission():
    env = Environment(48, 48, seed=random.randrange(10000))
    known = ExplorationMap(env)
    state = RoverState(position=env.base)

    known.observe(env, state.position, radius=5)

    rover = Rover(env, state, known)
    controller = MissionController(env, rover, known)
    mapper = MapRenderer(env.rows, env.cols, 15)
    dashboard = Dashboard()

    return env, known, state, rover, controller, mapper, dashboard


def main():
    pygame.init()
    pygame.display.set_caption(
        "LOST IN SPACE | Autonomous Rover Operations"
    )

    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("consolas", 17, bold=True)
    small = pygame.font.SysFont("consolas", 12)
    tiny = pygame.font.SysFont("consolas", 10)

    env, known, state, rover, controller, mapper, dashboard = (
        create_mission()
    )

    controls = Controls()

    paused = False
    running = True
    accumulator = 0.0
    step_interval = 0.28

    while running:
        dt = min(clock.tick(60) / 1000, 0.1)
        accumulator += dt

        w, h = screen.get_size()
        draw_surface_background(screen)

        # Header
        pygame.draw.rect(screen, (5, 12, 18), (0, 0, w, 56))
        pygame.draw.line(
            screen, theme.BORDER, (0, 55), (w, 55), 1
        )

        title = pygame.font.SysFont(
            "consolas", 22, bold=True
        )
        screen.blit(
            title.render("LOST IN SPACE", True, theme.TEXT),
            (20, 8)
        )
        screen.blit(
            small.render(
                "AUTONOMOUS PLANETARY EXPLORATION",
                True, theme.CYAN
            ),
            (22, 34)
        )

        status_text = (
            "PAUSED" if paused else "AUTONOMOUS"
        )
        status_color = theme.AMBER if paused else theme.GREEN

        pygame.draw.circle(
            screen, status_color, (w - 155, 27), 5
        )
        screen.blit(
            small.render(status_text, True, theme.TEXT),
            (w - 142, 20)
        )

        # Compact two-column layout
        margin = 14
        gap = 9
        top = 67
        event_h = 120
        event_y = h - event_h - 14

        available_w = w - 2 * margin - gap
        left_w = int(available_w * 0.55)
        right_x = margin + left_w + gap
        right_w = w - right_x - margin

        map_rect = pygame.Rect(
            margin, top, left_w, event_y - top - 14
        )

        mapper.draw(
            screen, map_rect, env, known, state,
            controller, small
        )

        tele = pygame.Rect(right_x, top, right_w, 150)
        mission = pygame.Rect(
            right_x, tele.bottom + 8, right_w, 170
        )
        surface = pygame.Rect(
            right_x, mission.bottom + 8, right_w, 105
        )
        control_rect = pygame.Rect(
            right_x, surface.bottom + 8, right_w, 145
        )

        dashboard.draw(
            screen, font, small, state, known, controller,
            {
                "telemetry": tele,
                "mission": mission,
                "status": surface,
                "events": pygame.Rect(
                    margin, event_y, w - 2 * margin, event_h
                )
            },
            paused
        )

        controls.draw(screen, font, small, control_rect)

        screen.blit(
            tiny.render(
                "AUTO NAVIGATION  |  LIVE TELEMETRY  |  "
                "SCIENTIFIC SAMPLE RECOVERY",
                True, theme.MUTED
            ),
            (margin, h - 5)
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            action = controls.handle_event(event)

            if action == "START":
                paused = False
                dashboard.log("AUTONOMOUS NAVIGATION RESUMED")

            elif action == "PAUSE":
                paused = True
                dashboard.log("SIMULATION PAUSED")

            elif action == "SCAN":
                known.observe(env, state.position, radius=6)
                dashboard.log("LOCAL SENSOR SWEEP COMPLETE")

            elif action == "COLLECT":
                collected = False

                for resource in known.resources.values():
                    if (
                        resource.position == state.position
                        and not resource.collected
                    ):
                        resource.collected = True
                        state.carried_data += resource.data_size
                        dashboard.log(
                            f"SAMPLE SECURED +{resource.data_size:.1f} MB"
                        )
                        collected = True
                        break

                if not collected:
                    dashboard.log("NO SAMPLE AT CURRENT LOCATION")

            elif action == "RESET":
                (
                    env, known, state, rover, controller,
                    mapper, dashboard
                ) = create_mission()

                paused = False
                accumulator = 0
                dashboard.log("NEW AUTONOMOUS MISSION STARTED")

        # The rover moves by itself; no WASD input is required.
        if not paused and accumulator >= step_interval:
            accumulator = 0

            result = controller.step()

            if result and result.get("event"):
                dashboard.log(result["event"])

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()