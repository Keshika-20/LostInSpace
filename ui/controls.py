import pygame
from ui import theme


class Controls:
    """Draw controls and convert mouse clicks into commands only."""
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 17, bold=True)
        self.buttons = {
            "START": pygame.Rect(610, 420, 105, 40),
            "PAUSE": pygame.Rect(730, 420, 105, 40),
            "RESET": pygame.Rect(672, 470, 105, 40),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for command, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    return command
        return None

    def draw(self, screen):
        for command, rect in self.buttons.items():
            pygame.draw.rect(screen, (37, 67, 97), rect, border_radius=7)
            pygame.draw.rect(screen, (100, 175, 220), rect, 2, border_radius=7)
            label = self.font.render(command, True, theme.TEXT)
            screen.blit(label, label.get_rect(center=rect.center))
