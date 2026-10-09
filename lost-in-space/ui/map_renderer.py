"""
True isometric 3D planetary surface renderer.
Height-displaced terrain, volumetric rocks, atmospheric depth, sci-fi overlays.
Looks like a real alien world, not a flat 2D grid.
"""
from __future__ import annotations
import math
import random
from typing import List, Optional, Tuple, Dict, Any
import pygame
from .theme import Theme
from simulation.exploration_map import (
    UNKNOWN, KNOWN_EMPTY, KNOWN_OBSTACLE, KNOWN_BASE, KNOWN_ZONE
)
from simulation.models import Position, Resource


def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(_clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _darken(c, amount=0.35):
    return tuple(_clamp(ch * (1.0 - amount)) for ch in c)


def _lighten(c, amount=0.25):
    return tuple(_clamp(ch + (255 - ch) * amount) for ch in c)


class MapRenderer:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.tile_w = Theme.TILE_W
        self.tile_h = Theme.TILE_H
        self.h_scale = Theme.HEIGHT_SCALE
        self._tick = 0
        self._pulse_events: List[Dict[str, Any]] = []

        # Continuous organic heightmap
        rng = random.Random(42)
        self.height = [[0.0] * cols for _ in range(rows)]
        self.detail = [[0.0] * cols for _ in range(rows)]

        # multi-octave hills
        for _ in range(7):
            cx = rng.uniform(0, cols)
            cy = rng.uniform(0, rows)
            rad = rng.uniform(3.0, 7.5)
            amp = rng.uniform(0.22, 0.58)
            for r in range(rows):
                for c in range(cols):
                    d = math.hypot(c - cx, r - cy) / rad
                    if d < 2.4:
                        self.height[r][c] += amp * math.exp(-d * d)

        # secondary detail ridges
        for _ in range(4):
            cx = rng.uniform(0, cols)
            cy = rng.uniform(0, rows)
            rad = rng.uniform(1.5, 3.0)
            amp = rng.uniform(0.08, 0.18)
            for r in range(rows):
                for c in range(cols):
                    d = math.hypot(c - cx, r - cy) / rad
                    if d < 2.0:
                        self.height[r][c] += amp * math.exp(-d * d * 1.4)

        # normalize
        mn = min(min(row) for row in self.height)
        mx = max(max(row) for row in self.height) or 1.0
        for r in range(rows):
            for c in range(cols):
                self.height[r][c] = (self.height[r][c] - mn) / (mx - mn + 1e-6)
                self.detail[r][c] = rng.random()

        # origin so the whole diamond fits with padding
        # Isometric bounding box of the grid
        self.origin_x = Theme.MAP_PAD + (rows + cols) * self.tile_w // 4 + 30
        self.origin_y = Theme.MAP_PAD + 48

    def map_pixel_size(self) -> Tuple[int, int]:
        # Full diamond size + margins + title bar
        w = (self.rows + self.cols) * self.tile_w // 2 + Theme.MAP_PAD * 2 + 80
        h = (self.rows + self.cols) * self.tile_h // 2 + self.h_scale + Theme.MAP_PAD * 2 + 90
        return max(w, 620), max(h, 520)

    def _iso(self, r: int, c: int, elev: float = 0.0) -> Tuple[int, int]:
        """Grid (row, col) + elevation → screen (x, y)."""
        x = self.origin_x + (c - r) * self.tile_w // 2
        y = self.origin_y + (c + r) * self.tile_h // 2 - int(elev * self.h_scale)
        return x, y

    def cell_center(self, r: int, c: int) -> Tuple[int, int]:
        elev = self.height[r][c]
        return self._iso(r, c, elev)

    def add_pulse(self, pos: Position, color: Tuple[int, int, int], life: int = 50) -> None:
        self._pulse_events.append({"pos": pos, "color": color, "life": life, "max": life})

    def tick(self) -> None:
        self._tick += 1
        self._pulse_events = [p for p in self._pulse_events if p["life"] > 0]
        for p in self._pulse_events:
            p["life"] -= 1

    def _slope_light(self, r: int, c: int) -> float:
        """Directional lighting (NW light source)."""
        h = self.height[r][c]
        hn = self.height[r - 1][c] if r > 0 else h
        hw = self.height[r][c - 1] if c > 0 else h
        return max(-0.42, min(0.55, (h - hn) * 2.1 + (h - hw) * 1.4))

    def _draw_iso_tile(self, surface: pygame.Surface, r: int, c: int,
                       top_col: Tuple[int, int, int],
                       left_col: Tuple[int, int, int],
                       right_col: Tuple[int, int, int],
                       elev: float, wall_h: int = 0) -> None:
        """Draw a single isometric prism (top face + optional side walls)."""
        tw, th = self.tile_w, self.tile_h
        cx, cy = self._iso(r, c, elev)

        # Top face (diamond)
        top = [
            (cx, cy - th // 2),
            (cx + tw // 2, cy),
            (cx, cy + th // 2),
            (cx - tw // 2, cy),
        ]
        pygame.draw.polygon(surface, top_col, top)

        # Side walls for height (gives true 3D volume)
        if wall_h > 0:
            # left face
            left = [
                (cx - tw // 2, cy),
                (cx, cy + th // 2),
                (cx, cy + th // 2 + wall_h),
                (cx - tw // 2, cy + wall_h),
            ]
            pygame.draw.polygon(surface, left_col, left)
            # right face
            right = [
                (cx + tw // 2, cy),
                (cx, cy + th // 2),
                (cx, cy + th // 2 + wall_h),
                (cx + tw // 2, cy + wall_h),
            ]
            pygame.draw.polygon(surface, right_col, right)

        # subtle rim highlight on top edges
        pygame.draw.lines(surface, _lighten(top_col, 0.18), False,
                          [(cx - tw // 2, cy), (cx, cy - th // 2), (cx + tw // 2, cy)], 1)

    def _draw_terrain_cell(self, surface: pygame.Surface, exp_map, r: int, c: int) -> None:
        cell = exp_map.get_cell((r, c))
        elev = self.height[r][c]
        shade = self._slope_light(r, c)
        det = self.detail[r][c]
        wall = max(2, int(elev * self.h_scale * 0.55) + 3)

        if cell == UNKNOWN:
            base = _mix(Theme.UNKNOWN_DARK, Theme.UNKNOWN_MID, elev * 0.4 + det * 0.12)
            left = _darken(base, 0.45)
            right = _darken(base, 0.28)
            self._draw_iso_tile(surface, r, c, base, left, right, elev, wall)
            return

        if cell == KNOWN_OBSTACLE:
            # Raised rocky outcrop
            base = _mix(Theme.ROCK_DARK, Theme.ROCK_MID, elev)
            base = _mix(base, Theme.ROCK_LIGHT, max(0, shade) * 0.55)
            left = _darken(base, 0.38)
            right = _darken(base, 0.22)
            rock_wall = wall + 8 + int(det * 6)
            self._draw_iso_tile(surface, r, c, base, left, right, elev + 0.25, rock_wall)
            # jagged top highlight
            cx, cy = self._iso(r, c, elev + 0.25)
            pygame.draw.circle(surface, Theme.ROCK_RIM, (cx, cy - 4), 3)
            return

        if cell == KNOWN_BASE:
            base = _mix(Theme.BASE_PAD, Theme.BASE_GLOW, 0.15)
            left = _darken(base, 0.35)
            right = _darken(base, 0.2)
            self._draw_iso_tile(surface, r, c, base, left, right, elev, wall + 2)
            return

        if cell == KNOWN_ZONE:
            base = _mix(Theme.ZONE_PAD, Theme.ZONE_GLOW, 0.12)
            left = _darken(base, 0.35)
            right = _darken(base, 0.2)
            self._draw_iso_tile(surface, r, c, base, left, right, elev, wall + 2)
            return

        # Known empty — dusty regolith
        t = elev * 0.5 + det * 0.22
        base = _mix(Theme.DUST_DARK, Theme.DUST_MID, t)
        base = _mix(base, Theme.DUST_LIGHT, max(0, shade) * 0.5)
        if shade < -0.12:
            base = _mix(base, Theme.DUST_DARK, abs(shade) * 0.55)
        if det > 0.82:
            base = _mix(base, Theme.DUST_HIGHLIGHT, 0.1)
        left = _darken(base, 0.32)
        right = _darken(base, 0.18)
        self._draw_iso_tile(surface, r, c, base, left, right, elev, wall)

        # sparse pebbles / micro-craters on top face
        if 0.60 < det < 0.68:
            cx, cy = self._iso(r, c, elev)
            pygame.draw.circle(surface, _darken(base, 0.4), (cx - 4, cy + 2), 2)

    def draw(
        self,
        surface: pygame.Surface,
        exp_map,
        rover_pos: Position,
        route: Optional[List[Position]] = None,
        target: Optional[Position] = None,
        resources: Optional[List[Resource]] = None,
        mission_state: str = "EXPLORING",
        return_route: Optional[List[Position]] = None,
    ) -> None:
        map_w, map_h = self.map_pixel_size()

        # deep space background
        pygame.draw.rect(surface, Theme.BG_SPACE, (0, 0, map_w, map_h))

        # subtle star field
        rng = random.Random(99)
        for _ in range(45):
            sx = rng.randint(8, map_w - 8)
            sy = rng.randint(8, map_h - 8)
            bright = rng.randint(40, 120)
            pygame.draw.circle(surface, (bright, bright, bright + 20), (sx, sy), 1)

        # Draw tiles back-to-front for correct occlusion
        # Order by (r + c) ascending, then r
        order = sorted(
            [(r, c) for r in range(self.rows) for c in range(self.cols)],
            key=lambda p: (p[0] + p[1], p[0])
        )
        for r, c in order:
            self._draw_terrain_cell(surface, exp_map, r, c)

        # Atmospheric fog overlay (soft depth)
        self._draw_atmosphere(surface, map_w, map_h)

        # Animated structures (drawn after terrain so they sit on top)
        for r in range(self.rows):
            for c in range(self.cols):
                cell = exp_map.get_cell((r, c))
                if cell == KNOWN_BASE:
                    self._draw_base(surface, r, c)
                elif cell == KNOWN_ZONE:
                    self._draw_zone(surface, r, c)

        # Resources
        if resources:
            for res in resources:
                if res.discovered:
                    self._draw_resource(surface, res)

        # Routes (under rover)
        if return_route and len(return_route) > 1:
            self._draw_route(surface, return_route, dim=True)
        if route and len(route) > 1:
            self._draw_route(surface, route)

        if target is not None:
            self._draw_target(surface, target)

        # Pulses
        for p in self._pulse_events:
            self._draw_pulse(surface, p)

        # Rover last
        self._draw_rover(surface, rover_pos, mission_state)

        # Frame + title
        pygame.draw.rect(surface, (36, 28, 68), (0, 0, map_w, map_h), 2)
        title = Theme.FONT_HEAD.render("PLANETARY SURFACE  ·  3D ISOMETRIC  ·  SECTOR 7-Δ", True, Theme.TEXT_ACCENT)
        surface.blit(title, (Theme.MAP_PAD + 4, 8))

        # Status badge
        badge_col = {
            "EXPLORING": Theme.TEXT_ACCENT, "TRAVELLING": Theme.TEXT_INFO,
            "COLLECTING": Theme.TEXT_WARNING, "TRAVELLING_TO_ZONE": Theme.TEXT_INFO,
            "UPLOADING": Theme.TEXT_SUCCESS, "RETURNING": Theme.ALERT_RETURN,
            "COMPLETED": Theme.TEXT_SUCCESS, "FAILED": Theme.TEXT_DANGER,
        }.get(mission_state, Theme.TEXT_SECONDARY)
        badge = Theme.FONT_SMALL.render(mission_state, True, badge_col)
        surface.blit(badge, (map_w - badge.get_width() - 14, 10))

        self._draw_legend(surface, map_w, map_h)

    def _draw_atmosphere(self, surface, map_w, map_h):
        fog = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        for i in range(22):
            a = int(110 * (1 - i / 22))
            pygame.draw.line(fog, (3, 2, 9, a), (0, i), (map_w, i))
            pygame.draw.line(fog, (3, 2, 9, a), (0, map_h - 1 - i), (map_w, map_h - 1 - i))
        for i in range(16):
            a = int(80 * (1 - i / 16))
            pygame.draw.line(fog, (3, 2, 9, a), (i, 0), (i, map_h))
            pygame.draw.line(fog, (3, 2, 9, a), (map_w - 1 - i, 0), (map_w - 1 - i, map_h))
        surface.blit(fog, (0, 0))

    def _draw_base(self, surface, r, c):
        elev = self.height[r][c]
        cx, cy = self._iso(r, c, elev)
        pulse = 0.55 + 0.45 * math.sin(self._tick * 0.07)
        for rad, alpha in [(20, 50), (14, 90), (9, 140)]:
            s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*Theme.BASE_GLOW, alpha), (rad, rad), rad)
            surface.blit(s, (cx - rad, cy - rad - 6))
        pygame.draw.circle(surface, Theme.BASE_GLOW, (cx, cy - 6), int(5 + pulse * 2), 2)
        pygame.draw.circle(surface, Theme.BASE_CORE, (cx, cy - 6), 3)

    def _draw_zone(self, surface, r, c):
        elev = self.height[r][c]
        cx, cy = self._iso(r, c, elev)
        pulse = abs(math.sin(self._tick * 0.05))
        for i in range(3):
            rad = int(7 + i * 5 + pulse * 4)
            s = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*Theme.ZONE_GLOW, 65 - i * 16), (rad + 1, rad + 1), rad, 2)
            surface.blit(s, (cx - rad - 1, cy - rad - 7))
        pygame.draw.line(surface, Theme.ZONE_GLOW, (cx, cy - 14), (cx, cy - 6), 2)
        pygame.draw.circle(surface, Theme.ZONE_CORE, (cx, cy - 14), 3)

    def _draw_resource(self, surface, res: Resource):
        elev = self.height[res.position[0]][res.position[1]]
        cx, cy = self._iso(*res.position, elev)
        if res.collected:
            pygame.draw.circle(surface, Theme.RESOURCE_DONE, (cx, cy - 4), 5)
            pygame.draw.line(surface, (35, 28, 16), (cx - 3, cy - 7), (cx + 3, cy - 1), 2)
            return
        pulse = 0.65 + 0.35 * math.sin(self._tick * 0.09 + res.position[0] * 0.7)
        for rad, alpha in [(16, 35), (11, 70), (7, 130)]:
            s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*Theme.RESOURCE, alpha), (rad, rad), int(rad * pulse))
            surface.blit(s, (cx - rad, cy - rad - 5))
        pygame.draw.circle(surface, Theme.RESOURCE, (cx, cy - 5), 5)
        pygame.draw.circle(surface, Theme.RESOURCE_GLOW, (cx, cy - 5), 3)
        pygame.draw.circle(surface, Theme.RESOURCE_CORE, (cx - 1, cy - 7), 2)

    def _draw_route(self, surface, route: List[Position], dim: bool = False):
        pts = []
        for p in route:
            elev = self.height[p[0]][p[1]]
            pts.append(self._iso(p[0], p[1], elev))
        if len(pts) < 2:
            return
        if not dim:
            for width, col in [(6, (0, 160, 145)), (3, Theme.ROUTE_GLOW), (1, Theme.ROUTE)]:
                pygame.draw.lines(surface, col, False, pts, width)
            for p in pts[1:-1]:
                pygame.draw.circle(surface, Theme.ROUTE_GLOW, p, 2)
        else:
            pygame.draw.lines(surface, (0, 90, 85), False, pts, 2)

    def _draw_target(self, surface, target: Position):
        elev = self.height[target[0]][target[1]]
        cx, cy = self._iso(*target, elev)
        pulse = 0.75 + 0.25 * math.sin(self._tick * 0.11)
        r = int(11 * pulse)
        pygame.draw.circle(surface, Theme.TARGET_GLOW, (cx, cy - 4), r + 3, 1)
        pygame.draw.circle(surface, Theme.TARGET, (cx, cy - 4), r, 2)
        arm, gap = 13, 4
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            pygame.draw.line(surface, Theme.TARGET,
                             (cx + dx * gap, cy - 4 + dy * gap),
                             (cx + dx * arm, cy - 4 + dy * arm), 2)

    def _draw_pulse(self, surface, p):
        elev = self.height[p["pos"][0]][p["pos"][1]]
        cx, cy = self._iso(*p["pos"], elev)
        t = p["life"] / max(1, p["max"])
        rad = int((1.0 - t) * 28 + 6)
        s = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
        alpha = int(170 * t)
        pygame.draw.circle(s, (*p["color"], alpha), (rad + 2, rad + 2), rad, 2)
        surface.blit(s, (cx - rad - 2, cy - rad - 6))

    def _draw_rover(self, surface, pos: Position, state: str):
        elev = self.height[pos[0]][pos[1]]
        cx, cy = self._iso(*pos, elev)

        # ground shadow (isometric ellipse)
        shadow = pygame.Surface((30, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, 30, 14))
        surface.blit(shadow, (cx - 15, cy + 2))

        # 3D chassis
        body_col = Theme.ROVER_BODY
        accent = Theme.ROVER_ACCENT2 if state in ("UPLOADING", "COMPLETED") else Theme.ROVER_ACCENT

        # lower body
        pygame.draw.rect(surface, Theme.ROVER_DARK, (cx - 10, cy - 4, 20, 9), border_radius=2)
        # upper plate
        pygame.draw.rect(surface, body_col, (cx - 9, cy - 10, 18, 8), border_radius=2)
        pygame.draw.rect(surface, _lighten(body_col, 0.15), (cx - 8, cy - 9, 16, 3), border_radius=1)

        # canopy / sensor
        pygame.draw.rect(surface, accent, (cx - 5, cy - 9, 10, 5), border_radius=2)

        # side pods
        pygame.draw.rect(surface, Theme.ROVER_DARK, (cx - 12, cy - 3, 4, 5), border_radius=1)
        pygame.draw.rect(surface, Theme.ROVER_DARK, (cx + 8, cy - 3, 4, 5), border_radius=1)

        # wheels (isometric)
        for wx, wy in ((cx - 7, cy + 5), (cx + 7, cy + 5)):
            pygame.draw.circle(surface, (22, 22, 30), (wx, wy), 4)
            pygame.draw.circle(surface, (65, 65, 78), (wx, wy), 4, 1)
            pygame.draw.circle(surface, (95, 95, 110), (wx, wy), 1)

        # antenna
        pygame.draw.line(surface, accent, (cx + 4, cy - 10), (cx + 9, cy - 20), 2)
        tip = Theme.TEXT_DANGER if (self._tick // 12) % 2 == 0 else accent
        pygame.draw.circle(surface, tip, (cx + 9, cy - 20), 2)

        if state in ("RETURNING", "FAILED"):
            pygame.draw.circle(surface, Theme.TEXT_WARNING, (cx, cy - 4), 16, 1)

    def _draw_legend(self, surface, map_w, map_h):
        items = [
            (Theme.DUST_MID, "Terrain"),
            (Theme.ROCK_MID, "Rock"),
            (Theme.BASE_GLOW, "Base"),
            (Theme.ZONE_GLOW, "Comm"),
            (Theme.RESOURCE, "Sample"),
            (Theme.ROUTE, "Path"),
        ]
        x = 10
        y = map_h - 18
        for col, label in items:
            pygame.draw.circle(surface, col, (x + 4, y + 4), 4)
            txt = Theme.FONT_TINY.render(label, True, Theme.TEXT_MUTED)
            surface.blit(txt, (x + 12, y))
            x += 12 + txt.get_width() + 12
