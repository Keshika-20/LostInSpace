# Architecture — Person 2 UI integration build

## Stage coverage
- **Stage 1:** launchable Pygame window, fixed 48×48 map, rover marker, title and legend.
- **Stage 2:** actual rover position and energy, Start/Pause/Reset and keyboard movement.
- **Stage 3:** hidden world vs. known map, local scan reveal, explored coverage and terrain states.
- **Stage 4:** A* route overlay, target position and route state exposed to the UI.
- **Stage 5:** discovered resources, collected/uncollected states, target value and carried data.

## UI ownership boundary
`ui/map_renderer.py`, `ui/dashboard.py`, `ui/controls.py`, and `ui/theme.py` are Person 2's primary files. They render supplied model state and emit user intents; movement, energy deduction, target selection and collection rules live outside the UI.

## Visual approach
The surface view uses layered atmospheric silhouettes and procedural regolith markings; the tactical map uses deterministic terrain variation, unknown-area fog, obstacle texture, a route trace, resource markers, and a small rover chassis. HUD panels use restrained cyan/amber telemetry accents rather than playful saturated blocks.
