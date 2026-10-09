"""UI controls — Member 2. Commands only, never mutates simulation."""
from __future__ import annotations
from typing import Optional
import pygame
from .theme import Theme


class Button:
    def __init__(self, rect: pygame.Rect, label: str, command: str):
        self.rect = rect
        self.label = label
        self.command = command
        self.hovered = False
        self.pressed = False
        self.enabled = True

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            bg, border, tcol = (20, 16, 36), Theme.BG_PANEL_EDGE, Theme.TEXT_MUTED
        elif self.pressed:
            bg, border, tcol = Theme.BTN_ACTIVE, Theme.TEXT_ACCENT, Theme.BTN_TEXT
        elif self.hovered:
            bg, border, tcol = Theme.BTN_HOVER, Theme.BTN_BORDER, Theme.BTN_TEXT
        else:
            bg, border, tcol = Theme.BTN_BG, Theme.BTN_BORDER, Theme.BTN_TEXT
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=8)
        if self.hovered and self.enabled:
            pygame.draw.rect(surface, (70, 60, 120),
                             (self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 3), border_radius=2)
        txt = Theme.FONT_BODY.render(self.label, True, tcol)
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                           self.rect.centery - txt.get_height() // 2))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if not self.enabled:
            return None
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            if was:
                return self.command
        return None


class Controls:
    def __init__(self, x: int, y: int, width: int):
        self.x, self.y, self.width = x, y, width
        btn_w = (width - 40) // 3
        gap = 10
        self.buttons = [
            Button(pygame.Rect(x + 10, y, btn_w, 40), "▶  START", "START"),
            Button(pygame.Rect(x + 10 + btn_w + gap, y, btn_w, 40), "⏸  PAUSE", "PAUSE"),
            Button(pygame.Rect(x + 10 + 2 * (btn_w + gap), y, btn_w, 40), "↺  RESET", "RESET"),
        ]
        self.paused = True

    def set_running(self, running: bool) -> None:
        self.paused = not running

    def draw(self, surface: pygame.Surface) -> None:
        strip = pygame.Rect(self.x, self.y - 6, self.width, 68)
        pygame.draw.rect(surface, Theme.BG_PANEL, strip, border_radius=10)
        pygame.draw.rect(surface, Theme.BG_PANEL_EDGE, strip, 1, border_radius=10)
        for b in self.buttons:
            b.draw(surface)
        hint = "PAUSED" if self.paused else "RUNNING"
        col = Theme.TEXT_WARNING if self.paused else Theme.TEXT_SUCCESS
        surface.blit(Theme.FONT_SMALL.render(hint, True, col), (self.x + 14, self.y + 46))
        keys = Theme.FONT_TINY.render("Space  ·  R  ·  Esc", True, Theme.TEXT_MUTED)
        surface.blit(keys, (self.x + self.width - keys.get_width() - 14, self.y + 46))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.QUIT:
            return "QUIT"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "QUIT"
            if event.key == pygame.K_SPACE:
                return "PAUSE" if not self.paused else "START"
            if event.key == pygame.K_r:
                return "RESET"
        for b in self.buttons:
            cmd = b.handle_event(event)
            if cmd:
                return cmd
        return None
