"""Full mission controller — Stages 1–9 behaviour."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from simulation.models import Position, RoverState
from simulation.rover import Rover
from simulation.exploration_map import ExplorationMap
from simulation.pathfinding import find_path, is_route_valid
from .target_selector import TargetSelector
from .metrics import MetricsTracker
from .communication import can_upload, do_upload

ENERGY_RESERVE = 15.0  # keep this much for safe return
MAX_REPLAN_STREAK = 20


class MissionController:
    def __init__(self, rover: Rover, exp_map: ExplorationMap):
        self.rover = rover
        self.exp_map = exp_map
        self.selector = TargetSelector(exp_map)
        self.metrics = MetricsTracker()
        self.current_route: Optional[List[Position]] = None
        self.route_index: int = 0
        self.last_action: str = "idle"
        self.events: List[str] = []
        self.replan_streak: int = 0
        self._dynamic_triggered: bool = False
        self.return_success: bool = False

    def _log(self, msg: str) -> None:
        self.events.append(msg)
        if len(self.events) > 50:
            self.events = self.events[-50:]

    def step(self) -> Dict[str, Any]:
        state = self.rover.state
        result: Dict[str, Any] = {
            "action": "idle", "moved": False, "collected": False,
            "uploaded": False, "message": "", "route": self.current_route,
            "events": list(self.events), "pulse_pos": None, "pulse_color": None,
        }

        if state.mission_state in ("COMPLETED", "FAILED"):
            result["message"] = state.mission_state
            return result

        # Critical energy → force return
        if state.energy < ENERGY_RESERVE and state.mission_state not in (
            "RETURNING", "UPLOADING", "TRAVELLING_TO_ZONE"
        ):
            state.mission_state = "RETURNING"
            self._log("Critical energy — aborting to base")
            self._plan_to(self.rover.env.base_pos)
            result["action"] = "energy_abort"
            return result

        # Stage 7: one controlled dynamic blockage mid-mission
        if (not self._dynamic_triggered and self.metrics.metrics.moves == 25
                and state.mission_state in ("TRAVELLING", "EXPLORING")):
            self._trigger_dynamic_block(result)

        pos = state.position

        # ── COLLECTING ──
        if state.mission_state == "COLLECTING":
            ok, msg, size = self.rover.try_collect()
            if ok:
                res = self.rover.env.get_resource_at(pos)
                val = res.value if res else 0.0
                self.metrics.on_collect(size, val)
                self._log(f"Collected {size:.1f} MB (value {val:.0f})")
                result["collected"] = True
                result["message"] = f"Collected {size:.1f} MB"
                result["pulse_pos"] = pos
                result["pulse_color"] = (255, 200, 50)
                # after collect, prefer upload if carrying data
                if state.carried_data > 0:
                    zone = self.selector.choose_nearest_zone(pos)
                    if zone and self._energy_feasible(zone):
                        state.mission_state = "TRAVELLING_TO_ZONE"
                        self._plan_to(zone)
                    else:
                        state.mission_state = "EXPLORING"
                else:
                    state.mission_state = "EXPLORING"
                state.target = None
                self.current_route = None
            else:
                state.mission_state = "EXPLORING"
            result["action"] = "collect"
            return result

        # ── UPLOADING ──
        if state.mission_state == "UPLOADING":
            if can_upload(state, self.exp_map):
                data, value = do_upload(state)
                self.metrics.on_upload(data, value)
                self._log(f"Uploaded {data:.1f} MB (value {value:.0f})")
                result["uploaded"] = True
                result["message"] = f"Uploaded {data:.1f} MB"
                result["pulse_pos"] = pos
                result["pulse_color"] = (60, 220, 140)
                # decide next
                if state.energy < ENERGY_RESERVE * 1.5:
                    state.mission_state = "RETURNING"
                    self._plan_to(self.rover.env.base_pos)
                else:
                    state.mission_state = "EXPLORING"
            else:
                self._log("Upload failed — not in zone")
                state.mission_state = "EXPLORING"
            result["action"] = "upload"
            return result

        # ── Follow route ──
        if self.current_route and self.route_index < len(self.current_route):
            next_pos = self.current_route[self.route_index]
            if next_pos == pos:
                self.route_index += 1
                if self.route_index >= len(self.current_route):
                    self._on_arrival()
                return result

            ok, msg = self.rover.move(next_pos)
            if ok:
                self.metrics.on_move()
                self.metrics.on_explore(self.exp_map.explored_count)
                self.route_index += 1
                self.replan_streak = 0
                result["moved"] = True
                result["action"] = "move"
                result["message"] = f"Moved to {next_pos}"
                if self.route_index >= len(self.current_route):
                    self._on_arrival()
            else:
                self.metrics.on_replan()
                self.replan_streak += 1
                self._log(f"Blocked at {next_pos} — replan #{self.replan_streak}")
                result["action"] = "replan"
                result["message"] = "Route blocked"
                result["pulse_pos"] = next_pos
                result["pulse_color"] = (255, 80, 60)
                self.current_route = None
                self.route_index = 0
                if self.replan_streak >= MAX_REPLAN_STREAK:
                    # abandon current target and try safe return instead of hard fail
                    self._log("Too many replans — aborting to base")
                    state.mission_state = "RETURNING"
                    self.replan_streak = 0
                    if not self._plan_to(self.rover.env.base_pos):
                        state.mission_state = "FAILED"
                        self._log("Cannot reach base — mission failed")
                else:
                    # try replan to same target
                    if state.target:
                        if not self._plan_to(state.target):
                            self._decide_next_target()
            return result

        # No route — decide
        self._decide_next_target()
        result["route"] = self.current_route
        result["action"] = "plan"
        return result

    def _trigger_dynamic_block(self, result: Dict) -> None:
        """Stage 7: block a cell ahead if possible."""
        self._dynamic_triggered = True
        pos = self.rover.state.position
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1)]:
            nr, nc = pos[0] + dr, pos[1] + dc
            cand = (nr, nc)
            if (self.rover.env.is_inside(cand)
                    and cand != self.rover.env.base_pos
                    and self.rover.env.is_traversable_true(cand)):
                self.rover.env.block_cell(cand)
                # reveal if near
                self.exp_map.observe(pos, radius=2)
                self._log(f"Dynamic hazard at {cand}")
                result["pulse_pos"] = cand
                result["pulse_color"] = (255, 80, 60)
                break

    def _on_arrival(self) -> None:
        state = self.rover.state
        pos = state.position
        self.current_route = None
        self.route_index = 0

        if state.mission_state == "TRAVELLING":
            state.mission_state = "COLLECTING"
            self._log(f"Arrived at resource {pos}")
        elif state.mission_state == "TRAVELLING_TO_ZONE":
            state.mission_state = "UPLOADING"
            self._log(f"Entered comm zone {pos}")
        elif state.mission_state == "RETURNING":
            if pos == self.rover.env.base_pos:
                state.mission_state = "COMPLETED"
                self.return_success = True
                self._log("Returned to base — mission complete")
        elif state.mission_state == "EXPLORING":
            self._log(f"Reached frontier {pos}")

    def _plan_to(self, goal: Position) -> bool:
        path = find_path(self.rover.state.position, goal, self.exp_map)
        if path is None:
            self._log(f"No path to {goal}")
            return False
        self.current_route = path
        self.route_index = 0
        self.rover.state.target = goal
        return True

    def _energy_feasible(self, goal: Position) -> bool:
        path = find_path(self.rover.state.position, goal, self.exp_map)
        if path is None:
            return False
        cost = (len(path) - 1) * 1.0
        # also estimate return to base
        ret = find_path(goal, self.rover.env.base_pos, self.exp_map)
        ret_cost = (len(ret) - 1) * 1.0 if ret else 30.0
        return self.rover.state.energy >= cost + ret_cost + ENERGY_RESERVE * 0.5

    def _decide_next_target(self) -> None:
        state = self.rover.state
        pos = state.position

        # Prefer upload if carrying significant data
        if state.carried_data >= 5.0:
            zone = self.selector.choose_nearest_zone(pos)
            if zone and self._energy_feasible(zone):
                if self._plan_to(zone):
                    state.mission_state = "TRAVELLING_TO_ZONE"
                    self._log(f"Heading to comm zone {zone}")
                    return

        # Best resource
        best = self.selector.choose_best_resource(pos, state.energy)
        if best is not None and self._energy_feasible(best.position):
            if self._plan_to(best.position):
                state.mission_state = "TRAVELLING"
                self._log(f"Targeting resource value={best.value:.0f} at {best.position}")
                return

        # Explore frontier
        frontier = self.selector.choose_exploration_frontier(pos)
        if frontier is not None:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = frontier[0] + dr, frontier[1] + dc
                if self.exp_map.is_traversable((nr, nc)):
                    if self._plan_to((nr, nc)):
                        state.mission_state = "EXPLORING"
                        self._log(f"Exploring toward frontier {frontier}")
                        return

        # Return home
        if pos != self.rover.env.base_pos:
            if self._plan_to(self.rover.env.base_pos):
                state.mission_state = "RETURNING"
                self._log("No more targets — returning")
                return
            else:
                state.mission_state = "FAILED"
                self._log("Cannot reach base — failed")
                return
        state.mission_state = "COMPLETED"
        self.return_success = True
        self._log("Nothing left to do — complete")

    def get_report(self) -> Dict[str, Any]:
        m = self.metrics.snapshot()
        return {
            "outcome": self.rover.state.mission_state,
            "coverage": self.exp_map.coverage(),
            "data_collected": m.data_collected,
            "data_uploaded": m.data_uploaded,
            "value_uploaded": m.value_uploaded,
            "energy_used": m.energy_used,
            "moves": m.moves,
            "replans": m.replans,
            "collections": m.collections,
            "return_success": self.return_success,
        }

    def reset(self) -> None:
        self.current_route = None
        self.route_index = 0
        self.events.clear()
        self.metrics = MetricsTracker()
        self.replan_streak = 0
        self._dynamic_triggered = False
        self.return_success = False
        self.rover.state.mission_state = "EXPLORING"
        self.rover.state.target = None
