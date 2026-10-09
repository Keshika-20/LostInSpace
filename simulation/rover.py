"""Rover: owns its position, energy, cargo and its own map of the world.

Rule used in move_to: check everything first, change state last.
A rejected move therefore never leaves the rover half-moved.
"""

from dataclasses import dataclass

from simulation.environment import Environment, Position
from simulation.exploration_map import ExplorationMap


@dataclass
class MoveResult:
    """What happened when the rover tried to move."""
    success: bool
    reason: str          # "ok", "out_of_bounds", "not_adjacent", "blocked", "insufficient_energy"
    energy_spent: float  # 0 when the move failed


class Rover:
    def __init__(
        self,
        env: Environment,
        start: Position = (0, 0),
        energy: float = 100.0,
        move_cost: float = 1.0,
        vision_radius: int = 2,
        capacity: float = 10.0,
    ):
        if not env.is_traversable(start):
            raise ValueError("start position must be inside the grid and not an obstacle")
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        self.env = env
        self.start = start
        self.initial_energy = energy
        self.move_cost = move_cost
        self.vision_radius = vision_radius
        self.capacity = capacity            # most data (MB) the rover can carry at once
        # Same field names as RoverState in the shared models contract.
        self.position = start
        self.energy = energy
        self.carried_data = 0.0             # on board, not uploaded yet
        self.uploaded_data = 0.0            # total uploaded (updated by the mission code)
        self.moves = 0                      # successful moves so far
        # What the rover has seen so far. Starts completely unknown.
        self.known_map = ExplorationMap(env.rows, env.cols)
        self.observe()

    # ---------- sensing ----------

    def observe(self) -> int:
        """Look around from the current position. Returns the number of new cells seen."""
        return self.known_map.observe(self.env, self.position, self.vision_radius)

    def at_comm_zone(self) -> bool:
        """True if the rover is standing inside a communication zone."""
        return self.env.in_comm_zone(self.position)

    # ---------- movement ----------

    def move_to(self, next_pos: Position) -> MoveResult:
        """Try to move one cell (up, down, left or right) to next_pos."""
        # 1. Inside the grid?
        if not self.env.in_bounds(next_pos):
            return MoveResult(False, "out_of_bounds", 0.0)

        # 2. Exactly one step, no diagonals, not staying in place?
        #    This comes BEFORE the obstacle check on purpose: a far-away
        #    invalid move must not reveal whether that cell is blocked.
        row_diff = abs(next_pos[0] - self.position[0])
        col_diff = abs(next_pos[1] - self.position[1])
        if row_diff + col_diff != 1:
            return MoveResult(False, "not_adjacent", 0.0)

        # 3. Not an obstacle? The rover has bumped into it, so it remembers it.
        #    This is checked at move time, so cells blocked mid-mission are caught too.
        if not self.env.is_traversable(next_pos):
            self.known_map.mark_obstacle(next_pos)
            return MoveResult(False, "blocked", 0.0)

        # 4. Enough energy? (this also guarantees energy never goes negative)
        if self.energy < self.move_cost:
            return MoveResult(False, "insufficient_energy", 0.0)

        # All checks passed: now, and only now, change state.
        self.position = next_pos
        self.energy -= self.move_cost
        self.moves += 1
        self.observe()
        return MoveResult(True, "ok", self.move_cost)

    # ---------- cargo ----------

    def can_carry(self, data_size: float) -> bool:
        """True if this much more data still fits on board."""
        return self.carried_data + data_size <= self.capacity

    def load(self, data_size: float) -> bool:
        """Take on data. Returns False (and changes nothing) if it would not fit."""
        if data_size < 0:
            raise ValueError("data_size cannot be negative")
        if not self.can_carry(data_size):
            return False
        self.carried_data += data_size
        return True

    def unload(self) -> float:
        """Empty the cargo and return how much was on board (the upload step uses this)."""
        amount = self.carried_data
        self.carried_data = 0.0
        return amount

    # ---------- bookkeeping ----------

    def energy_used(self) -> float:
        """Energy spent since the start of the mission."""
        return self.initial_energy - self.energy

    def reset(self) -> None:
        """Back to the start: position, energy, cargo, counters, empty map, resources uncollected.

        Terrain changed by Stage 7 events is NOT undone. For a full reset,
        rebuild the Environment from its seed (same seed, same world).
        """
        self.position = self.start
        self.energy = self.initial_energy
        self.carried_data = 0.0
        self.uploaded_data = 0.0
        self.moves = 0
        self.env.reset_resources()
        self.known_map = ExplorationMap(self.env.rows, self.env.cols)
        self.observe()