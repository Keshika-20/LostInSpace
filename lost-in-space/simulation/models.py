"""Shared data contracts for Lost in Space simulation.
Coordinates: (row, col), zero-based. Rows increase downwards; columns rightwards.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

Position = Tuple[int, int]

@dataclass
class Resource:
    position: Position
    value: float          # scientific value score
    data_size: float      # MB
    discovered: bool = False
    collected: bool = False

@dataclass
class RoverState:
    position: Position
    energy: float = 100.0
    carried_data: float = 0.0
    uploaded_data: float = 0.0
    mission_state: str = "EXPLORING"
    target: Optional[Position] = None
    carried_value: float = 0.0   # scientific value of carried data

@dataclass
class MissionMetrics:
    moves: int = 0
    energy_used: float = 0.0
    cells_explored: int = 0
    data_collected: float = 0.0
    data_uploaded: float = 0.0
    value_uploaded: float = 0.0
    value_collected: float = 0.0
    replans: int = 0
    collections: int = 0

# Mission states (agreed set)
MISSION_STATES = {
    "EXPLORING",
    "TRAVELLING",
    "COLLECTING",
    "TRAVELLING_TO_ZONE",
    "UPLOADING",
    "RETURNING",
    "COMPLETED",
    "FAILED",
}
