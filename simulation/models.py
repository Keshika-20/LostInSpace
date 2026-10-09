"""Shared data contract for the whole team (from the team PDF).

Member 4 owns this file. This copy exists so Member 1's code can run
until Member 4's version is merged.
"""

from dataclasses import dataclass, field
from typing import Optional

Position = tuple[int, int]


@dataclass
class Resource:
    position: Position
    value: float
    data_size: float
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


@dataclass
class MissionMetrics:
    moves: int = 0
    energy_used: float = 0.0
    cells_explored: int = 0
    data_collected: float = 0.0
    data_uploaded: float = 0.0
    value_uploaded: float = 0.0
    replans: int = 0