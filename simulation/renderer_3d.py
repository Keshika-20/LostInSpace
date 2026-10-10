"""3D Projection and Rendering Engine for Lost in Space.

Provides 3D camera transforms, 3D planet zoom animation, 3D surface grid terrain,
3D rover models, glowing 3D communication domes, and 3D high-value science crystals.
"""

import math
import random
import pygame
import numpy as np
from ui import theme


class Camera3D:
    """3D Camera with position, rotation (yaw/pitch), zoom, and perspective projection."""

    def __init__(self, target_pos=(4.5, 0.0, 4.5), distance=14.0, yaw=45.0, pitch=35.0, fov=450.0):
        self.target_x, self.target_y, self.target_z = target_pos
        self.distance = distance
        self.yaw = math.radians(yaw)
        self.pitch = math.radians(pitch)
        self.fov = fov
        self.screen_width = 1280
        self.screen_height = 720
        self.center_x = 350
        self.center_y = 360

    def update_screen_size(self, width, height, center_x=None, center_y=None):
        self.screen_width = width
        self.screen_height = height
        self.center_x = center_x if center_x is not None else width // 2 - 120
        self.center_y = center_y if center_y is not None else height // 2

    def project(self, x, y, z):
        """Project world coordinate (x, y, z) into 2D screen coordinate (sx, sy, depth)."""
        # Translate relative to target
        dx = x - self.target_x
        dy = y - self.target_y
        dz = z - self.target_z

        # Rotate around Y axis (yaw)
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        rx = dx * cos_y - dz * sin_y
        rz = dx * sin_y + dz * cos_y

        # Rotate around X axis (pitch)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)
        ry = dy * cos_p - rz * sin_p
        rz_final = dy * sin_p + rz * cos_p + self.distance

        if rz_final <= 0.1:
            rz_final = 0.1

        scale = self.fov / rz_final
        sx = self.center_x + rx * scale
        sy = self.center_y - ry * scale
        return (int(sx), int(sy), rz_final)


def draw_3d_stars(screen, count=120, time_sec=0.0):
    """Draw space starfield background."""
    w, h = screen.get_width(), screen.get_height()
    rng = random.Random(42)
    for i in range(count):
        sx = (rng.randint(0, w) + int(time_sec * (i % 5 + 1) * 2)) % w
        sy = rng.randint(0, h)
        rad = rng.choice((1, 1, 2))
        brightness = 150 + int(70 * math.sin(time_sec * 2.0 + i))
        color = (brightness, brightness, min(255, brightness + 30))
        pygame.draw.circle(screen, color, (sx, sy), rad)


def draw_planet_zoom_intro(screen, progress, time_sec=0.0):
    """Render 3D planet zoom sequence from space orbit down to surface.
    
    progress: float from 0.0 (deep space orbit) to 1.0 (landed on surface).
    """
    w, h = screen.get_width(), screen.get_height()
    center = (w // 2 - 120, h // 2)

    # Dark space background
    screen.fill((4, 7, 18))
    draw_3d_stars(screen, count=150, time_sec=time_sec)

    # 3D Planet sphere rendering
    planet_radius = int((1.0 - progress) * 260 + progress * 800)
    planet_cy = center[1] + int(progress * 700)
    planet_cx = center[0]

    # Atmosphere glow halo
    glow_surf = pygame.Surface((planet_radius * 2 + 100, planet_radius * 2 + 100), pygame.SRCALPHA)
    for r in range(planet_radius + 40, planet_radius, -3):
        alpha = int((1.0 - (r - planet_radius) / 40.0) * 90 * (1.0 - progress * 0.5))
        pygame.draw.circle(glow_surf, (80, 180, 255, alpha), (planet_radius + 50, planet_radius + 50), r)
    screen.blit(glow_surf, (planet_cx - planet_radius - 50, planet_cy - planet_radius - 50))

    # Planet main body
    if planet_radius > 0:
        pygame.draw.circle(screen, (22, 38, 62), (planet_cx, planet_cy), planet_radius)

    # 3D Grid lines on planet sphere surface
    lat_count = 12
    lon_count = 18
    rot_angle = time_sec * 0.5

    for lat in range(-lat_count // 2, lat_count // 2 + 1):
        lat_rad = math.radians(lat * 15)
        r_ring = planet_radius * math.cos(lat_rad)
        y_ring = planet_cy - int(planet_radius * math.sin(lat_rad))
        if r_ring > 5:
            ellipse_h = max(2, int(r_ring * 0.35))
            pygame.draw.ellipse(
                screen,
                (45, 95, 140),
                (planet_cx - r_ring, y_ring - ellipse_h // 2, r_ring * 2, ellipse_h),
                1,
            )

    # Zoom status overlay banner
    font_title = pygame.font.SysFont("arial", 28, bold=True)
    font_sub = pygame.font.SysFont("arial", 14, bold=True)
    
    if progress < 0.95:
        txt = font_title.render("ORBITAL ENTRY & PLANET DESCENT", True, (110, 215, 255))
        txt_rect = txt.get_rect(center=(center[0], 120))
        screen.blit(txt, txt_rect)
        
        pct_text = font_sub.render(f"APPROACH VECTOR: {int(progress * 100)}%   ·   INITIATING ROVER LANDING", True, (180, 220, 255))
        pct_rect = pct_text.get_rect(center=(center[0], 155))
        screen.blit(pct_text, pct_rect)


def draw_3d_map(screen, camera, environment, rover, known_map=None, route=None,
                target=None, session_info=None, time_sec=0.0):
    """Render the 3D surface map with terrain elevation, obstacles, comm zones, resources, and rover."""
    draw_3d_stars(screen, count=90, time_sec=time_sec)
    
    rows, cols = environment.rows, environment.cols
    route = list(route or [])
    
    # Generate heightmap and polygon meshes
    polygons = []

    def get_height(r, c, status):
        if status == "obstacle":
            return 0.9
        elif status == "unknown":
            return 0.0
        # Gentle terrain relief
        h_seed = (r * 13 + c * 37) % 100 / 100.0 * 0.2
        return h_seed

    # 1. Project Grid Cells and collect faces for z-sorting
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            cell_type = rover.known_map.cell_at(pos)
            
            if cell_type == -1:
                status = "unknown"
            elif cell_type == 1:
                status = "obstacle"
            else:
                status = "free"

            if environment.in_comm_zone(pos) and rover.known_map.is_known_zone(pos):
                status = "zone"
            if pos == environment.base:
                status = "base"

            # World coordinates: r -> z, c -> x
            x0, z0 = c, r
            x1, z1 = c + 1, r + 1
            h = get_height(r, c, status)

            # Project 4 corners
            p1 = camera.project(x0, h, z0)
            p2 = camera.project(x1, h, z0)
            p3 = camera.project(x1, h, z1)
            p4 = camera.project(x0, h, z1)

            avg_depth = (p1[2] + p2[2] + p3[2] + p4[2]) / 4.0
            polygons.append({
                "type": "cell",
                "pos": pos,
                "status": status,
                "pts": [p1[:2], p2[:2], p3[:2], p4[:2]],
                "depth": avg_depth,
                "h": h,
                "x_center": (x0 + x1) / 2.0,
                "z_center": (z0 + z1) / 2.0,
            })

    # Sort polygons back-to-front (painter's algorithm)
    polygons.sort(key=lambda p: p["depth"], reverse=True)

    # Render sorted 3D terrain cells
    for poly in polygons:
        pts = poly["pts"]
        status = poly["status"]
        pos = poly["pos"]

        if status == "unknown":
            color = (16, 22, 38)
            border_color = (25, 36, 58)
        elif status == "obstacle":
            color = (130, 55, 45)
            border_color = (180, 80, 65)
        elif status == "zone":
            # Pulsing communication zone
            pulse = int(40 * math.sin(time_sec * 4.0 + pos[0] + pos[1]))
            color = (20, 110 + pulse, 160 + pulse)
            border_color = (80, 220, 255)
        elif status == "base":
            color = (35, 150, 120)
            border_color = (90, 230, 190)
        else:
            # Regular explored terrain
            color = (48, 55, 70)
            border_color = (85, 100, 125)

        # Highlight Useful Regions
        if session_info and pos in session_info.get("useful_cells", set()):
            color = (70, 50, 110)
            border_color = (180, 120, 255)

        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, border_color, pts, 1)

        # Draw 3D Boulder for obstacle
        if status == "obstacle":
            cx, cz = poly["x_center"], poly["z_center"]
            top_pt = camera.project(cx, poly["h"] + 0.6, cz)[:2]
            base_pt = camera.project(cx, poly["h"], cz)[:2]
            pygame.draw.line(screen, (220, 110, 90), base_pt, top_pt, 4)
            pygame.draw.circle(screen, (240, 130, 100), top_pt, 7)

        # Draw 3D Comm Zone Beacon Tower
        if status == "zone":
            cx, cz = poly["x_center"], poly["z_center"]
            top_pt = camera.project(cx, 1.2, cz)[:2]
            base_pt = camera.project(cx, 0.0, cz)[:2]
            pygame.draw.line(screen, (0, 220, 255), base_pt, top_pt, 3)
            pygame.draw.circle(screen, (100, 240, 255), top_pt, 5)

    # 2. Draw 3D Route Ribbon
    if len(route) > 1:
        route_pts = []
        for r, c in route:
            pt = camera.project(c + 0.5, 0.15, r + 0.5)[:2]
            route_pts.append(pt)
        pygame.draw.lines(screen, (90, 230, 255), False, route_pts, 3)

    # 3. Draw 3D Resources (Floating Science Crystals with distinct high-value colors)
    for res in rover.known_map.known_resources():
        if res.collected:
            continue
        r, c = res.position
        # High value (>50) gets glowing Amber/Gold; regular gets Cyan/Purple
        is_high_val = res.value >= 50.0
        float_h = 0.4 + 0.15 * math.sin(time_sec * 3.0 + r + c)
        pt = camera.project(c + 0.5, float_h, r + 0.5)[:2]
        
        main_color = (255, 215, 0) if is_high_val else (210, 90, 255)
        glow_color = (255, 245, 160) if is_high_val else (240, 180, 255)
        
        pygame.draw.circle(screen, main_color, pt, 8 if is_high_val else 6)
        pygame.draw.circle(screen, glow_color, pt, 4 if is_high_val else 3)
        
        # High value label tag
        if is_high_val:
            tag_font = pygame.font.SysFont("arial", 11, bold=True)
            lbl = tag_font.render(f"HIGH VAL {int(res.value)}", True, (255, 230, 120))
            screen.blit(lbl, (pt[0] - 25, pt[1] - 20))

    # 4. Draw 3D Target Marker
    if target:
        tr, tc = target
        t_pt = camera.project(tc + 0.5, 0.2, tr + 0.5)[:2]
        pygame.draw.circle(screen, (255, 200, 50), t_pt, 12, 2)

    # 5. Draw 3D Rover Model
    rr, rc = rover.position
    rover_h = 0.25
    r_center = camera.project(rc + 0.5, rover_h, rr + 0.5)
    r_pt = r_center[:2]

    # Rover Shadow
    shadow_pt = camera.project(rc + 0.5, 0.05, rr + 0.5)[:2]
    pygame.draw.ellipse(screen, (10, 14, 25), (shadow_pt[0] - 14, shadow_pt[1] - 7, 28, 14))

    # Rover Body Box
    pygame.draw.circle(screen, (245, 185, 75), r_pt, 10)
    pygame.draw.circle(screen, (255, 240, 200), r_pt, 10, 2)
    
    # Rover Antenna & Headlamp Beam
    antenna_top = camera.project(rc + 0.5, rover_h + 0.5, rr + 0.5)[:2]
    pygame.draw.line(screen, (200, 220, 240), r_pt, antenna_top, 2)
    pygame.draw.circle(screen, (100, 230, 255), antenna_top, 3)
