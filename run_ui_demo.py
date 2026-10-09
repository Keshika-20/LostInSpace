
import pygame
from ui import theme
from ui.map_renderer import draw_map
from ui.dashboard import draw_dashboard
from ui.controls import handle_events

def main():
    pygame.init()
    screen = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))
    pygame.display.set_caption("Lost in Space - Stage 1")
    clock = pygame.time.Clock()
    running = True

    while running:
        running = not handle_events()
        screen.fill(theme.BACKGROUND)
        draw_map(screen, rover_position=(0, 0), rows=10, cols=10)
        draw_dashboard(screen, energy=100.0, status="READY", position=(0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()