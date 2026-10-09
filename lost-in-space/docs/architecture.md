# Architecture Overview

## Data flow

```
Environment (true world)
        │
        ▼ observe()
ExplorationMap (known cells only)
        │
        ├──► Pathfinding (A*)
        ├──► TargetSelector
        └──► MapRenderer (UI)
                │
Rover ◄── MissionController ◄── Controls (START/PAUSE/RESET)
  │                │
  └── state ───────┴──► Dashboard
```

## Shared contracts

See `simulation/models.py`:

- `Position = tuple[int, int]`
- `Resource`, `RoverState`, `MissionMetrics`
- Mission states: EXPLORING, TRAVELLING, COLLECTING, …

## UI rule

UI modules **display** and **send commands**. They never:

- deduct energy
- move the rover
- collect samples
- choose mission targets
