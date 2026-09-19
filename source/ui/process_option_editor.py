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

# ui/process_option_editor.py
import uuid
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QComboBox
)
from models.manufacturing import ProcessOption


class ProcessOptionEditor(QDialog):
    def __init__(self, parent=None, existing: ProcessOption = None):
        super().__init__(parent)
        self.setWindowTitle("Process Option")
        self.setMinimumWidth(420)

        # Stable identifier used to name this option's archive folder for
        # step attachments (Manufacturing/<id>/<StepID>/...). Generated once
        # and kept for the option's lifetime; never regenerated on edit.
        self._option_id = (existing.id if existing and existing.id
                            else f"PO-{uuid.uuid4().hex[:6]}")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()

        self.revision = QLineEdit()
        self.revision.setPlaceholderText("e.g. A  /  1.0  /  2024-R2")

        self.description = QTextEdit()
        self.description.setFixedHeight(80)

        self.maturity = QComboBox()
        self.maturity.addItems([
            "Very Low — Ad hoc / Initial",
            "Low — Repeatable",
            "Moderate — Defined / Standardized",
            "High — Measured and Controlled",
            "Very High — Optimized",
        ])
        self.maturity.wheelEvent = lambda e: e.ignore()

        if existing:
            self.name.setText(existing.option_name)
            self.revision.setText(existing.revision)
            self.description.setPlainText(existing.description)
            self.maturity.setCurrentText(existing.maturity)

        form.addRow("Option Name:", self.name)
        form.addRow("Revision:", self.revision)
        form.addRow("Process Maturity:", self.maturity)
        form.addRow("Description:", self.description)
        layout.addLayout(form)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def get_data(self) -> dict:
        return {
            "id": self._option_id,
            "OptionName": self.name.text().strip(),
            "Revision": self.revision.text().strip(),
            "Description": self.description.toPlainText().strip(),
            "Maturity": self.maturity.currentText(),
            "Steps": [],
        }
