
import pygame


class Controls:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)
        self.buttons = {
            "START": pygame.Rect(620, 400, 100, 40),
            "PAUSE": pygame.Rect(730, 400, 100, 40),
            "RESET": pygame.Rect(675, 455, 100, 40),
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for command, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    return command
        return None

    def draw(self, screen):
        for command, rect in self.buttons.items():
            pygame.draw.rect(screen, (45, 75, 110), rect, border_radius=6)
            pygame.draw.rect(screen, (120, 170, 220), rect, 2, border_radius=6)

            text = self.font.render(command, True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=rect.center))