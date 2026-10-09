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
    name: str = "Scientific sample"

@dataclass
class RoverState:
    position: Position = (24, 24)
    energy: float = 100.0
    carried_data: float = 0.0
    uploaded_data: float = 0.0
    mission_state: str = "EXPLORING"
    target: Optional[Position] = None
    moves: int = 0

@dataclass
class MissionMetrics:
    moves: int = 0
    energy_used: float = 0.0
    cells_explored: int = 0
    data_collected: float = 0.0
    data_uploaded: float = 0.0
    value_uploaded: float = 0.0
    replans: int = 0
