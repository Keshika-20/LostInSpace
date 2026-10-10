"""3D Mission Control Dashboard and Telemetry HUD."""

import pygame
from ui import theme


def _position(rover_state):
    position = getattr(rover_state, "position", rover_state)
    if isinstance(position, tuple) and len(position) == 2:
        return int(position[0]), int(position[1])
    if hasattr(position, "row") and hasattr(position, "col"):
        return int(position.row), int(position.col)
    if hasattr(position, "x") and hasattr(position, "y"):
        return int(position.y), int(position.x)
    raise TypeError("Unsupported rover position format")


def get_fullscreen_toggle_rect(screen_w, screen_h, fullscreen_console=False):
    """Return clickable bounding box for fullscreen output terminal toggle button."""
    if fullscreen_console:
        return pygame.Rect(screen_w - 280, 24, 250, 36)
    width = min(390, max(360, int(screen_w * 0.28))) if screen_w >= 1000 else 380
    x = screen_w - width - 16
    stats_y = 86 + 54
    card_y2 = stats_y + 56 + 72
    sec_y = card_y2 + 74
    out_y = sec_y + 56
    return pygame.Rect(x + width - 118, out_y + 3, 98, 20)


def _draw_fullscreen_console(screen, rover, env, mission, reg_name, state_str, logs, time_sec=0.0):
    """Render full-screen NASA / Mission Control output console terminal."""
    screen_w, screen_h = screen.get_width(), screen.get_height()
    
    # Deep terminal background
    screen.fill((5, 9, 18))

    term_rect = pygame.Rect(20, 16, screen_w - 40, screen_h - 32)
    pygame.draw.rect(screen, (7, 13, 26), term_rect, border_radius=12)
    pygame.draw.rect(screen, (0, 210, 255), term_rect, 2, border_radius=12)

    # Top Header Bar
    hdr = pygame.Rect(term_rect.x, term_rect.y, term_rect.width, 54)
    pygame.draw.rect(screen, (13, 24, 42), hdr, border_top_left_radius=12, border_top_right_radius=12)
    pygame.draw.line(screen, (0, 210, 255), hdr.bottomleft, hdr.bottomright, 2)

    title_f = pygame.font.SysFont("segoe ui", 22, bold=True)
    mono_f = pygame.font.SysFont("consolas", 15, bold=True)
    small_f = pygame.font.SysFont("segoe ui", 13, bold=True)

    screen.blit(
        title_f.render("▶ NASA MISSION CONTROL REAL-TIME OUTPUT SCREEN [FULL SCREEN]", True, (0, 240, 255)),
        (hdr.x + 20, hdr.y + 12),
    )

    # Toggle return button
    btn_rect = get_fullscreen_toggle_rect(screen_w, screen_h, fullscreen_console=True)
    pygame.draw.rect(screen, (24, 45, 75), btn_rect, border_radius=6)
    pygame.draw.rect(screen, (255, 215, 0), btn_rect, 1, border_radius=6)
    screen.blit(
        small_f.render("⛶ RETURN TO DUAL VIEW (TAB/ESC)", True, (255, 215, 0)),
        (btn_rect.x + 10, btn_rect.y + 8),
    )

    # Sub-header telemetry status ticker
    r, c = _position(rover)
    energy = float(getattr(rover, "energy", 100.0))
    up_data = float(getattr(rover, "uploaded_data", 0.0))
    num_zones = len(env.zone_cells) if env and hasattr(env, "zone_cells") else 3
    status_bar_txt = (
        f"STATUS: {state_str}  ·  TARGET: {reg_name.upper()}  ·  ROVER AT ROW {r:02d}, COL {c:02d}  ·  "
        f"BATTERY RESERVE: {energy:.1f}%  ·  TRANSMITTED: {up_data:.1f} MB  ·  COMM RELAYS: {num_zones} ONLINE"
    )
    screen.blit(small_f.render(status_bar_txt, True, (130, 220, 255)), (term_rect.x + 22, hdr.bottom + 12))
    pygame.draw.line(screen, (25, 45, 70), (term_rect.x + 18, hdr.bottom + 36), (term_rect.right - 18, hdr.bottom + 36), 1)

    # Multi-line console log output filling full screen height
    log_y = hdr.bottom + 48
    line_spacing = 26
    max_lines = max(6, (term_rect.bottom - log_y - 28) // line_spacing)
    recent_logs = logs[-max_lines:] if logs else []

    if recent_logs:
        for entry in recent_logs:
            if "If reached, mission failure may occur" in entry:
                entry_color = (255, 110, 90)
                prefix = "⚠️ "
            elif "HIGH MINERAL" in entry:
                entry_color = (255, 225, 50)
                prefix = "★ "
            elif "Explored" in entry or "IDENTIFIED" in entry:
                entry_color = (100, 235, 255)
                prefix = "💎 "
            elif "SUCCESS" in entry or "ACCOMPLISHED" in entry:
                entry_color = (80, 250, 170)
                prefix = "✓ "
            else:
                entry_color = (220, 235, 255)
                prefix = "▸ "

            screen.blit(mono_f.render(f"{prefix}{entry}", True, entry_color), (term_rect.x + 24, log_y))
            log_y += line_spacing
    else:
        screen.blit(
            mono_f.render("▸ System online. Awaiting mission commands to begin exploration loop...", True, theme.MUTED_TEXT),
            (term_rect.x + 24, log_y),
        )

    # Bottom footer helper
    screen.blit(
        small_f.render("Full Screen Output Console Active — Press TAB or click RETURN button to exit to Satellite Map", True, theme.MUTED_TEXT),
        (term_rect.x + 24, term_rect.bottom - 24),
    )


def draw_dashboard(screen, application, simulation_running=False, environment=None, time_sec=0.0, fullscreen_console=False):
    """Draw right-side telemetry panel, session statistics, data upload log, and mission status."""
    if hasattr(application, "rover"):
        rover = application.rover
        env = application.environment
        mission = application.autonomous_mission
        reg_name = application.region_name
        sess_cnt = application.session_count
        succ_cnt = application.successful_sessions
        fail_cnt = application.failed_sessions
        useful_cnt = application.useful_regions_count
        is_running = application.is_running
        state_str = mission.state.value if hasattr(mission.state, "value") else str(mission.state)
        state_name = mission.state.name if hasattr(mission.state, "name") else "IDLE"
        logs = mission.logs
    else:
        # Compatibility fallback for test fixtures passing raw rover state
        rover = application
        env = environment
        mission = None
        state_str = "PAUSED" if not simulation_running else "RUNNING"
        state_name = "IDLE"
        reg_name = "Region 1: Ares Planitia"
        sess_cnt, succ_cnt, fail_cnt, useful_cnt = 1, 0, 0, 0
        is_running = simulation_running
        logs = []

    if fullscreen_console:
        _draw_fullscreen_console(screen, rover, env, mission, reg_name, state_str, logs, time_sec=time_sec)
        return

    title_font = pygame.font.SysFont("segoe ui", 16, bold=True)
    label_font = pygame.font.SysFont("segoe ui", 11, bold=True)
    value_font = pygame.font.SysFont("segoe ui", 17, bold=True)
    body_font = pygame.font.SysFont("segoe ui", 12)
    small_font = pygame.font.SysFont("segoe ui", 11)
    console_font = pygame.font.SysFont("consolas", 12, bold=True)

    # Minimized right-side panel docked cleanly on the right
    screen_w, screen_h = screen.get_width(), screen.get_height()
    width = min(390, max(360, int(screen_w * 0.28))) if screen_w >= 1000 else 380
    x = screen_w - width - 16
    y = 86
    panel_height = max(560, screen_h - y - 16)
    panel = pygame.Rect(x, y, width, panel_height)
    
    pygame.draw.rect(screen, theme.PANEL, panel, border_radius=14)
    pygame.draw.rect(screen, theme.PANEL_BORDER, panel, 1, border_radius=14)

    # Title & Target Header
    screen.blit(title_font.render("ROVER TELEMETRY & CONTROL", True, theme.TEXT), (x + 14, y + 10))
    screen.blit(
        small_font.render(f"TARGET: {reg_name.upper()}", True, theme.ACCENT),
        (x + 14, y + 32),
    )

    # State Status Badge (compact pill on the right of header)
    if state_name == "SUCCESS":
        status_color = theme.SUCCESS
    elif state_name == "FAILURE":
        status_color = theme.ERROR
    elif is_running:
        status_color = theme.ACCENT
    else:
        status_color = theme.WARNING

    status_rect = pygame.Rect(x + width - 138, y + 10, 124, 24)
    pygame.draw.rect(screen, theme.PANEL_RAISED, status_rect, border_radius=12)
    pygame.draw.rect(screen, status_color, status_rect, 1, border_radius=12)
    pygame.draw.circle(screen, status_color, (status_rect.x + 10, status_rect.centery), 4)
    screen.blit(
        label_font.render(state_str[:16], True, status_color),
        (status_rect.x + 18, status_rect.y + 5),
    )

    # Session Stats Banner
    stats_y = y + 54
    stats_box = pygame.Rect(x + 14, stats_y, width - 28, 50)
    pygame.draw.rect(screen, theme.PANEL_RAISED, stats_box, border_radius=8)
    pygame.draw.rect(screen, theme.PANEL_BORDER, stats_box, 1, border_radius=8)

    col1 = f"SESS: {sess_cnt}"
    col2 = f"SUCC: {succ_cnt}"
    col4 = f"USEFUL: {useful_cnt}"

    screen.blit(label_font.render(col1, True, theme.TEXT), (stats_box.x + 10, stats_box.y + 7))
    screen.blit(label_font.render(col2, True, theme.SUCCESS), (stats_box.x + 95, stats_box.y + 7))
    screen.blit(label_font.render(col4, True, (190, 140, 255)), (stats_box.x + 185, stats_box.y + 7))

    # High Mineral Zone Mention
    if hasattr(mission, "highest_mineral_zone") and mission.highest_mineral_zone:
        hz = mission.highest_mineral_zone
        most_str = f"★ HIGH MINERAL: {hz['name'].upper()} ({hz['value']:.0f} MB)"
    elif hasattr(application, "most_resourceful_region"):
        m_name, m_yield = application.most_resourceful_region
        most_str = f"★ HIGH RESOURCE: {m_name.upper()} ({m_yield:.0f} MB)"
    else:
        most_str = "★ SURVEYING HIGH MINERAL DEPOSITS..."

    screen.blit(
        small_font.render(most_str, True, (255, 215, 0)),
        (stats_box.x + 10, stats_box.y + 27),
    )

    # 4 Telemetry Metric Cards
    card_w = (width - 28 - 8) // 2
    card_h = 66
    card_y1 = stats_y + 56
    card_y2 = card_y1 + 72

    def draw_card(cx, cy, label, val_str, accent, sub_str=None, progress=None):
        card = pygame.Rect(cx, cy, card_w, card_h)
        pygame.draw.rect(screen, theme.PANEL_RAISED, card, border_radius=8)
        pygame.draw.rect(screen, theme.PANEL_BORDER, card, 1, border_radius=8)
        screen.blit(label_font.render(label, True, theme.MUTED_TEXT), (card.x + 8, card.y + 6))
        screen.blit(value_font.render(val_str, True, accent), (card.x + 8, card.y + 22))
        if sub_str:
            screen.blit(small_font.render(sub_str, True, theme.TEXT), (card.x + 8, card.y + 44))
        if progress is not None:
            bar = pygame.Rect(card.x + 8, card.bottom - 7, card.width - 16, 4)
            pygame.draw.rect(screen, theme.PANEL_BORDER, bar, border_radius=2)
            fill = bar.copy()
            fill.width = int(bar.width * max(0.0, min(1.0, progress)))
            pygame.draw.rect(screen, accent, fill, border_radius=2)

    # Card 1: Rover Position
    r, c = _position(rover)
    draw_card(x + 14, card_y1, "ROVER POSITION", f"R {r:02d} / C {c:02d}", theme.ACCENT, sub_str="Orbital grid coords")

    # Card 2: Energy Reserve
    initial_energy = float(getattr(rover, "initial_energy", 100.0))
    rover_energy = float(getattr(rover, "energy", 100.0))
    energy_pct = rover_energy / max(1.0, initial_energy)
    draw_card(
        x + 14 + card_w + 8,
        card_y1,
        "ENERGY RESERVE",
        f"{rover_energy:.1f}%",
        theme.SUCCESS if rover_energy > 25 else theme.ERROR,
        sub_str=f"{rover_energy:.1f} / {initial_energy:.0f} kWh",
        progress=energy_pct,
    )

    # Card 3: Mineral Discoveries (Exact Mineral Identification, No "Nodes Detected")
    discovered_minerals = []
    if env and hasattr(env, "resources"):
        discovered_minerals = [res for res in env.resources if getattr(res, "discovered", False)]
    elif hasattr(rover, "known_map"):
        discovered_minerals = rover.known_map.known_resources()

    total_val = sum(r.value for r in discovered_minerals)
    gold_cnt = sum(1 for r in discovered_minerals if r.value >= 70)
    copper_cnt = sum(1 for r in discovered_minerals if 50 <= r.value < 70)
    titanium_cnt = sum(1 for r in discovered_minerals if 35 <= r.value < 50)
    other_cnt = sum(1 for r in discovered_minerals if r.value < 35)

    if gold_cnt > 0:
        main_min_txt = f"{len(discovered_minerals)} (★ GOLD)"
    elif discovered_minerals:
        main_min_txt = f"{len(discovered_minerals)} CATALOGED"
    else:
        main_min_txt = "SCANNING..."

    minerals_summary = f"Au:{gold_cnt} · Cu:{copper_cnt} · Ti:{titanium_cnt}"

    draw_card(
        x + 14,
        card_y2,
        "MINERAL EXPLORATION",
        main_min_txt,
        (255, 215, 0),
        sub_str=minerals_summary,
        progress=None,
    )

    # Card 4: Accumulated Science Value
    draw_card(
        x + 14 + card_w + 8,
        card_y2,
        "ACCUMULATED VALUE",
        f"{total_val:.0f} MB",
        (0, 230, 255),
        sub_str="Spectral data",
        progress=None,
    )

    if env is not None:
        total_free = env.free_cell_count()
        explored_free = rover.known_map.known_free_count()
        cov_pct = (100.0 * explored_free / total_free) if total_free > 0 else 0.0
        cov_str = f"Explored: {explored_free}/{total_free} ({cov_pct:.0f}%)"
    else:
        cov_str = "Explored: 1/0 (0%)"

    # Communication & Upload Status Section (Showing all 3 Comm Zones)
    sec_y = card_y2 + 74
    pygame.draw.line(screen, theme.PANEL_BORDER, (x + 14, sec_y), (x + width - 14, sec_y), 1)

    screen.blit(label_font.render("COMMUNICATION RELAY STATUS (3 ACTIVE)", True, theme.MUTED_TEXT), (x + 14, sec_y + 6))

    in_comm = rover.at_comm_zone() if hasattr(rover, "at_comm_zone") else False
    if env and env.zone_cells:
        cz_list = sorted(list(env.zone_cells))
        cz_list.sort(key=lambda z: abs(rover.position[0] - z[0]) + abs(rover.position[1] - z[1]))
        nearest_cz = cz_list[0]
        dist_cz = abs(rover.position[0] - nearest_cz[0]) + abs(rover.position[1] - nearest_cz[1])
        cz_info = f"3 RELAYS · NEAREST: R{nearest_cz[0]:02d},C{nearest_cz[1]:02d} ({dist_cz} STEPS)"
    else:
        cz_info = "3 RELAY STATIONS ACTIVE ON ORBITAL FREQ"

    if in_comm:
        comm_status_txt = "✓ IN COMM ZONE — TRANSMITTING PACKETS!"
        comm_color = (0, 240, 255)
    else:
        comm_status_txt = f"📡 {cz_info}"
        comm_color = (130, 215, 255)

    screen.blit(body_font.render(comm_status_txt, True, comm_color), (x + 14, sec_y + 22))

    uploaded_val = float(getattr(rover, "uploaded_data", 0.0))
    screen.blit(
        body_font.render(
            f"Transmitted: {uploaded_val:.1f} MB Science Data",
            True,
            (255, 215, 0),
        ),
        (x + 14, sec_y + 38),
    )
    cov_surf = small_font.render(cov_str, True, theme.MUTED_TEXT)
    screen.blit(
        cov_surf,
        (x + width - 14 - cov_surf.get_width(), sec_y + 38),
    )

    # -------------------------------------------------------------
    # MISSION CONTROL REAL-TIME OUTPUT SCREEN / CONSOLE TERMINAL
    # -------------------------------------------------------------
    out_y = sec_y + 56
    buttons_reserved_h = 96
    out_h = max(130, panel.bottom - out_y - buttons_reserved_h)
    out_box = pygame.Rect(x + 14, out_y, width - 28, out_h)

    # Styled high-tech terminal console box
    pygame.draw.rect(screen, (7, 13, 24), out_box, border_radius=8)
    pygame.draw.rect(screen, (0, 180, 230), out_box, 1, border_radius=8)

    # Console Header Bar
    console_bar = pygame.Rect(out_box.x, out_box.y, out_box.width, 24)
    pygame.draw.rect(screen, (14, 25, 42), console_bar, border_top_left_radius=8, border_top_right_radius=8)
    pygame.draw.line(screen, (0, 180, 230), console_bar.bottomleft, console_bar.bottomright, 1)

    screen.blit(
        label_font.render("▶ MISSION CONTROL OUTPUT", True, (0, 240, 255)),
        (console_bar.x + 8, console_bar.y + 4),
    )

    # Fullscreen terminal toggle button
    btn_toggle = get_fullscreen_toggle_rect(screen_w, screen_h, fullscreen_console=False)
    pygame.draw.rect(screen, (22, 40, 68), btn_toggle, border_radius=4)
    pygame.draw.rect(screen, (255, 215, 0), btn_toggle, 1, border_radius=4)
    screen.blit(
        small_font.render("⛶ FULL (TAB)", True, (255, 215, 0)),
        (btn_toggle.x + 8, btn_toggle.y + 3),
    )

    # Render multi-line activity log inside console terminal
    line_y = console_bar.bottom + 6
    line_h = 20
    max_visible_lines = max(3, (out_h - 32) // line_h)
    display_logs = logs[-max_visible_lines:] if logs else []

    if display_logs:
        for entry in display_logs:
            # Color-code critical mission messages
            if "If reached, mission failure may occur" in entry:
                entry_color = (255, 110, 90)  # Bright alert
                prefix = "⚠️ "
            elif "HIGH MINERAL" in entry:
                entry_color = (255, 225, 50)  # Gold highlight
                prefix = "★ "
            elif "Explored" in entry or "IDENTIFIED" in entry:
                entry_color = (100, 235, 255)  # Mineral cyan
                prefix = "💎 "
            elif "SUCCESS" in entry or "ACCOMPLISHED" in entry:
                entry_color = (90, 245, 170)   # Success green
                prefix = "✓ "
            else:
                entry_color = (220, 235, 250)
                prefix = "▸ "

            max_chars = max(20, (out_box.width - 24) // 8)
            rendered_entry = entry if len(entry) <= max_chars else entry[:max_chars - 3] + "..."
            line_text = console_font.render(f"{prefix}{rendered_entry}", True, entry_color)
            screen.blit(line_text, (out_box.x + 8, line_y))
            line_y += line_h
    else:
        screen.blit(
            console_font.render("▸ System online. Awaiting START...", True, theme.MUTED_TEXT),
            (out_box.x + 8, line_y),
        )
