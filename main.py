"""Pygame interface for the rover simulation."""

import pygame

from application_controller import ApplicationController
from simulation.environment import OBSTACLE
from simulation.exploration_map import UNKNOWN
from ui import theme
from ui.controls import Controls
from ui.dashboard import draw_dashboard
from ui.map_renderer import draw_map


def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("Lost in Space — Rover Mission Control")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 27, bold=True)
    small_font = pygame.font.SysFont("arial", 14)
    controls = Controls()
    application = ApplicationController()
    running = True

    movement_keys = {
        pygame.K_UP: (-1, 0),
        pygame.K_DOWN: (1, 0),
        pygame.K_LEFT: (0, -1),
        pygame.K_RIGHT: (0, 1),
    }

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                command = controls.handle_event(event)
                if command is not None:
                    application.handle_command(command)
                elif (
                    event.type == pygame.KEYDOWN
                    and application.is_running
                    and event.key in movement_keys
                ):
                    row, col = application.rover.position
                    row_delta, col_delta = movement_keys[event.key]
                    application.handle_command(
                        "MOVE",
                        (row + row_delta, col + col_delta),
                    )

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
            screen.blit(title_font.render("LOST IN SPACE", True, theme.ACCENT), (50, 24))
            screen.blit(
                small_font.render(
                    "Start, then use arrow keys to move • Pause stops movement",
                    True,
                    theme.MUTED_TEXT,
                ),
                (50, 54),
            )
            draw_map(
                screen,
                rover,
                environment.rows,
                environment.cols,
                known_map=known_map,
                resources=rover.known_map.known_resources(),
                base=environment.base,
            )
            draw_dashboard(
                screen,
                rover,
                application.is_running,
                moves=rover.moves,
                carried_data=rover.carried_data,
                environment=environment,
            )
            controls.draw(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
