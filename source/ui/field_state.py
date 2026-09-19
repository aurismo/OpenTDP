# SPDX-License-Identifier: GPL-3.0-or-later
#
# OpenTDP Package Editor — OpenTDP "FIN TDP"
# Copyright (C) 2026  V. Viljanen <fintdp@outlook.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Project:      OpenTDP Package Editor
# Version:      v20260909a (Alpha)
# Specification: OpenTDP "FIN TDP"
# Repository:   https://github.com/aurismo/OpenTDP
# Development:  Manual programming, GitHub Copilot, Claude.ai

# ui/field_state.py
"""
Centralised field-state styling for all TDP tabs.

Two states:
  REQUIRED_EMPTY  — field is mandatory right now but has no value:
                    red border + very light red background.
  REQUIRED_FILLED — field is mandatory right now and has a value:
                    green border + very light green background.

Widgets that are optional receive no extra styling (clear() resets them).

Usage
-----
    from ui.field_state import apply_state, clear_state, REQUIRED_EMPTY, REQUIRED_FILLED

    # Mark a single widget:
    apply_state(self.tdp_id, REQUIRED_EMPTY)
    apply_state(self.name,   REQUIRED_FILLED)
    clear_state(self.description)   # optional field — no colour

    # Convenience: update a whole mapping in one call:
    update_states({
        self.tdp_id:    bool(self.tdp_id.text().strip()),
        self.name:      bool(self.name.text().strip()),
    })
    # True  → REQUIRED_FILLED (green)
    # False → REQUIRED_EMPTY  (red)
"""
from PyQt6.QtWidgets import QWidget

# ── Stylesheet fragments ──────────────────────────────────────────────────────
_BASE = "border-radius: 4px;"

REQUIRED_EMPTY = (
    "border: 1.5px solid #f87171;"          # red-400
    "background-color: #fff5f5;"            # very light red
) + _BASE

REQUIRED_FILLED = (
    "border: 1.5px solid #4ade80;"          # green-400
    "background-color: #f0fdf4;"            # very light green
) + _BASE

_CLEAR = ""   # reset to default Qt styling


# ── Public API ────────────────────────────────────────────────────────────────

def apply_state(widget: QWidget, style: str) -> None:
    """Apply REQUIRED_EMPTY or REQUIRED_FILLED stylesheet to *widget*."""
    widget.setStyleSheet(style)


def clear_state(widget: QWidget) -> None:
    """Remove any field-state styling (optional field)."""
    widget.setStyleSheet(_CLEAR)


def update_states(mapping: dict[QWidget, bool]) -> None:
    """
    Bulk-update a dict of {widget: is_filled}.
    True  → REQUIRED_FILLED (green)
    False → REQUIRED_EMPTY  (red)
    """
    for widget, filled in mapping.items():
        apply_state(widget, REQUIRED_FILLED if filled else REQUIRED_EMPTY)
