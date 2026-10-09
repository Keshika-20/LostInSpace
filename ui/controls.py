"""Stage 1 event handling. Simulation controls are added in Stage 2."""

import pygame


def handle_events(events=None):
    """Return True if the app should quit; do not mutate simulation state."""
    if events is None:
        events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            return True

    return False
