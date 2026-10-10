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


def draw_dashboard(screen, application, simulation_running=False, environment=None, time_sec=0.0):
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
        state_str = "PAUSED" if not simulation_running else "RUNNING"
        state_name = "IDLE"
        reg_name = "Region 1: Ares Planitia"
        sess_cnt, succ_cnt, fail_cnt, useful_cnt = 1, 0, 0, 0
        is_running = simulation_running
        logs = []

    title_font = pygame.font.SysFont("arial", 21, bold=True)
    label_font = pygame.font.SysFont("arial", 12, bold=True)
    value_font = pygame.font.SysFont("arial", 19, bold=True)
    body_font = pygame.font.SysFont("arial", 13)
    small_font = pygame.font.SysFont("arial", 12)

    x, y = 720, 100
    width = 520
    panel = pygame.Rect(x, y, width, 520)
    
    pygame.draw.rect(screen, theme.PANEL, panel, border_radius=16)
    pygame.draw.rect(screen, theme.PANEL_BORDER, panel, 1, border_radius=16)

    # Title & Region Header
    screen.blit(title_font.render("3D ROVER TELEMETRY & CONTROL", True, theme.TEXT), (x + 18, y + 14))
    screen.blit(
        small_font.render(f"CURRENT TARGET AREA: {reg_name.upper()}", True, theme.ACCENT),
        (x + 18, y + 40),
    )

    # State Status Badge
    if state_name == "SUCCESS":
        status_color = theme.SUCCESS
    elif state_name == "FAILURE":
        status_color = theme.ERROR
    elif is_running:
        status_color = theme.ACCENT
    else:
        status_color = theme.WARNING

    status_rect = pygame.Rect(x + width - 210, y + 14, 195, 32)
    pygame.draw.rect(screen, theme.PANEL_RAISED, status_rect, border_radius=16)
    pygame.draw.rect(screen, status_color, status_rect, 1, border_radius=16)
    pygame.draw.circle(screen, status_color, (status_rect.x + 14, status_rect.centery), 4)
    screen.blit(
        label_font.render(state_str[:22], True, status_color),
        (status_rect.x + 24, status_rect.y + 8),
    )

    # Session Stats Banner
    stats_y = y + 68
    stats_box = pygame.Rect(x + 18, stats_y, width - 36, 55)
    pygame.draw.rect(screen, theme.PANEL_RAISED, stats_box, border_radius=10)
    pygame.draw.rect(screen, theme.PANEL_BORDER, stats_box, 1, border_radius=10)

    col1 = f"SESSION: {sess_cnt}"
    col2 = f"SUCCESS: {succ_cnt}"
    col4 = f"USEFUL REGIONS: {useful_cnt}"

    screen.blit(label_font.render(col1, True, theme.TEXT), (stats_box.x + 16, stats_box.y + 10))
    screen.blit(label_font.render(col2, True, theme.SUCCESS), (stats_box.x + 140, stats_box.y + 10))
    screen.blit(label_font.render(col4, True, (190, 140, 255)), (stats_box.x + 270, stats_box.y + 10))

    if hasattr(application, "most_resourceful_region"):
        m_name, m_yield = application.most_resourceful_region
        most_str = f"★ MOST RESOURCEFUL REGION: {m_name.upper()} ({m_yield:.0f} MB)"
    else:
        most_str = "★ MOST RESOURCEFUL REGION: REGION 1: ARES PLANITIA (0 MB)"

    screen.blit(
        small_font.render(most_str, True, (255, 215, 0)),
        (stats_box.x + 16, stats_box.y + 30),
    )

    # 4 Telemetry Metric Cards
    card_w = (width - 48) // 2
    card_h = 74
    card_y1 = stats_y + 68
    card_y2 = card_y1 + 82

    def draw_card(cx, cy, label, val_str, accent, sub_str=None, progress=None):
        card = pygame.Rect(cx, cy, card_w, card_h)
        pygame.draw.rect(screen, theme.PANEL_RAISED, card, border_radius=10)
        pygame.draw.rect(screen, theme.PANEL_BORDER, card, 1, border_radius=10)
        screen.blit(label_font.render(label, True, theme.MUTED_TEXT), (card.x + 12, card.y + 8))
        screen.blit(value_font.render(val_str, True, accent), (card.x + 12, card.y + 26))
        if sub_str:
            screen.blit(small_font.render(sub_str, True, theme.TEXT), (card.x + 12, card.y + 50))
        if progress is not None:
            bar = pygame.Rect(card.x + 12, card.bottom - 8, card.width - 24, 4)
            pygame.draw.rect(screen, theme.PANEL_BORDER, bar, border_radius=2)
            fill = bar.copy()
            fill.width = int(bar.width * max(0.0, min(1.0, progress)))
            pygame.draw.rect(screen, accent, fill, border_radius=2)

    # Card 1: Rover Position
    r, c = _position(rover)
    draw_card(x + 18, card_y1, "ROVER POSITION (SATELLITE)", f"ROW {r:02d} / COL {c:02d}", theme.ACCENT)

    # Card 2: Energy
    initial_energy = float(getattr(rover, "initial_energy", 100.0))
    rover_energy = float(getattr(rover, "energy", 100.0))
    energy_pct = rover_energy / max(1.0, initial_energy)
    draw_card(
        x + 30 + card_w,
        card_y1,
        "ENERGY RESERVE",
        f"{rover_energy:.1f} / {initial_energy:.0f}",
        theme.SUCCESS if rover_energy > 25 else theme.ERROR,
        progress=energy_pct,
    )

    # Card 3 & 4: Mineral Spectrum Breakdown & Total Scientific Value
    known_res = rover.known_map.known_resources() if hasattr(rover, "known_map") else []
    total_val = sum(r.value for r in known_res)
    
    gold_cnt = sum(1 for r in known_res if r.value >= 70)
    copper_cnt = sum(1 for r in known_res if 50 <= r.value < 70)
    titanium_cnt = sum(1 for r in known_res if 30 <= r.value < 50)
    lithium_cnt = sum(1 for r in known_res if r.value < 30)

    minerals_summary = f"Gold:{gold_cnt} · Cu:{copper_cnt} · Ti:{titanium_cnt} · Li:{lithium_cnt}"

    draw_card(
        x + 18,
        card_y2,
        "MINERALS IDENTIFIED",
        f"{len(known_res)} NODES DETECTED",
        (255, 215, 0),
        sub_str=minerals_summary,
        progress=None,
    )

    draw_card(
        x + 30 + card_w,
        card_y2,
        "ACCUMULATED SCI VALUE",
        f"{total_val:.0f} MB VALUE",
        (0, 230, 255),
        sub_str="High-yield spectrograph data",
        progress=None,
    )

    if env is not None:
        total_free = env.free_cell_count()
        explored_free = rover.known_map.known_free_count()
        cov_pct = (100.0 * explored_free / total_free) if total_free > 0 else 0.0
        cov_str = f"Explored: {explored_free}/{total_free} ({cov_pct:.0f}%)"
    else:
        cov_str = "0% COVERAGE"

    # Science & Comm Zone Upload Section
    sec_y = card_y2 + 82
    pygame.draw.line(screen, theme.PANEL_BORDER, (x + 18, sec_y), (x + width - 18, sec_y), 1)

    screen.blit(label_font.render("COMMUNICATION & UPLOAD STATUS", True, theme.MUTED_TEXT), (x + 18, sec_y + 10))
    
    in_comm = rover.at_comm_zone() if hasattr(rover, "at_comm_zone") else False
    if env and env.zone_cells:
        cz_list = sorted(list(env.zone_cells))
        cz_pos = cz_list[0]
        dist_cz = abs(rover.position[0] - cz_pos[0]) + abs(rover.position[1] - cz_pos[1])
        cz_info = f"COMM TOWER: ROW {cz_pos[0]:02d} / COL {cz_pos[1]:02d} ({dist_cz} STEPS AWAY)"
    else:
        cz_info = "COMM TOWER: SCANNING SATELLITE FREQUENCY"

    if in_comm:
        comm_status_txt = f"✓ STANDING IN COMM ZONE — TRANSMITTING PACKETS!"
        comm_color = (0, 230, 255)
    else:
        comm_status_txt = f"📡 {cz_info}"
        comm_color = (140, 210, 255)

    screen.blit(body_font.render(comm_status_txt, True, comm_color), (x + 18, sec_y + 30))

    uploaded_val = float(getattr(rover, "uploaded_data", 0.0))
    screen.blit(
        body_font.render(
            f"Total Transmitted: {uploaded_val:.1f} MB Science Data Packets",
            True,
            (255, 215, 0),
        ),
        (x + 18, sec_y + 52),
    )
    screen.blit(
        small_font.render(cov_str, True, theme.MUTED_TEXT),
        (x + 350, sec_y + 52),
    )

    # Activity Log
    log_y = sec_y + 80
    pygame.draw.line(screen, theme.PANEL_BORDER, (x + 18, log_y), (x + width - 18, log_y), 1)
    screen.blit(label_font.render("REAL-TIME MISSION ACTIVITY LOG", True, theme.MUTED_TEXT), (x + 18, log_y + 10))

    if logs:
        for idx, entry in enumerate(logs[-4:]):
            ly = log_y + 30 + idx * 20
            screen.blit(small_font.render(f"▸ {entry}", True, theme.TEXT), (x + 18, ly))
    else:
        screen.blit(small_font.render("Awaiting START command to initialize mission loop...", True, theme.MUTED_TEXT), (x + 18, log_y + 30))
