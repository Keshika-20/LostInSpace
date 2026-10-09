
import pygame


def draw_dashboard(screen, rover_state, simulation_running):
    title_font = pygame.font.SysFont("arial", 25, bold=True)
    font = pygame.font.SysFont("arial", 19)

    x = 620
    y = 100

    title = title_font.render("MISSION DASHBOARD", True, (115, 205, 255))
    screen.blit(title, (x, y))

    position_text = font.render(
        f"Rover position: {rover_state.position}", True, (240, 245, 255)
    )
    energy_text = font.render(
        f"Energy: {rover_state.energy:.0f}%", True, (240, 245, 255)
    )

    status = "RUNNING" if simulation_running else "STOPPED"
    status_color = (100, 230, 150) if simulation_running else (255, 190, 100)
    status_text = font.render(f"Status: {status}", True, status_color)

    screen.blit(position_text, (x, y + 55))
    screen.blit(energy_text, (x, y + 95))
    screen.blit(status_text, (x, y + 135))