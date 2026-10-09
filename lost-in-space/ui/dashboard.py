"""
Mission dashboard — Member 2. Clear telemetry, polished cards, end report.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import pygame
from .theme import Theme
from simulation.models import RoverState, MissionMetrics


class Dashboard:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.notifications: List[Dict[str, str]] = []
        self.show_report = False
        self.report_data: Optional[Dict[str, Any]] = None

    def push_notification(self, text: str, kind: str = "info") -> None:
        self.notifications.append({"text": text, "kind": kind})
        if len(self.notifications) > 8:
            self.notifications = self.notifications[-8:]

    def show_end_report(self, data: Dict[str, Any]) -> None:
        self.show_report = True
        self.report_data = data

    def hide_report(self) -> None:
        self.show_report = False

    def draw(self, surface, state: RoverState, metrics: MissionMetrics,
             coverage: float, events=None, route_len: int = 0, extra=None) -> None:
        pygame.draw.rect(surface, Theme.BG_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, Theme.BG_PANEL_EDGE, self.rect, 2, border_radius=12)

        x = self.rect.x + 18
        y = self.rect.y + 14
        w = self.rect.width - 36

        surface.blit(Theme.FONT_TITLE.render("MISSION CONTROL", True, Theme.TEXT_PRIMARY), (x, y))
        y += 28
        pygame.draw.line(surface, Theme.BG_PANEL_EDGE, (x, y), (x + w, y), 1)
        y += 12

        status_col = {
            "EXPLORING": Theme.TEXT_ACCENT, "TRAVELLING": Theme.TEXT_INFO,
            "COLLECTING": Theme.TEXT_WARNING, "TRAVELLING_TO_ZONE": Theme.TEXT_INFO,
            "UPLOADING": Theme.TEXT_SUCCESS, "RETURNING": Theme.ALERT_RETURN,
            "COMPLETED": Theme.TEXT_SUCCESS, "FAILED": Theme.TEXT_DANGER,
        }.get(state.mission_state, Theme.TEXT_SECONDARY)

        card = pygame.Rect(x, y, w, 30)
        pygame.draw.rect(surface, Theme.BG_CARD, card, border_radius=6)
        pygame.draw.rect(surface, status_col, card, 1, border_radius=6)
        surface.blit(Theme.FONT_HEAD.render(state.mission_state, True, status_col), (x + 12, y + 6))
        y += 40

        # Energy
        surface.blit(Theme.FONT_SMALL.render("ENERGY RESERVE", True, Theme.TEXT_ACCENT), (x, y))
        y += 16
        energy_pct = max(0.0, min(1.0, state.energy / 100.0))
        bar_h = 18
        pygame.draw.rect(surface, Theme.ENERGY_BG, (x, y, w, bar_h), border_radius=6)
        fill_w = max(0, int(w * energy_pct))
        ecol = Theme.ENERGY_HIGH if energy_pct > 0.5 else (Theme.ENERGY_MID if energy_pct > 0.25 else Theme.ENERGY_LOW)
        if fill_w > 0:
            pygame.draw.rect(surface, ecol, (x, y, fill_w, bar_h), border_radius=6)
        for i in range(1, 4):
            sx = x + int(w * i / 4)
            pygame.draw.line(surface, Theme.BG_PANEL, (sx, y + 2), (sx, y + bar_h - 2), 1)
        e_txt = Theme.FONT_SMALL.render(f"{state.energy:.1f}", True, Theme.TEXT_PRIMARY)
        surface.blit(e_txt, (x + w - e_txt.get_width(), y - 14))
        y += bar_h + 14

        self._kv(surface, "POSITION", f"R{state.position[0]}  C{state.position[1]}", x, y, w)
        y += 20
        tgt = f"R{state.target[0]}  C{state.target[1]}" if state.target else "—"
        self._kv(surface, "TARGET", tgt, x, y, w)
        y += 20
        self._kv(surface, "ROUTE", f"{route_len} steps" if route_len else "—", x, y, w)
        y += 26

        pygame.draw.line(surface, Theme.BG_PANEL_EDGE, (x, y), (x + w, y), 1)
        y += 10
        surface.blit(Theme.FONT_SMALL.render("SCIENCE PAYLOAD", True, Theme.TEXT_ACCENT), (x, y))
        y += 18
        self._row(surface, "CARRIED", f"{state.carried_data:.1f} MB", x, y, w, Theme.TEXT_WARNING)
        y += 20
        self._row(surface, "UPLOADED", f"{state.uploaded_data:.1f} MB", x, y, w, Theme.TEXT_SUCCESS)
        y += 20
        self._row(surface, "VALUE HELD", f"{state.carried_value:.0f}", x, y, w, Theme.TEXT_ACCENT)
        y += 20
        self._row(surface, "VALUE SENT", f"{metrics.value_uploaded:.0f}", x, y, w, Theme.TEXT_SUCCESS)
        y += 26

        pygame.draw.line(surface, Theme.BG_PANEL_EDGE, (x, y), (x + w, y), 1)
        y += 10
        surface.blit(Theme.FONT_SMALL.render("EXPLORATION", True, Theme.TEXT_ACCENT), (x, y))
        y += 18
        cov_pct = max(0.0, min(1.0, coverage / 100.0))
        pygame.draw.rect(surface, Theme.ENERGY_BG, (x, y, w, 11), border_radius=4)
        pygame.draw.rect(surface, Theme.TEXT_ACCENT, (x, y, int(w * cov_pct), 11), border_radius=4)
        cov_txt = Theme.FONT_TINY.render(f"{coverage:.1f}%", True, Theme.TEXT_PRIMARY)
        surface.blit(cov_txt, (x + w - cov_txt.get_width(), y - 13))
        y += 18

        grid = [
            ("CELLS", str(metrics.cells_explored)), ("MOVES", str(metrics.moves)),
            ("REPLANS", str(metrics.replans)), ("SAMPLES", str(metrics.collections)),
            ("ENERGY USED", f"{metrics.energy_used:.0f}"), ("DATA UP", f"{metrics.data_uploaded:.1f}"),
        ]
        col_w = w // 2
        for i, (k, v) in enumerate(grid):
            gx = x + (i % 2) * col_w
            gy = y + (i // 2) * 20
            surface.blit(Theme.FONT_TINY.render(k, True, Theme.TEXT_MUTED), (gx, gy))
            surface.blit(Theme.FONT_SMALL.render(v, True, Theme.TEXT_PRIMARY), (gx + 70, gy - 1))
        y += 20 * 3 + 10

        pygame.draw.line(surface, Theme.BG_PANEL_EDGE, (x, y), (x + w, y), 1)
        y += 10
        surface.blit(Theme.FONT_SMALL.render("EVENT LOG", True, Theme.TEXT_ACCENT), (x, y))
        y += 16

        feed = self.notifications[-6:]
        if not feed and events:
            feed = [{"text": e, "kind": "info"} for e in events[-6:]]
        kind_col = {
            "info": Theme.TEXT_SECONDARY, "block": Theme.ALERT_BLOCK,
            "energy": Theme.ALERT_ENERGY, "replan": Theme.ALERT_REPLAN,
            "upload": Theme.ALERT_UPLOAD, "return": Theme.ALERT_RETURN,
            "success": Theme.TEXT_SUCCESS, "collect": Theme.TEXT_WARNING,
        }
        for item in feed:
            col = kind_col.get(item.get("kind", "info"), Theme.TEXT_SECONDARY)
            display = item["text"] if len(item["text"]) < 40 else item["text"][:37] + "…"
            surface.blit(Theme.FONT_TINY.render("▸ " + display, True, col), (x, y))
            y += 15

        if self.show_report and self.report_data:
            self._draw_report(surface)

    def _draw_report(self, surface):
        d = self.report_data
        rw, rh = self.rect.width - 24, 360
        rx = self.rect.x + 12
        ry = self.rect.y + 50
        report = pygame.Rect(rx, ry, rw, rh)
        pygame.draw.rect(surface, Theme.REPORT_BG, report, border_radius=12)
        pygame.draw.rect(surface, Theme.REPORT_EDGE, report, 2, border_radius=12)
        cx, cy = rx + 18, ry + 16
        surface.blit(Theme.FONT_TITLE.render("MISSION REPORT", True, Theme.TEXT_ACCENT), (cx, cy))
        cy += 34
        outcome = d.get("outcome", "UNKNOWN")
        ocol = Theme.TEXT_SUCCESS if outcome == "COMPLETED" else Theme.TEXT_DANGER
        surface.blit(Theme.FONT_HEAD.render(outcome, True, ocol), (cx, cy))
        cy += 30
        rows = [
            ("Coverage", f"{d.get('coverage', 0):.1f}%"),
            ("Data collected", f"{d.get('data_collected', 0):.1f} MB"),
            ("Data uploaded", f"{d.get('data_uploaded', 0):.1f} MB"),
            ("Value delivered", f"{d.get('value_uploaded', 0):.0f}"),
            ("Energy used", f"{d.get('energy_used', 0):.1f}"),
            ("Moves", str(d.get('moves', 0))),
            ("Replans", str(d.get('replans', 0))),
            ("Samples", str(d.get('collections', 0))),
            ("Return success", "YES" if d.get('return_success') else "NO"),
        ]
        for k, v in rows:
            surface.blit(Theme.FONT_BODY.render(k, True, Theme.TEXT_SECONDARY), (cx, cy))
            vt = Theme.FONT_BODY.render(v, True, Theme.TEXT_PRIMARY)
            surface.blit(vt, (rx + rw - 18 - vt.get_width(), cy))
            cy += 24
        surface.blit(Theme.FONT_TINY.render("Press RESET to run again", True, Theme.TEXT_MUTED),
                     (cx, ry + rh - 26))

    def _kv(self, surface, key, value, x, y, w):
        surface.blit(Theme.FONT_BODY.render(key, True, Theme.TEXT_SECONDARY), (x, y))
        vt = Theme.FONT_BODY.render(value, True, Theme.TEXT_PRIMARY)
        surface.blit(vt, (x + w - vt.get_width(), y))

    def _row(self, surface, key, value, x, y, w, vcol):
        surface.blit(Theme.FONT_BODY.render(key, True, Theme.TEXT_SECONDARY), (x, y))
        vt = Theme.FONT_BODY.render(value, True, vcol)
        surface.blit(vt, (x + w - vt.get_width(), y))
