"""Standalone Person 2 UI demo covering visual features from Stages 1–5.

Movement and map discovery here are demo harness behavior only. In the team
repository, the simulation and mission controller must own those decisions.
"""
import pygame
from ui import theme
from ui.controls import Controls
from ui.dashboard import draw_dashboard
from ui.map_renderer import draw_map


class DemoRoverState:
    def __init__(self):
        self.position = (0, 0)
        self.energy = 100.0
        self.carried_data = 0.0
        self.mission_state = "EXPLORING"


class DemoResource:
    def __init__(self, position, value, data_size, discovered=False, collected=False):
        self.position = position
        self.value = value
        self.data_size = data_size
        self.discovered = discovered
        self.collected = collected


def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("Lost in Space — Person 2 UI Demo (Stages 1–5)")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("arial", 27, bold=True)
    small_font = pygame.font.SysFont("arial", 14)
    controls = Controls()
    rover = DemoRoverState()
    rows = cols = 10
    base = (0, 0)
    obstacles = {(2, 3), (3, 3), (4, 3), (5, 6), (6, 6), (7, 6)}
    target = (8, 8)
    true_resources = [
        DemoResource((4, 6), 9.5, 4.0),
        DemoResource((8, 3), 6.0, 2.5),
    ]
    explored = {(r, c) for r in range(3) for c in range(3)}
    route = []
    simulation_running = False
    moves = replans = 0
    move_timer = 0
    move_delay = 350
    running = True

    def observe(pos):
        r, c = pos
        for rr in range(max(0, r-1), min(rows, r+2)):
            for cc in range(max(0, c-1), min(cols, c+2)):
                explored.add((rr, cc))
        for resource in true_resources:
            if abs(resource.position[0] - r) <= 1 and abs(resource.position[1] - c) <= 1:
                resource.discovered = True

    def make_demo_route(start, goal):
        # Display-only deterministic route; not the project A* implementation.
        r, c = start
        result = [(r, c)]
        while c != goal[1]:
            step = c + (1 if goal[1] > c else -1)
            if (r, step) in obstacles:
                break
            c = step
            result.append((r, c))
        while r != goal[0]:
            step = r + (1 if goal[0] > r else -1)
            if (step, c) in obstacles:
                break
            r = step
            result.append((r, c))
        return result

    observe(rover.position)
    route = make_demo_route(rover.position, target)

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                command = controls.handle_event(event)
                if command == "START":
                    simulation_running = True
                    rover.mission_state = "TRAVELLING"
                elif command == "PAUSE":
                    simulation_running = False
                    rover.mission_state = "EXPLORING"
                elif command == "RESET":
                    rover = DemoRoverState()
                    explored.clear()
                    observe(rover.position)
                    for resource in true_resources:
                        resource.discovered = False
                        resource.collected = False
                    simulation_running = False
                    moves = replans = 0
                    move_timer = 0
                    route = make_demo_route(rover.position, target)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                    # Visualization aid: reveal all cells, not a mission action.
                    explored.update((r, c) for r in range(rows) for c in range(cols))
                    for resource in true_resources:
                        resource.discovered = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    replans += 1
                    route = make_demo_route(rover.position, target)

            if simulation_running:
                move_timer += clock.get_time()
                if move_timer >= move_delay:
                    move_timer = 0
                    r, c = rover.position
                    candidates = []
                    if c < target[1]: candidates.append((r, c+1))
                    if r < target[0]: candidates.append((r+1, c))
                    if c > target[1]: candidates.append((r, c-1))
                    if r > target[0]: candidates.append((r-1, c))
                    next_pos = next((p for p in candidates if p not in obstacles and p[0] < rows and p[1] < cols), None)
                    if next_pos is not None and rover.energy >= 1:
                        rover.position = next_pos
                        rover.energy -= 1
                        moves += 1
                        observe(next_pos)
                        route = make_demo_route(rover.position, target)
                        # Demo collection: only discovered resource at current cell.
                        for resource in true_resources:
                            if resource.discovered and not resource.collected and resource.position == rover.position:
                                resource.collected = True
                                rover.carried_data += resource.data_size
                    else:
                        simulation_running = False
                        replans += 1
                    if rover.position == target or rover.energy <= 0:
                        simulation_running = False
                        rover.mission_state = "COMPLETED" if rover.position == target else "FAILED"

            screen.fill(theme.BACKGROUND)
            screen.blit(title_font.render("LOST IN SPACE", True, theme.ACCENT), (50, 24))
            screen.blit(small_font.render("Stages 1–5 UI demo • N: reveal map • R: refresh route/replan indicator", True, theme.MUTED_TEXT), (50, 54))
            known_map = {}
            for r in range(rows):
                for c in range(cols):
                    pos = (r, c)
                    if pos in obstacles and pos in explored:
                        known_map[pos] = "obstacle"
                    elif pos == base:
                        known_map[pos] = "base"
                    elif pos in explored:
                        known_map[pos] = "free"
                    else:
                        known_map[pos] = "unknown"
            visible_resources = [r for r in true_resources if r.discovered]
            target_resource = next((r for r in visible_resources if not r.collected), None)
            target_value = target_resource.value if target_resource else None
            draw_map(screen, rover, rows, cols, obstacles=obstacles,
                     known_map=known_map, route=route, target=target,
                     resources=visible_resources, base=base)
            draw_dashboard(screen, rover, simulation_running, target=target, moves=moves,
                           explored_count=len(explored), total_cells=rows*cols,
                           replans=replans, carried_data=rover.carried_data,
                           target_value=target_value, mission_state=rover.mission_state)
            controls.draw(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
