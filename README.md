# Lost in Space — Rover Mission Control

Lost in Space is a student project to build a rover mission simulator with a
grid-based view of an unexplored world. The project uses Python and Pygame.

## Current status

The root Pygame application integrates the simulation through **Stage 5**:

- A rover explores an initially unknown grid with a repeatable, seeded world.
- Terrain contains traversable ground and obstacles; only the rover's observed
  map is shown as explored.
- Arrow keys or WASD, the on-screen direction pad, and the Start/Pause/Reset
  controls operate on the same rover instance.
- The rover automatically observes its surroundings as it moves. Discovered
  science resources appear on the map.
- A route preview finds a shortest safe path through known terrain to the
  nearest discovered resource. It does not drive the rover automatically.
- Collect loads the resource under the rover into its limited cargo capacity.
  The dashboard reports energy, coverage, cargo, resources, and moves.

Communication-zone upload, autonomous mission execution, dynamic terrain
events, and batch analytics are not part of this Stage 5 interface.

## Prerequisites

- Python 3
- Windows PowerShell

## Setup

From the project folder, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run and test

Start the application with:

```powershell
python main.py
```

Run the root-project tests with:

```powershell
python -m pytest -q .\tests --import-mode=importlib
```

## Controls

| Input | Action |
| --- | --- |
| Start / Pause | Enable or pause rover commands |
| Arrow keys / WASD / direction pad | Move one cell |
| C / Collect | Collect a discovered resource at the rover's position |
| P / Route | Preview a safe route to a known resource |
| Reset | Restore the same seeded world and rover baseline |
| Esc / window close | Quit |

Resources and terrain use fixed seeds at launch, so each fresh run and Reset
reproduces the same world.
