"""Rover movement, energy and observation."""
from __future__ import annotations
from typing import Optional, Tuple
from .models import Position, RoverState, Resource
from .environment import Environment
from .exploration_map import ExplorationMap

MOVE_COST = 1.0  # energy per successful one-cell move


class Rover:
    def __init__(self, env: Environment, exp_map: ExplorationMap, start: Optional[Position] = None):
        self.env = env
        self.exp_map = exp_map
        start_pos = start or env.base_pos
        self.state = RoverState(position=start_pos, energy=100.0)
        # initial observation
        self.exp_map.observe(start_pos, radius=2)

    def can_move_to(self, dest: Position) -> bool:
        if not self.env.is_inside(dest):
            return False
        # true-world check (dynamic obstacles)
        if not self.env.is_traversable_true(dest):
            return False
        # energy
        if self.state.energy < MOVE_COST:
            return False
        # only orthogonal one-step
        r, c = self.state.position
        dr, dc = abs(dest[0] - r), abs(dest[1] - c)
        return (dr + dc) == 1

    def move(self, dest: Position) -> Tuple[bool, str]:
        """Attempt one-cell move. Returns (success, message)."""
        if not self.can_move_to(dest):
            return False, "illegal_or_blocked"
        self.state.position = dest
        self.state.energy -= MOVE_COST
        # observe after move
        self.exp_map.observe(dest, radius=1)
        return True, "ok"

    def try_collect(self) -> Tuple[bool, str, float]:
        """Collect resource at current position if present and not yet collected."""
        res = self.env.get_resource_at(self.state.position)
        if res is None:
            return False, "no_resource", 0.0
        if not res.discovered:
            return False, "not_discovered", 0.0
        if res.collected:
            return False, "already_collected", 0.0
        # collect
        res.collected = True
        self.state.carried_data += res.data_size
        self.state.carried_value += res.value
        return True, "collected", res.data_size

    def reset(self, energy: float = 100.0) -> None:
        self.state = RoverState(position=self.env.base_pos, energy=energy)
        # re-observe base
        self.exp_map.observe(self.env.base_pos, radius=2)
