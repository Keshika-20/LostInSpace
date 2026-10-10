# LOST IN SPACE — Planetary Exploration Mission

**Stages 1–9 complete** · Python + Pygame · **True 3D Isometric Planetary Surface**

A rover explores an unknown alien world, discovers scientific resources, plans routes with A*, collects samples, uploads from communication zones, handles dynamic hazards, and returns safely — presented with a judge-ready **3D isometric planetary surface**.

---

## Features

| Stage | Capability |
|-------|------------|
| 1 | Project skeleton, Pygame window, shared contracts |
| 2 | Legal movement, energy accounting, Start/Pause/Reset |
| 3 | True world vs known map, incremental observation |
| 4 | A* pathfinding, route display, replan on blockage |
| 5 | Resource discovery, scoring, one-time collection |
| 6 | Communication zones, upload, safe-return energy check |
| 7 | Dynamic obstacles, robust recovery, event pulses |
| 8 | Analytics, end-of-mission report, metrics |
| 9 | Polish, documentation, clean install |

---

## 3D Planetary Surface UI

- **True isometric 3D projection** — height-displaced terrain, volumetric rock pillars, depth-sorted rendering
- Organic multi-octave heightmap with directional NW lighting & soft atmospheric fog
- Raised rocky outcrops with side faces, glowing crystals, animated base & comm-zone signal rings
- Sci-fi rover with 3D chassis, canopy, wheels and blinking antenna sitting on the surface
- Cyan route ribbons that follow terrain elevation + tactical target crosshair
- Event pulse animations on blockage / collect / upload
- Holographic Mission Control panel: energy bar, science payload, coverage, event log
- End-of-mission report overlay with full metrics
- Starfield background + vignette so the world feels embedded in deep space

UI **only displays and sends commands**. It never mutates energy, position, or mission logic.

---

## Quick Start

```bash
cd lost-in-space
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

**Controls**

| Input | Action |
|-------|--------|
| ▶ START / Space | Run simulation |
| ⏸ PAUSE / Space | Freeze |
| ↺ RESET / R | Rebuild world (same seed) |
| ESC | Quit |

---

## Architecture

```
lost-in-space/
├── main.py
├── simulation/          # M1 — true world, rover, map, A*
├── mission/             # M3 — controller, targets, upload, metrics
├── ui/                  # M2 — theme, map_renderer (3D iso), dashboard, controls
├── analytics/           # M4 — report, experiment runner
├── tests/
└── docs/
```

**Core principle:** the true world is never inspected by the mission planner. Only the exploration map is used for decisions.

---

## Running Tests

```bash
pytest -q
```

---

## Coordinates & Contracts

- Positions: `(row, col)` zero-based, row increases downward
- Energy cost: **1.0** per successful orthogonal move
- Route: list of positions including start & goal, or `None`
- Data size (MB) is separate from scientific value score
- Upload only inside known communication zones

---

## Team Roles

| Member | Owns |
|--------|------|
| M1 Simulation | environment, rover, exploration_map, pathfinding |
| M2 Frontend | map_renderer (3D isometric), dashboard, controls, theme |
| M3 Strategy | mission_controller, target_selector, communication, metrics |
| M4 Integration | main.py, models, analytics, README, requirements |

---

This package delivers a polished, fully runnable Stages 1–9 foundation with a presentation-ready **3D isometric planetary surface** designed to impress judges.
