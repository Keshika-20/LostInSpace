# Lost in Space — Rover Mission Control

Lost in Space is a student project to build a rover mission simulator with a
grid-based view of an unexplored world. The project uses Python and Pygame.

## Current status

**Stage 1 is in progress.** The team is preparing the project skeleton. The
planned first stage is a Pygame window with a static 10×10 grid, a placeholder
rover, title and status display, and quit handling. Movement, terrain
generation, pathfinding, resource collection, and mission logic are not part
of Stage 1.

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

Once the Stage 1 entry point is in place, start the application with:

```powershell
python main.py
```

Run the tests with:

```powershell
python -m pytest -q
```
