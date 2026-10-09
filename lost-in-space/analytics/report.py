"""Stage 8 — format final metrics for UI / text report."""
from __future__ import annotations
from typing import Dict, Any


def format_report(data: Dict[str, Any]) -> str:
    lines = [
        "=== MISSION REPORT ===",
        f"Outcome         : {data.get('outcome', '—')}",
        f"Coverage        : {data.get('coverage', 0):.1f}%",
        f"Data collected  : {data.get('data_collected', 0):.1f} MB",
        f"Data uploaded   : {data.get('data_uploaded', 0):.1f} MB",
        f"Value delivered : {data.get('value_uploaded', 0):.0f}",
        f"Energy used     : {data.get('energy_used', 0):.1f}",
        f"Moves           : {data.get('moves', 0)}",
        f"Replans         : {data.get('replans', 0)}",
        f"Samples         : {data.get('collections', 0)}",
        f"Return success  : {'YES' if data.get('return_success') else 'NO'}",
    ]
    return "\n".join(lines)
