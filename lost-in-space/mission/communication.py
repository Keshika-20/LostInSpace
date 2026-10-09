"""Communication zone upload logic — Stage 6."""
from __future__ import annotations
from typing import Tuple
from simulation.models import RoverState
from simulation.exploration_map import ExplorationMap, KNOWN_ZONE


def can_upload(state: RoverState, exp_map: ExplorationMap) -> bool:
    r, c = state.position
    return exp_map.get_cell((r, c)) == KNOWN_ZONE


def do_upload(state: RoverState) -> Tuple[float, float]:
    """Transfer all carried data. Returns (data_uploaded, value_uploaded)."""
    data = state.carried_data
    value = state.carried_value
    state.uploaded_data += data
    state.carried_data = 0.0
    # value is tracked in metrics; clear held value
    held = state.carried_value
    state.carried_value = 0.0
    return data, held
