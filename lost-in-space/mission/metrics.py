"""Mission metrics tracking."""
from __future__ import annotations
from simulation.models import MissionMetrics, RoverState


class MetricsTracker:
    def __init__(self):
        self.metrics = MissionMetrics()

    def on_move(self, energy_cost: float = 1.0) -> None:
        self.metrics.moves += 1
        self.metrics.energy_used += energy_cost

    def on_explore(self, cells: int) -> None:
        self.metrics.cells_explored = cells

    def on_collect(self, data_size: float, value: float) -> None:
        self.metrics.data_collected += data_size
        self.metrics.value_collected += value
        self.metrics.collections += 1

    def on_upload(self, data_size: float, value: float) -> None:
        self.metrics.data_uploaded += data_size
        self.metrics.value_uploaded += value

    def on_replan(self) -> None:
        self.metrics.replans += 1

    def snapshot(self) -> MissionMetrics:
        return self.metrics
