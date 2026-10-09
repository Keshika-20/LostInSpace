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


def draw_dashboard(screen, rover_state, simulation_running, target=None, moves=0,
                   explored_count=None, total_cells=None, replans=0,
                   carried_data=None, target_value=None, mission_state=None,
                   environment=None, capacity=10.0):
    title_font = pygame.font.SysFont("arial", 21, bold=True)
    label_font = pygame.font.SysFont("arial", 12, bold=True)
    value_font = pygame.font.SysFont("arial", 20, bold=True)
    body_font = pygame.font.SysFont("arial", 14)
    small_font = pygame.font.SysFont("arial", 13)
    x, y = theme.PANEL_LEFT, 110
    width = max(330, screen.get_width() - x - 32)
    panel = pygame.Rect(x - 18, y - 8, width + 36, 500)
    pygame.draw.rect(screen, theme.PANEL, panel, border_radius=16)
    pygame.draw.rect(screen, theme.PANEL_BORDER, panel, 1, border_radius=16)
    screen.blit(title_font.render("ROVER SYSTEMS", True, theme.TEXT), (x, y + 8))
    screen.blit(
        small_font.render("LIVE TELEMETRY  /  SURFACE UNIT 01", True, theme.MUTED_TEXT),
        (x, y + 36),
    )

    row, col = _position(rover_state)
    energy = float(getattr(rover_state, "energy", 0.0))
    status = "RUNNING" if simulation_running else "PAUSED"
    status_color = theme.SUCCESS if simulation_running else theme.WARNING
    if mission_state is None:
        mission_state = getattr(rover_state, "mission_state", status)
    if environment is not None:
        explored_count = rover_state.known_map.known_free_count()
        total_cells = environment.free_cell_count()
    if carried_data is None:
        carried_data = getattr(rover_state, "carried_data", 0.0)
    carried_data = float(carried_data)
    coverage = (
        100.0 * explored_count / total_cells
        if explored_count is not None and total_cells
        else 0.0
    )

    status_rect = pygame.Rect(x + width - 132, y + 8, 120, 30)
    pygame.draw.rect(screen, theme.PANEL_RAISED, status_rect, border_radius=15)
    pygame.draw.circle(screen, status_color, (status_rect.x + 16, status_rect.centery), 4)
    screen.blit(
        label_font.render(status, True, status_color),
        (status_rect.x + 28, status_rect.y + 9),
    )

    def metric_card(card_x, card_y, label, value, accent, progress=None):
        card = pygame.Rect(card_x, card_y, (width - 12) // 2, 76)
        pygame.draw.rect(screen, theme.PANEL_RAISED, card, border_radius=10)
        pygame.draw.rect(screen, theme.PANEL_BORDER, card, 1, border_radius=10)
        screen.blit(label_font.render(label, True, theme.MUTED_TEXT), (card.x + 12, card.y + 10))
        screen.blit(value_font.render(value, True, accent), (card.x + 12, card.y + 31))
        if progress is not None:
            bar = pygame.Rect(card.x + 12, card.bottom - 10, card.width - 24, 4)
            pygame.draw.rect(screen, theme.PANEL_BORDER, bar, border_radius=2)
            fill = bar.copy()
            fill.width = int(bar.width * max(0.0, min(1.0, progress)))
            pygame.draw.rect(screen, accent, fill, border_radius=2)

    gap = 12
    card_width = (width - gap) // 2
    metric_card(x, y + 68, "ROVER POSITION", f"{row:02d}  /  {col:02d}", theme.ACCENT)
    metric_card(
        x + card_width + gap,
        y + 68,
        "ENERGY RESERVE",
        f"{energy:.1f} / {float(getattr(rover_state, 'initial_energy', 100.0)):.1f}",
        theme.SUCCESS if energy > 25 else theme.ERROR,
        energy / max(1.0, float(getattr(rover_state, "initial_energy", 100.0))),
    )
    metric_card(
        x,
        y + 154,
        "CARGO MANIFEST",
        f"{carried_data:.1f} / {capacity:.1f} MB",
        theme.RESOURCE,
        carried_data / max(1.0, capacity),
    )
    metric_card(
        x + card_width + gap,
        y + 154,
        "TERRAIN MAPPED",
        f"{coverage:.0f}%",
        theme.ACCENT,
        coverage / 100.0,
    )

    if environment is not None:
        known_resources = rover_state.known_map.known_resources()
        discovered = len(rover_state.known_map.known_resources())
        collected = sum(resource.collected for resource in environment.resources)
        remaining = sum(not resource.collected for resource in environment.resources)
    else:
        known_resources = []
        discovered = 0
        collected = 0
        remaining = 0
    section_y = y + 250
    pygame.draw.line(screen, theme.PANEL_BORDER, (x, section_y), (x + width, section_y), 1)
    screen.blit(
        label_font.render("SCIENCE RESOURCES", True, theme.MUTED_TEXT),
        (x, section_y + 14),
    )
    screen.blit(
        body_font.render(
            f"Detected  {discovered}     Secured  {collected}     Remaining  {remaining}",
            True,
            theme.TEXT,
        ),
        (x, section_y + 38),
    )
    current_resource = (
        environment.resource_at(rover_state.position)
        if environment is not None
        else None
    )
    detail_y = section_y + 72
    if current_resource is not None and current_resource.discovered:
        detail = (
            f"Resource under rover  ·  {current_resource.value:.0f} science  ·  "
            f"{current_resource.data_size:.1f} MB"
        )
        detail_color = theme.RESOURCE
    elif target is not None:
        detail = f"Route target  ·  {target}"
        detail_color = theme.TARGET
    elif known_resources:
        detail = f"{discovered} sites identified  ·  Select ROUTE for a safe path preview."
        detail_color = theme.RESOURCE
    else:
        detail = "Move into unexplored terrain to reveal resource sites."
        detail_color = theme.MUTED_TEXT
    screen.blit(body_font.render(detail, True, detail_color), (x, detail_y))

    if explored_count is not None and total_cells is not None:
        screen.blit(
            small_font.render(
                f"Explored: {explored_count}/{total_cells} ({coverage:.0f}%)",
                True,
                theme.MUTED_TEXT,
            ),
            (x, detail_y + 28),
        )
    screen.blit(
        small_font.render(
            f"Moves {moves}   ·   Mission {mission_state}   ·   Target "
            f"{target if target is not None else '—'}   ·   Replans {replans}",
            True,
            theme.MUTED_TEXT,
        ),
        (x, detail_y + 48),
    )
    if target_value is not None:
        screen.blit(
            small_font.render(f"Target science value  {target_value:.0f}", True, theme.TARGET),
            (x, detail_y + 66),
        )
    sites_y = detail_y + 88
    pygame.draw.line(screen, theme.PANEL_BORDER, (x, sites_y), (x + width, sites_y), 1)
    screen.blit(
        label_font.render("KNOWN SITES", True, theme.MUTED_TEXT),
        (x, sites_y + 10),
    )
    if known_resources:
        for index, resource in enumerate(known_resources[:2]):
            site_y = sites_y + 30 + index * 20
            screen.blit(
                small_font.render(
                    f"SITE {resource.position[0]:02d}/{resource.position[1]:02d}",
                    True,
                    theme.TEXT,
                ),
                (x, site_y),
            )
            screen.blit(
                small_font.render(
                    f"{resource.value:.0f} SCI  ·  {resource.data_size:.1f} MB",
                    True,
                    theme.RESOURCE,
                ),
                (x + min(250, width // 2), site_y),
            )
    else:
        screen.blit(
            small_font.render("No sites detected in the current scan.", True, theme.MUTED_TEXT),
            (x, sites_y + 30),
        )
