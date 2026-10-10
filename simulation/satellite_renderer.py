"""Photorealistic Satellite Orbital Renderer for Lost in Space.

Renders realistic satellite imagery, tactical grid overlays, high-value spectrograph nodes,
comm dish arrays, top-down satellite rovers, and satellite orbital zoom sequences.
"""

import math
import os
import random
import pygame
from ui import theme


class SatelliteRenderer:
    """Satellite Renderer managing assets, tactical overlays, and satellite view projection."""

    def __init__(self, asset_dir="assets"):
        self.asset_dir = asset_dir
        self.surface_tex = None
        self.rover_tex = None
        self.comm_tex = None

        self._load_assets()

    def _load_assets(self):
        if not pygame.display.get_init():
            return
        
        try:
            surf_path = os.path.join(self.asset_dir, "satellite_surface.png")
            rover_path = os.path.join(self.asset_dir, "rover_topdown.png")
            comm_path = os.path.join(self.asset_dir, "comm_dish.png")

            if os.path.exists(surf_path):
                self.surface_tex = pygame.image.load(surf_path).convert_alpha()
            if os.path.exists(rover_path):
                self.rover_tex = pygame.image.load(rover_path).convert_alpha()
            if os.path.exists(comm_path):
                self.comm_tex = pygame.image.load(comm_path).convert_alpha()
        except Exception:
            pass


_renderer_instance = None


def get_satellite_renderer():
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = SatelliteRenderer()
    return _renderer_instance


def draw_satellite_zoom_intro(screen, progress, time_sec=0.0):
    """Render satellite orbital zoom sequence from orbit down to surface reconnaissance view.
    
    progress: float from 0.0 (high satellite orbit) to 1.0 (tactical grid surface view).
    """
    w, h = screen.get_width(), screen.get_height()
    map_center = (380, 370)

    # Deep orbital space background
    screen.fill((5, 8, 18))
    
    # Draw distant starfield
    rng = random.Random(101)
    for i in range(120):
        sx = (rng.randint(0, w) + int(time_sec * 5)) % w
        sy = rng.randint(0, h)
        bright = int(140 + 80 * math.sin(time_sec * 2.0 + i))
        pygame.draw.circle(screen, (bright, bright, min(255, bright + 40)), (sx, sy), rng.choice((1, 2)))

    # Satellite viewport frame
    viewport_r = int((1.0 - progress) * 220 + progress * 550)
    vp_rect = pygame.Rect(map_center[0] - viewport_r, map_center[1] - viewport_r, viewport_r * 2, viewport_r * 2)

    # Render planet sphere curvature when far in orbit
    if progress < 0.9:
        planet_surf = pygame.Surface((viewport_r * 2, viewport_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(planet_surf, (35, 20, 15), (viewport_r, viewport_r), viewport_r)
        
        # Satellite scan lines
        for y_line in range(0, viewport_r * 2, 12):
            alpha = int(40 + 30 * math.sin(time_sec * 4.0 + y_line))
            pygame.draw.line(planet_surf, (80, 160, 240, alpha), (0, y_line), (viewport_r * 2, y_line), 1)
        
        screen.blit(planet_surf, vp_rect.topleft)

    # Satellite Reticle & Crosshairs
    color_reticle = (0, 230, 255)
    cx, cy = map_center
    pygame.draw.circle(screen, color_reticle, map_center, int(viewport_r * 0.7), 1)
    pygame.draw.line(screen, color_reticle, (cx - viewport_r - 20, cy), (cx + viewport_r + 20, cy), 1)
    pygame.draw.line(screen, color_reticle, (cx, cy - viewport_r - 20), (cx, cy + viewport_r + 20), 1)

    # Altitude Telemetry Readout
    font_large = pygame.font.SysFont("arial", 26, bold=True)
    font_mono = pygame.font.SysFont("consolas", 14, bold=True)
    
    alt_km = int((1.0 - progress) * 450 + progress * 1.5)
    lat_val = 18.4251 + math.sin(time_sec * 0.1) * 0.001
    lon_val = 42.1584 + math.cos(time_sec * 0.1) * 0.001

    txt_t = font_large.render("SATELLITE ORBITAL DESCENT & TACTICAL LOCK", True, (0, 220, 255))
    screen.blit(txt_t, txt_t.get_rect(center=(w // 2 - 120, 80)))

    telemetry_str = f"ALTITUDE: {alt_km:03d} KM   |   LAT: {lat_val:.4f}° N   |   LON: {lon_val:.4f}° W   |   SATELLITE UPLINK: ACTIVE"
    txt_sub = font_mono.render(telemetry_str, True, (255, 215, 0))
    screen.blit(txt_sub, txt_sub.get_rect(center=(w // 2 - 120, 115)))


def draw_satellite_map(screen, environment, rover, route=None, target=None, session_info=None, time_sec=0.0):
    """Render photorealistic Satellite View of terrain, grid, assets, and HUD status."""
    renderer = get_satellite_renderer()
    
    # Dimensions & Position of Satellite Map Frame
    grid_left = 50
    grid_top = 110
    rows, cols = environment.rows, environment.cols
    cell_size = min(54, 530 // max(rows, cols))
    map_w = cols * cell_size
    map_h = rows * cell_size
    
    map_rect = pygame.Rect(grid_left, grid_top, map_w, map_h)

    # 1. Satellite Base Texture
    if renderer.surface_tex:
        tex_scaled = pygame.transform.scale(renderer.surface_tex, (map_w, map_h))
        screen.blit(tex_scaled, map_rect)
    else:
        pygame.draw.rect(screen, (38, 24, 20), map_rect)

    # Subtle Terrain Grid Shading
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            cell_x = grid_left + c * cell_size
            cell_y = grid_top + r * cell_size
            cell_rect = pygame.Rect(cell_x, cell_y, cell_size, cell_size)

            cell_type = rover.known_map.cell_at(pos)
            is_known = cell_type != -1
            is_obstacle = cell_type == 1

            # Render Obstacle Rock Fields / Craters
            if is_known and is_obstacle:
                pygame.draw.rect(screen, (75, 25, 20, 180), cell_rect)
                # Draw crater shadow & rim
                crater_center = cell_rect.center
                pygame.draw.circle(screen, (40, 15, 10), crater_center, cell_size // 3)
                pygame.draw.circle(screen, (160, 60, 45), crater_center, cell_size // 3, 2)
            elif is_known:
                # Explored ground terrain highlight overlay
                pygame.draw.rect(screen, (15, 45, 30, 40), cell_rect)

            # Highlight Useful Regions (Confirmed high-value data collected)
            if session_info and pos in session_info.get("useful_cells", set()):
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                s.fill((120, 40, 220, 65))
                screen.blit(s, (cell_x, cell_y))
                pygame.draw.rect(screen, (180, 100, 255), cell_rect, 1)

            # Communication Zone Satellite Base
            is_comm = environment.in_comm_zone(pos)
            is_comm_known = rover.known_map.is_known_zone(pos)
            if is_comm:
                pulse = int(35 * math.sin(time_sec * 4.0 + r + c))
                g_val = max(0, min(255, 160 + pulse))
                b_val = max(0, min(255, 200 + pulse))
                cz_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                
                alpha_cz = 120 if is_comm_known else 60
                cz_surf.fill((0, g_val, b_val, alpha_cz))
                screen.blit(cz_surf, (cell_x, cell_y))
                pygame.draw.rect(screen, (0, 230, 255) if is_comm_known else (0, 160, 200), cell_rect, 2)

                # Comm Dish Graphic & Radio Wave Ripples
                if renderer.comm_tex:
                    comm_icon = pygame.transform.scale(renderer.comm_tex, (cell_size - 10, cell_size - 10))
                    screen.blit(comm_icon, (cell_x + 5, cell_y + 5))
                else:
                    pygame.draw.circle(screen, (0, 220, 255), cell_rect.center, cell_size // 3, 2)
                    pygame.draw.circle(screen, (180, 250, 255), cell_rect.center, 4)

                # Radio wave pulse ring
                wave_r = int(14 + 10 * math.sin(time_sec * 5.0))
                pygame.draw.circle(screen, (0, 230, 255), cell_rect.center, wave_r, 1)

                # Explicit Label tag for Communication Zone
                tag_f = pygame.font.SysFont("arial", 10, bold=True)
                lbl_comm = tag_f.render(f"📡 COMM ZONE (R{r},C{c})", True, (0, 240, 255) if is_comm_known else (120, 200, 240))
                screen.blit(lbl_comm, (cell_x - 14, cell_y - 12))

            # Base Site (Habitat / Lander baseline)
            if pos == environment.base:
                base_rect = cell_rect.inflate(-8, -8)
                pygame.draw.rect(screen, (25, 120, 90), base_rect, border_radius=6)
                pygame.draw.rect(screen, (80, 240, 180), base_rect, 2, border_radius=6)
                font_b = pygame.font.SysFont("arial", 10, bold=True)
                screen.blit(font_b.render("BASE", True, (255, 255, 255)), (cell_x + 10, cell_y + 18))

    # 2. Atmospheric Satellite Fog-of-War Layer
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            if rover.known_map.cell_at(pos) == -1:  # UNKNOWN
                cell_x = grid_left + c * cell_size
                cell_y = grid_top + r * cell_size
                fog = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                fog.fill((8, 12, 22, 230))
                screen.blit(fog, (cell_x, cell_y))
                # Satellite scanning grid pattern for unknown cells
                pygame.draw.rect(screen, (18, 28, 48), (cell_x, cell_y, cell_size, cell_size), 1)

    # 3. Satellite Lat / Long Grid Ticks
    grid_color = (60, 90, 120)
    for r in range(rows + 1):
        y = grid_top + r * cell_size
        pygame.draw.line(screen, grid_color, (grid_left, y), (grid_left + map_w, y), 1)
    for c in range(cols + 1):
        x = grid_left + c * cell_size
        pygame.draw.line(screen, grid_color, (x, grid_top), (x, grid_top + map_h), 1)

    # Coordinate Header Labels
    label_font = pygame.font.SysFont("consolas", 11, bold=True)
    for c in range(cols):
        cx = grid_left + c * cell_size + cell_size // 2 - 10
        screen.blit(label_font.render(f"C{c:02d}", True, theme.MUTED_TEXT), (cx, grid_top - 16))
    for r in range(rows):
        ry = grid_top + r * cell_size + cell_size // 2 - 6
        screen.blit(label_font.render(f"R{r:02d}", True, theme.MUTED_TEXT), (grid_left - 32, ry))

    # 4. Route Ribbon (Satellite Trajectory Line)
    route = list(route or [])
    if len(route) > 1:
        pts = [
            (grid_left + c * cell_size + cell_size // 2, grid_top + r * cell_size + cell_size // 2)
            for r, c in route
        ]
        pygame.draw.lines(screen, (0, 230, 255), False, pts, 3)

    # 5. Science Resource Nodes (Color-Differentiated Mineral Spectrograph Hotspots)
    for res in rover.known_map.known_resources():
        if res.collected:
            continue
        r, c = res.position
        rx = grid_left + c * cell_size + cell_size // 2
        ry = grid_top + r * cell_size + cell_size // 2
        val = res.value
        
        if val >= 70:
            m_name, res_color, icon = "Rare Isotope", (255, 215, 0), "💎"
        elif val >= 50:
            m_name, res_color, icon = "Hydrated Min", (0, 230, 255), "💧"
        elif val >= 30:
            m_name, res_color, icon = "Titanium Core", (235, 90, 240), "🪨"
        else:
            m_name, res_color, icon = "Regolith Sample", (80, 240, 160), "🧪"

        glow_radius = int(12 + 4 * math.sin(time_sec * 5.0 + r + c))
        
        # Spectrograph halo
        s_halo = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s_halo, (*res_color, 120), (glow_radius, glow_radius), glow_radius)
        screen.blit(s_halo, (rx - glow_radius, ry - glow_radius))

        pygame.draw.circle(screen, res_color, (rx, ry), 7)
        pygame.draw.circle(screen, (255, 255, 255), (rx, ry), 3)

        # Mineral Name & Value Tag
        tag_f = pygame.font.SysFont("arial", 10, bold=True)
        txt = tag_f.render(f"{m_name} ({int(val)} MB)", True, res_color)
        screen.blit(txt, (rx - 28, ry - 20))

    # 6. Target Reticle
    if target:
        tr, tc = target
        tx = grid_left + tc * cell_size + cell_size // 2
        ty = grid_top + tr * cell_size + cell_size // 2
        pygame.draw.circle(screen, (255, 190, 40), (tx, ty), 16, 2)
        pygame.draw.circle(screen, (255, 215, 0), (tx, ty), 4)

    # 7. Satellite Radar Sweep Line
    radar_angle = time_sec * 1.5
    sweep_end_x = map_rect.centerx + int(320 * math.cos(radar_angle))
    sweep_end_y = map_rect.centery + int(320 * math.sin(radar_angle))
    radar_surf = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
    pygame.draw.line(radar_surf, (0, 220, 255, 45), (map_w // 2, map_h // 2),
                     (sweep_end_x - grid_left, sweep_end_y - grid_top), 2)
    screen.blit(radar_surf, map_rect.topleft)

    # 8. Satellite Rover Vehicle Rendering
    rr, rc = rover.position
    rover_x = grid_left + rc * cell_size + cell_size // 2
    rover_y = grid_top + rr * cell_size + cell_size // 2

    # Rover heading angle calculation
    if route and len(route) > 1 and route[0] == rover.position:
        nxt = route[1]
        angle_rad = math.atan2(nxt[0] - rr, nxt[1] - rc)
        angle_deg = math.degrees(-angle_rad)
    else:
        angle_deg = 0.0

    if renderer.rover_tex:
        rover_size = cell_size - 12
        scaled_r = pygame.transform.scale(renderer.rover_tex, (rover_size, rover_size))
        rotated_r = pygame.transform.rotate(scaled_r, angle_deg)
        r_rect = rotated_r.get_rect(center=(rover_x, rover_y))
        screen.blit(rotated_r, r_rect)
    else:
        pygame.draw.circle(screen, (245, 185, 65), (rover_x, rover_y), 11)
        pygame.draw.circle(screen, (255, 240, 200), (rover_x, rover_y), 11, 2)
        pygame.draw.circle(screen, (0, 220, 255), (rover_x, rover_y), 4)

    # Scanner Cone Projection
    cone_surf = pygame.Surface((cell_size * 2, cell_size * 2), pygame.SRCALPHA)
    pygame.draw.circle(cone_surf, (0, 220, 255, 35), (cell_size, cell_size), cell_size)
    screen.blit(cone_surf, (rover_x - cell_size, rover_y - cell_size))

    # Rover Label
    r_lbl_font = pygame.font.SysFont("arial", 11, bold=True)
    r_lbl = r_lbl_font.render("ROVER 01", True, (245, 195, 80))
    screen.blit(r_lbl, (rover_x - 22, rover_y + 14))

    return map_rect
