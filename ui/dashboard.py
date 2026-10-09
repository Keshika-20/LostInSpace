"""Draw the Stage 1 title and placeholder status panel."""

import pygame
from ui import theme


def draw_dashboard(screen, energy=100.0, status="READY", position=(0, 0)):
    """Display a title and simple status values without changing simulation state."""
    title_font = pygame.font.Font(None, 38)
    text_font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 21)

    title = title_font.render("LOST IN SPACE", True, theme.TEXT)
    subtitle = small_font.render("ROVER EXPLORATION SIMULATOR", True, theme.MUTED_TEXT)
    screen.blit(title, (40, 24))
    screen.blit(subtitle, (42, 61))

    panel = pygame.Rect(545, 100, 220, 480)
    pygame.draw.rect(screen, theme.PANEL, panel, border_radius=12)

    lines = [
        ("MISSION STATUS", theme.MUTED_TEXT),
        (str(status), theme.ACCENT),
        ("ENERGY", theme.MUTED_TEXT),
        (f"{energy:.1f}%", theme.ROVER),
        ("ROVER POSITION", theme.MUTED_TEXT),
        (f"Row: {position[0]}", theme.TEXT),
        (f"Col: {position[1]}", theme.TEXT),
        ("MAP LEGEND", theme.MUTED_TEXT),
        ("○  Rover", theme.ROVER),
        ("□  Grid cell", theme.TEXT),
    ]

    y = 125
    for label, colour in lines:
        font = small_font if label in ("MISSION STATUS", "ENERGY", "ROVER POSITION", "MAP LEGEND") else text_font
        rendered = font.render(label, True, colour)
        screen.blit(rendered, (565, y))
        y += 42 if label in ("MISSION STATUS", "ENERGY", "ROVER POSITION", "MAP LEGEND") else 31
