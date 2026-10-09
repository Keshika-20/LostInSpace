import pygame
from ui import theme


def get_position(rover_state):
    position = getattr(rover_state, "position", rover_state)
    if isinstance(position, tuple) and len(position) == 2:
        return int(position[0]), int(position[1])
    if hasattr(position, "row") and hasattr(position, "col"):
        return int(position.row), int(position.col)
    if hasattr(position, "x") and hasattr(position, "y"):
        return int(position.y), int(position.x)
    raise TypeError("Unsupported rover position format")


def _resource_items(resources):
    if resources is None:
        return []
    if isinstance(resources, dict):
        items = []
        for pos, value in resources.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("position", pos)
            else:
                item = {"position": pos, "value": getattr(value, "value", 0),
                        "data_size": getattr(value, "data_size", 0),
                        "discovered": getattr(value, "discovered", True),
                        "collected": getattr(value, "collected", False)}
            items.append(item)
        return items
    result = []
    for resource in resources:
        if isinstance(resource, dict):
            result.append(resource)
        else:
            result.append({
                "position": getattr(resource, "position", None),
                "value": getattr(resource, "value", 0),
                "data_size": getattr(resource, "data_size", 0),
                "discovered": getattr(resource, "discovered", True),
                "collected": getattr(resource, "collected", False),
            })
    return result


def _draw_stars(screen, width, height):
    """Deterministic starfield so the space background feels consistent."""
    import random
    rng = random.Random(19)
    for _ in range(115):
        x, y = rng.randrange(width), rng.randrange(height)
        radius = rng.choice((1, 1, 1, 2))
        color = rng.choice(((90, 122, 160), (142, 169, 204), (210, 226, 245)))
        pygame.draw.circle(screen, color, (x, y), radius)


def _draw_rover(screen, center_point, cell_size):
    """Small top-down rover with chassis, wheels, solar panel and antenna."""
    cx, cy = center_point
    scale = max(0.62, min(1.0, cell_size / 48))
    w, h = int(24 * scale), int(19 * scale)
    # dark shadow
    pygame.draw.ellipse(screen, (8, 12, 20), (cx-w//2-2, cy-h//2+5, w+6, h+5))
    # six chunky wheels
    wheel_w, wheel_h = max(3, int(5*scale)), max(5, int(9*scale))
    for dx in (-w//2, w//2-wheel_w):
        for dy in (-h//2, 0, h//2-wheel_h):
            pygame.draw.rect(screen, (27, 35, 46), (cx+dx, cy+dy, wheel_w, wheel_h), border_radius=2)
            pygame.draw.rect(screen, (123, 139, 153), (cx+dx, cy+dy, wheel_w, wheel_h), 1, border_radius=2)
    body = pygame.Rect(cx-int(9*scale), cy-int(8*scale), int(18*scale), int(16*scale))
    pygame.draw.rect(screen, (205, 143, 58), body, border_radius=3)
    pygame.draw.rect(screen, theme.ROVER_OUTLINE, body, max(1, int(scale)), border_radius=3)
    # blue solar/equipment deck
    panel = pygame.Rect(cx-int(6*scale), cy-int(5*scale), int(12*scale), int(7*scale))
    pygame.draw.rect(screen, (42, 103, 145), panel, border_radius=1)
    pygame.draw.line(screen, (111, 211, 246), (panel.centerx, panel.top), (panel.centerx, panel.bottom), 1)
    pygame.draw.line(screen, (111, 211, 246), (panel.left, panel.centery), (panel.right, panel.centery), 1)
    # forward sensor and antenna
    pygame.draw.circle(screen, (255, 92, 83), (cx, cy-int(9*scale)), max(2, int(2*scale)))
    pygame.draw.line(screen, (215, 225, 235), (cx+int(7*scale), cy-int(4*scale)), (cx+int(10*scale), cy-int(10*scale)), max(1, int(scale)))
    pygame.draw.circle(screen, (106, 224, 255), (cx+int(10*scale), cy-int(10*scale)), max(2, int(2*scale)))


def draw_map(screen, rover_state, rows=10, cols=10, obstacles=None,
             known_map=None, route=None, target=None, resources=None, base=(0, 0)):
    """Draw known terrain, route, target, resources and rover.

    known_map can be a mapping from (row, col) to 'unknown'/'free'/'obstacle'/'base',
    or a collection of known/explored coordinates. If omitted, cells are known.
    Returns the rectangle occupied by the grid.
    """
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be positive")
    obstacles = set(obstacles or ())
    route = list(route or ())
    cell_size = min(theme.CELL_SIZE, 480 // max(rows, cols))
    left, top = theme.GRID_LEFT, theme.GRID_TOP
    _draw_stars(screen, screen.get_width(), screen.get_height())

    def in_bounds(pos):
        return isinstance(pos, (tuple, list)) and len(pos) == 2 and 0 <= pos[0] < rows and 0 <= pos[1] < cols

    def center(pos):
        r, c = pos
        return (left + int(c) * cell_size + cell_size // 2,
                top + int(r) * cell_size + cell_size // 2)

    known_status = {}
    if isinstance(known_map, dict):
        known_status = known_map
    elif known_map is not None:
        known_status = {tuple(pos): "free" for pos in known_map}

    for row in range(rows):
        for col in range(cols):
            pos = (row, col)
            status = known_status.get(pos, "free" if known_map is None else "unknown")
            if status in ("unknown", None):
                color = theme.GRID_UNKNOWN
            elif status == "obstacle" or (pos in obstacles and known_map is None):
                color = theme.OBSTACLE
            elif status == "base" or pos == base:
                color = theme.BASE
            elif status == "explored":
                color = theme.GRID_EXPLORED
            else:
                color = theme.GRID_CELL
            rect = pygame.Rect(left + col * cell_size, top + row * cell_size,
                               cell_size, cell_size)
            pygame.draw.rect(screen, color, rect)
            # Alien regolith: subtle mineral flecks and crater rings, not flat tiles.
            if status not in ("unknown", None):
                seed = row * 137 + col * 71 + 23
                crater_x = rect.x + 8 + (seed % max(1, cell_size - 16))
                crater_y = rect.y + 8 + ((seed // 7) % max(1, cell_size - 16))
                crater_r = max(3, cell_size // 7)
                pygame.draw.circle(screen, (47, 52, 62), (crater_x, crater_y), crater_r)
                pygame.draw.arc(screen, (113, 113, 118), pygame.Rect(crater_x-crater_r, crater_y-crater_r, crater_r*2, crater_r*2), 0.15, 2.7, 1)
                for k in range(3):
                    fx = rect.x + ((seed * (k+3)) % max(1, cell_size-5)) + 2
                    fy = rect.y + ((seed * (k+5)) % max(1, cell_size-5)) + 2
                    pygame.draw.circle(screen, (111, 104, 94), (fx, fy), 1)
            pygame.draw.rect(screen, theme.GRID_LINE, rect, 1)

    valid_route = [tuple(p) for p in route if in_bounds(p)]
    if len(valid_route) > 1:
        pygame.draw.lines(screen, theme.ROUTE, False,
                          [center(p) for p in valid_route], max(2, cell_size // 9))

    if base is not None and in_bounds(base):
        pygame.draw.rect(screen, theme.BASE,
                         pygame.Rect(left + base[1]*cell_size + cell_size//4,
                                     top + base[0]*cell_size + cell_size//4,
                                     cell_size//2, cell_size//2), border_radius=3)

    for resource in _resource_items(resources):
        pos = resource.get("position")
        if not in_bounds(pos) or not resource.get("discovered", True):
            continue
        pos = tuple(pos)
        color = theme.RESOURCE_COLLECTED if resource.get("collected", False) else theme.RESOURCE
        pygame.draw.circle(screen, color, center(pos), max(5, cell_size // 5))
        pygame.draw.circle(screen, theme.TEXT, center(pos), max(5, cell_size // 5), 1)

    if target is not None and in_bounds(target):
        pygame.draw.circle(screen, theme.TARGET, center(target), max(7, cell_size // 3), 3)

    rover_row, rover_col = get_position(rover_state)
    if 0 <= rover_row < rows and 0 <= rover_col < cols:
        rover_center = center((rover_row, rover_col))
        _draw_rover(screen, rover_center, cell_size)

    return pygame.Rect(left, top, cols * cell_size, rows * cell_size)
