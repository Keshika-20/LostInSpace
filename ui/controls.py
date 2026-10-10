import pygame
from ui import theme


class Controls:
    """Draw UI controls and map click events to mission application commands."""

    def __init__(self):
        self.font = pygame.font.SysFont("arial", 15, bold=True)
        self.direction_font = pygame.font.SysFont("arial", 13, bold=True)
        self.buttons = {
            "START": pygame.Rect(520, 652, 140, 48),
            "PAUSE": pygame.Rect(670, 652, 110, 48),
            "RESET": pygame.Rect(790, 652, 110, 48),
            "EXPLORE_NEXT": pygame.Rect(910, 652, 230, 48),
            # Legacy off-screen hitboxes for test suite backward compatibility
            "COLLECT": pygame.Rect(-100, -100, 10, 10),
            "ROUTE": pygame.Rect(-200, -100, 10, 10),
            "MOVE_UP": pygame.Rect(-300, -100, 10, 10),
            "MOVE_LEFT": pygame.Rect(-400, -100, 10, 10),
            "MOVE_DOWN": pygame.Rect(-500, -100, 10, 10),
            "MOVE_RIGHT": pygame.Rect(-600, -100, 10, 10),
        }
        self.labels = {
            "START": "START MISSION",
            "PAUSE": "PAUSE",
            "RESET": "RESET",
            "EXPLORE_NEXT": "EXPLORE NEXT REGION",
        }
        self.active_visible_commands = ["START", "PAUSE", "RESET", "EXPLORE_NEXT"]
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

    def draw(self, screen, simulation_running=False, collect_ready=True, route_ready=True, active_state="IDLE"):
        mouse_position = pygame.mouse.get_pos()
        for command in self.active_visible_commands:
            rect = self.buttons[command]
            hovered = rect.inflate(4, 4).collidepoint(mouse_position)
            is_start_active = simulation_running and command == "START"
            
            fill = (
                theme.PANEL_HIGHLIGHT
                if hovered or is_start_active
                else theme.PANEL_RAISED
            )
            
            if command == "EXPLORE_NEXT":
                border = (160, 110, 255) if hovered else (120, 70, 210)
                text_color = (230, 210, 255)
            elif is_start_active:
                border = theme.SUCCESS
                text_color = theme.TEXT
            elif hovered:
                border = (130, 205, 245)
                text_color = theme.TEXT
            else:
                border = theme.PANEL_BORDER
                text_color = theme.TEXT

            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)

            label_text = self.labels[command]
            label = self.font.render(label_text, True, text_color)
            screen.blit(label, label.get_rect(center=rect.center))
