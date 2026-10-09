# LOST IN SPACE — Person 2 UI build (Stages 1–5)

A Pygame planetary rover interface built around a larger **48×48** world, with a restrained mission-control HUD, procedural Mars-like terrain, fog of war, live telemetry, route rendering, discovered sample markers and keyboard/button controls.

## Requirements
- Python 3.10+
- Pygame 2.5+
- pytest 8+

## Run (Windows PowerShell)
```powershell
py -m pip install -r requirements.txt
py main.py
```

## Tests
```powershell
py -m pytest -q
```

## Controls
- **Enter**: start/resume autonomous exploration
- **Space**: pause
- **Tab**: scan local area
- **E**: collect sample when standing on its cell
- **R**: reset deterministic mission
- **WASD / Arrow keys**: move one adjacent cell
- On-screen buttons provide Start, Pause, Reset, Scan and Collect.

## Person 2 files
- `ui/map_renderer.py` — planetary tactical map, fog of war, rover, resources and route.
- `ui/dashboard.py` — telemetry, mission/target panel, event stream and surface conditions.
- `ui/controls.py` — UI intent handling; does not directly mutate simulation state.
- `ui/theme.py` — centralized colors and UI theme.

## Scope and honest status
This is a runnable integrated reference build for the **Stage 1–5** workflow in the supplied team guide. It includes minimal supporting simulation/mission modules so the UI can be launched and demonstrated independently. It is not a completion of later Stage 6–9 features such as communication-zone uploads, dynamic events, experiment reports or final release workflows. The generated map is a stylized simulation, not a physically accurate planetary terrain model.
