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

# ui/colours.py
"""
Centralised colour definitions for lifecycle and criticality levels.
Import from here — do not redefine these in individual tab files.
"""

# Lifecycle colours: (text_fg, light_bg)
LC_COLOURS = {
    "Draft":      ("#64748b", "#f1f5f9"),
    "In Review":  ("#0369a1", "#e0f2fe"),
    "Approved":   ("#3d7a00", "#ecfccb"),
    "Released":   ("#065F46", "#a7f3d0"),
    "Deprecated": ("#6b7280", "#f3f4f6"),
}

# Criticality colours: (light_text, dark_bg) — for badges and labels
CRIT_COLOURS = {
    "Non-critical": ("#e2e8f0", "#475569"),
    "Low":          ("#fef9c3", "#854d0e"),
    "Medium":       ("#ffedd5", "#c2410c"),
    "High":         ("#fecaca", "#b91c1c"),
    "Very High":    ("#ede9fe", "#4c1d95"),
}
