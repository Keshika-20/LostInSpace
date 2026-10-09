"""
Cinematic planetary theme — 3D isometric surface + holographic mission control.
"""
from __future__ import annotations
import pygame


class Theme:
    # Deep space / alien world palette
    BG_SPACE         = (3, 2, 9)
    BG_ATMOS         = (14, 8, 20)
    BG_PANEL         = (10, 8, 22)
    BG_PANEL_EDGE    = (48, 38, 90)
    BG_CARD          = (16, 13, 32)
    BG_CARD_EDGE     = (60, 50, 110)

    # Terrain (Martian / alien regolith)
    DUST_DARK        = (42, 26, 16)
    DUST_MID         = (68, 42, 26)
    DUST_LIGHT       = (95, 60, 36)
    DUST_HIGHLIGHT   = (128, 88, 52)
    DUST_RIM         = (155, 110, 70)

    ROCK_DARK        = (18, 15, 22)
    ROCK_MID         = (36, 32, 42)
    ROCK_LIGHT       = (58, 52, 66)
    ROCK_RIM         = (78, 70, 88)

    UNKNOWN_DARK     = (6, 5, 12)
    UNKNOWN_MID      = (12, 9, 20)

    # Structures
    BASE_PAD         = (24, 80, 140)
    BASE_GLOW        = (70, 190, 255)
    BASE_CORE        = (180, 230, 255)
    ZONE_PAD         = (14, 100, 70)
    ZONE_GLOW        = (40, 230, 150)
    ZONE_CORE        = (120, 255, 190)

    # Resources
    RESOURCE         = (230, 175, 40)
    RESOURCE_GLOW    = (255, 220, 100)
    RESOURCE_CORE    = (255, 250, 200)
    RESOURCE_DONE    = (50, 40, 22)

    # Rover
    ROVER_BODY       = (210, 218, 230)
    ROVER_DARK       = (110, 118, 132)
    ROVER_ACCENT     = (0, 210, 255)
    ROVER_ACCENT2    = (0, 255, 210)
    ROVER_SHADOW     = (0, 0, 0)

    # Path / targeting
    ROUTE            = (0, 230, 210)
    ROUTE_GLOW       = (80, 255, 240)
    TARGET           = (255, 70, 50)
    TARGET_GLOW      = (255, 130, 100)

    # Text
    TEXT_PRIMARY     = (240, 240, 252)
    TEXT_SECONDARY   = (155, 150, 180)
    TEXT_MUTED       = (85, 80, 105)
    TEXT_ACCENT      = (0, 230, 210)
    TEXT_WARNING     = (255, 165, 55)
    TEXT_DANGER      = (255, 70, 70)
    TEXT_SUCCESS     = (70, 235, 140)
    TEXT_INFO        = (100, 185, 255)

    # Buttons
    BTN_BG           = (24, 20, 48)
    BTN_HOVER        = (42, 35, 80)
    BTN_ACTIVE       = (0, 130, 120)
    BTN_BORDER       = (60, 50, 105)
    BTN_TEXT         = (230, 230, 248)

    # Energy
    ENERGY_HIGH      = (45, 215, 135)
    ENERGY_MID       = (235, 185, 45)
    ENERGY_LOW       = (235, 55, 50)
    ENERGY_BG        = (14, 11, 26)

    # Alerts
    ALERT_BLOCK      = (255, 85, 65)
    ALERT_ENERGY     = (255, 165, 45)
    ALERT_REPLAN     = (0, 205, 225)
    ALERT_UPLOAD     = (65, 225, 145)
    ALERT_RETURN     = (195, 140, 255)

    # Report
    REPORT_BG        = (6, 5, 16)
    REPORT_EDGE      = (0, 190, 170)

    # Isometric layout
    TILE_W           = 54          # isometric tile width
    TILE_H           = 27          # isometric tile height (half of width)
    HEIGHT_SCALE     = 18          # pixels of elevation per unit height
    MAP_PAD          = 12
    PANEL_WIDTH      = 360

    FONT_TITLE = FONT_HEAD = FONT_BODY = FONT_SMALL = FONT_TINY = FONT_HUGE = None

    @classmethod
    def init_fonts(cls) -> None:
        pygame.font.init()
        try:
            cls.FONT_HUGE  = pygame.font.SysFont("segoeui", 28, bold=True)
            cls.FONT_TITLE = pygame.font.SysFont("segoeui", 20, bold=True)
            cls.FONT_HEAD  = pygame.font.SysFont("segoeui", 15, bold=True)
            cls.FONT_BODY  = pygame.font.SysFont("segoeui", 13)
            cls.FONT_SMALL = pygame.font.SysFont("segoeui", 12)
            cls.FONT_TINY  = pygame.font.SysFont("segoeui", 11)
        except Exception:
            cls.FONT_HUGE  = pygame.font.Font(None, 32)
            cls.FONT_TITLE = pygame.font.Font(None, 24)
            cls.FONT_HEAD  = pygame.font.Font(None, 18)
            cls.FONT_BODY  = pygame.font.Font(None, 15)
            cls.FONT_SMALL = pygame.font.Font(None, 14)
            cls.FONT_TINY  = pygame.font.Font(None, 12)
