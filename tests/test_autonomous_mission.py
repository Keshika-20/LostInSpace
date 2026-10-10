"""Unit tests for Autonomous Mission Controller, Comm Zone Uploads, and Multi-Region Exploration."""

import pytest
from application_controller import ApplicationController
from mission.autonomous_mission import MissionState
from simulation.renderer_3d import Camera3D


def test_camera_3d_projection():
    camera = Camera3D(target_pos=(5.0, 0.0, 5.0), distance=10.0, yaw=0.0, pitch=0.0)
    sx, sy, depth = camera.project(5.0, 0.0, 5.0)
    assert isinstance(sx, int)
    assert isinstance(sy, int)
    assert depth > 0.0


def test_autonomous_mission_flow():
    app = ApplicationController(seed=2025)
    app.start_autonomous_mission()

    assert app.is_running is True
    assert app.autonomous_mission.state == MissionState.EXPLORING

    # Tick simulation steps until mission reaches terminal state or step limit
    max_steps = 300
    steps = 0
    while app.is_running and steps < max_steps:
        app.update_tick()
        steps += 1

    assert app.is_running is False
    assert app.autonomous_mission.state in (MissionState.SUCCESS, MissionState.FAILURE)
    assert app.session_count == 1
    assert len(app.session_history) == 1


def test_multi_region_exploration_persistence():
    app = ApplicationController(seed=2025)
    
    # Observe initial terrain
    app.rover.observe()
    initial_explored = app.rover.known_map.explored_count()
    assert initial_explored > 0

    # Advance to next region
    app.explore_next_region()
    assert app.region_index == 1
    assert app.session_count == 2
    # Preserves previously explored cells
    assert app.rover.known_map.explored_count() >= initial_explored
    assert app.rover.position == (0, 0)
    assert app.rover.energy == app.rover.initial_energy


def test_comm_zone_placement():
    app = ApplicationController(seed=2025)
    assert len(app.environment.zone_cells) >= 3


def test_energy_precheck_prevents_mission_failure(capsys):
    app = ApplicationController(seed=2025)
    # Set low energy so reaching distant targets would cause mission failure
    app.rover.energy = 8.0
    app.start_autonomous_mission()

    # Step autonomous mission
    app.autonomous_mission.step()

    # Check stdout and logs for required exact warning
    captured = capsys.readouterr()
    assert "If reached, mission failure may occur" in captured.out
    assert any("If reached, mission failure may occur" in log for log in app.autonomous_mission.logs)


def test_persistent_minerals_and_naming():
    app = ApplicationController(seed=2025)
    assert len(app.environment.resources) >= 18
    # Verify resources have assigned mineral names
    assert all(hasattr(r, "name") and len(r.name) > 0 for r in app.environment.resources)

    # Pick a resource and observe it
    target_res = app.environment.resources[0]
    app.rover.known_map.observe(app.environment, target_res.position, radius=2)
    assert target_res.discovered is True

    # If collected, it remains marked as discovered (permanently visible on map)
    target_res.collected = True
    assert target_res.discovered is True
