# Architecture

The project is being developed in stages. Stage 1 aims for a minimal Pygame
skeleton: a static 10×10 grid, placeholder rover, title and status display,
and quit handling. Later-stage behavior should not be added until the team
agrees to move beyond Stage 1.

## Team ownership

- **M1 — Simulation:** `simulation/` owns the environment and, in later
  stages, rover state, exploration, and pathfinding. The true world and the
  rover's known map are intended to remain separate.
- **M2 — UI:** `ui/` owns map rendering, the dashboard, controls, and later
  theming.
- **M3 — Mission:** `mission/` owns the mission controller and, in later
  stages, target selection, communication, and metrics.
- **M4 — Integration:** owns `main.py`, dependency and ignore files, project
  documentation, shared-model coordination, and integration tests.

## Shared models and interfaces

The agreed shared model names are `Position`, `Resource`, `RoverState`, and
`MissionMetrics`. `Position` is a zero-based `(row, col)` tuple. The other
models cover:

- `Resource`: position, scientific value, data size, and discovered and
  collected state.
- `RoverState`: position, energy, carried and uploaded data, mission state,
  and an optional target.
- `MissionMetrics`: moves, energy used, explored cells, collected and
  uploaded data, uploaded value, and replans.

Exact field names, types, defaults, and module/function signatures are pending
team agreement; confirm them with the owners before wiring modules together.
