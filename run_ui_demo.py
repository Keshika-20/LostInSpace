
import pygame

from ui.map_renderer import draw_map
from ui.dashboard import draw_dashboard
from ui.controls import Controls
from ui import theme


class DemoEnvironment:
    def __init__(self):
        self.rows = 10
        self.cols = 10
        self.obstacles = {
            (2, 3), (3, 3), (4, 3),
            (5, 6), (6, 6), (7, 6)
        }

    def is_traversable(self, position):
        row, col = position
        return (
            0 <= row < self.rows
            and 0 <= col < self.cols
            and position not in self.obstacles
        )


class DemoRoverState:
    def __init__(self):
        self.position = (0, 0)
        self.energy = 100.0


def main():
    pygame.init()

    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("LostInSpace - Stage 1 UI Demo")

    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 28, bold=True)

    environment = DemoEnvironment()
    rover_state = DemoRoverState()
    controls = Controls()

    running = True
    simulation_running = False
    move_timer = 0
    move_delay = 400
    target = (9, 9)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            command = controls.handle_event(event)

            if command == "START":
                simulation_running = True
            elif command == "PAUSE":
                simulation_running = False
            elif command == "RESET":
                rover_state = DemoRoverState()
                simulation_running = False
                move_timer = 0

        if simulation_running:
            move_timer += clock.get_time()

            if move_timer >= move_delay:
                move_timer = 0

                row, col = rover_state.position
                target_row, target_col = target
                next_position = (row, col)

                if col < target_col:
                    next_position = (row, col + 1)
                elif row < target_row:
                    next_position = (row + 1, col)

                if (
                    next_position != rover_state.position
                    and environment.is_traversable(next_position)
                    and rover_state.energy >= 1
                ):
                    rover_state.position = next_position
                    rover_state.energy -= 1

                if rover_state.position == target:
                    simulation_running = False

        screen.fill(theme.BACKGROUND)

        title = title_font.render(
            "LOST IN SPACE", True, (115, 205, 255)
        )
        screen.blit(title, (50, 25))

        draw_map(
            screen,
            rover_state.position,
            environment.rows,
            environment.cols,
            environment.obstacles,
        )
        draw_dashboard(screen, rover_state, simulation_running)
        controls.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()