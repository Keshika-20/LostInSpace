import pygame
from ui import theme


class Controls:
    """Draw controls and convert mouse clicks into commands only."""
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 17, bold=True)
        self.direction_font = pygame.font.SysFont("arial", 13, bold=True)
        self.buttons = {
            "START": pygame.Rect(390, 638, 112, 48),
            "PAUSE": pygame.Rect(512, 638, 112, 48),
            "RESET": pygame.Rect(634, 638, 112, 48),
            "COLLECT": pygame.Rect(756, 638, 112, 48),
            "ROUTE": pygame.Rect(878, 638, 112, 48),
            "MOVE_UP": pygame.Rect(153, 628, 56, 34),
            "MOVE_LEFT": pygame.Rect(94, 668, 56, 34),
            "MOVE_DOWN": pygame.Rect(153, 668, 56, 34),
            "MOVE_RIGHT": pygame.Rect(212, 668, 56, 34),
        }
        self.labels = {
            "MOVE_UP": "UP",
            "MOVE_LEFT": "LEFT",
            "MOVE_DOWN": "DOWN",
            "MOVE_RIGHT": "RIGHT",
        }
        self._mouse_button_down = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_button_down = True
            return self._command_at(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            released_command = self._command_at(event.pos)
            saw_mouse_down = self._mouse_button_down
            self._mouse_button_down = False
            if not saw_mouse_down:
                return released_command

        return None

    def _command_at(self, position):
        for command, rect in self.buttons.items():
            if rect.inflate(4, 4).collidepoint(position):
                return command
        return None

    def draw(
        self,
        screen,
        simulation_running=None,
        collect_ready=True,
        route_ready=True,
    ):
        mouse_position = pygame.mouse.get_pos()
        for command, rect in self.buttons.items():
            hovered = rect.inflate(4, 4).collidepoint(mouse_position)
            active = (
                (simulation_running is True and command == "PAUSE")
                or (simulation_running is False and command == "START")
            )
            enabled = (
                command not in ("COLLECT", "ROUTE")
                or command == "COLLECT" and collect_ready
                or command == "ROUTE" and route_ready
            )
            fill = (
                theme.PANEL_HIGHLIGHT
                if hovered or active
                else theme.PANEL_RAISED
            )
            if not enabled:
                fill = theme.PANEL
                border = theme.PANEL_BORDER
                text_color = theme.MUTED_TEXT
            elif active:
                border = theme.SUCCESS
                text_color = theme.TEXT
            elif hovered:
                border = (130, 205, 245)
                text_color = theme.TEXT
            else:
                border = theme.PANEL_BORDER
                text_color = theme.TEXT
            pygame.draw.rect(screen, fill, rect, border_radius=7)
            pygame.draw.rect(screen, border, rect, 2, border_radius=7)
            if command.startswith("MOVE_"):
                label_text = self.labels[command]
                label_font = self.direction_font
            else:
                label_text = command
                label_font = self.font
            label = label_font.render(label_text, True, text_color)
            screen.blit(label, label.get_rect(center=rect.center))
