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
                   carried_data=None, target_value=None, mission_state=None):
    title_font = pygame.font.SysFont("arial", 22, bold=True)
    font = pygame.font.SysFont("arial", 16)
    x, y = theme.PANEL_LEFT, 90
    screen.blit(title_font.render("ROVER DASHBOARD", True, theme.ACCENT), (x, y))

    row, col = _position(rover_state)
    energy = float(getattr(rover_state, "energy", 0.0))
    status = "RUNNING" if simulation_running else "PAUSED"
    status_color = theme.SUCCESS if simulation_running else theme.WARNING
    if mission_state is None:
        mission_state = getattr(rover_state, "mission_state", status)

    lines = [
        (f"Position: ({row}, {col})", theme.TEXT),
        (f"Energy: {energy:.1f}", theme.TEXT),
        (f"Status: {status}", status_color),
        (f"Mission: {mission_state}", theme.TEXT),
        (f"Target: {target if target is not None else '—'}", theme.TEXT),
        (f"Moves: {moves}", theme.TEXT),
        (f"Replans: {replans}", theme.TEXT),
    ]
    if explored_count is not None and total_cells:
        coverage = 100.0 * explored_count / total_cells
        lines.append((f"Explored: {explored_count}/{total_cells} ({coverage:.0f}%)", theme.TEXT))
    if carried_data is None:
        carried_data = getattr(rover_state, "carried_data", 0.0)
    lines.append((f"Carried data: {float(carried_data):.1f} MB", theme.TEXT))
    if target_value is not None:
        lines.append((f"Target value: {float(target_value):.1f}", theme.TARGET))

    for index, (message, color) in enumerate(lines):
        screen.blit(font.render(message, True, color), (x, y + 42 + index * 27))

    legend_y = y + 42 + len(lines) * 27 + 8
    legend = [
        (theme.ROVER, "Rover"),
        (theme.OBSTACLE, "Known obstacle"),
        (theme.RESOURCE, "Discovered resource"),
        (theme.BASE, "Base"),
        (theme.ROUTE, "Planned route"),
    ]
    for i, (color, label) in enumerate(legend):
        col = i % 2
        row_idx = i // 2
        px, py = x + col * 145, legend_y + row_idx * 23
        pygame.draw.rect(screen, color, pygame.Rect(px, py + 3, 12, 12), border_radius=3)
        screen.blit(font.render(label, True, theme.MUTED_TEXT), (px + 19, py))
