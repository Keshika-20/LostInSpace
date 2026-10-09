"""Draw the Stage 1 static grid and placeholder rover marker."""

import pygame
from ui import theme


def draw_map(screen, rover_position=(0, 0), rows=10, cols=10):
    """Draw a fixed grid and a rover marker at (row, col)."""
    cell_size = min(theme.CELL_SIZE, 480 // max(rows, cols))
    grid_width = cols * cell_size
    grid_height = rows * cell_size
    left = theme.GRID_LEFT
    top = theme.GRID_TOP

    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(
                left + col * cell_size,
                top + row * cell_size,
                cell_size,
                cell_size,
            )
            pygame.draw.rect(screen, theme.GRID_CELL, rect)
            pygame.draw.rect(screen, theme.GRID_LINE, rect, 1)

    rover_row, rover_col = rover_position
    if 0 <= rover_row < rows and 0 <= rover_col < cols:
        center = (
            left + rover_col * cell_size + cell_size // 2,
            top + rover_row * cell_size + cell_size // 2,
        )
        radius = max(8, cell_size // 3)
        pygame.draw.circle(screen, theme.ROVER, center, radius)
        pygame.draw.circle(screen, theme.ROVER_OUTLINE, center, radius, 2)

    return pygame.Rect(left, top, grid_width, grid_height)
