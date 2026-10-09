"""Rover: owns its position and energy, and is the only place a move is applied.

Rule used everywhere in move_to: check everything first, change state last.
That way a rejected move can never leave the rover half-moved.
"""

from dataclasses import dataclass

from simulation.environment import Environment, Position


@dataclass
class MoveResult:
    """What happened when the rover tried to move."""
    success: bool
    reason: str          # "ok", "out_of_bounds", "blocked", "not_adjacent", "insufficient_energy"
    energy_spent: float  # 0 when the move failed


class Rover:
    def __init__(
        self,
        env: Environment,
        start: Position = (0, 0),
        energy: float = 100.0,
        move_cost: float = 1.0,
    ):
        if not env.is_traversable(start):
            raise ValueError("start position must be inside the grid and not an obstacle")
        self.env = env
        self.start = start
        self.initial_energy = energy
        self.move_cost = move_cost
        # Same field names as RoverState in the shared models contract.
        self.position = start
        self.energy = energy

    def move_to(self, next_pos: Position) -> MoveResult:
        """Try to move one cell (up, down, left or right) to next_pos."""
        # 1. Inside the grid?
        if not self.env.in_bounds(next_pos):
            return MoveResult(False, "out_of_bounds", 0.0)

        # 2. Not an obstacle?
        if not self.env.is_traversable(next_pos):
            return MoveResult(False, "blocked", 0.0)

        # 3. Exactly one step, no diagonals, not staying in place?
        row_diff = abs(next_pos[0] - self.position[0])
        col_diff = abs(next_pos[1] - self.position[1])
        if row_diff + col_diff != 1:
            return MoveResult(False, "not_adjacent", 0.0)

        # 4. Enough energy? (this also guarantees energy never goes negative)
        if self.energy < self.move_cost:
            return MoveResult(False, "insufficient_energy", 0.0)

        # All checks passed: now, and only now, change state.
        self.position = next_pos
        self.energy -= self.move_cost
        return MoveResult(True, "ok", self.move_cost)

    def reset(self) -> None:
        """Back to the start position and starting energy (used by the Reset button)."""
        self.position = self.start
        self.energy = self.initial_energy