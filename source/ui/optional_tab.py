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

# ui/optional_tab.py
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal

from models.optional import OptionalData, AdditionalCADModel, ReferenceImage
from services.checksum_service import file_checksum


class OptionalDataTab(QWidget):
    data_changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Additional CAD / Project files"))
        layout.addLayout(self._btn_row("Add CAD File", self._add_cad,
                                       "Remove Selected", self._remove_cad,
                                       self._export_cad))
        self.cad_table = self._make_table()
        layout.addWidget(self.cad_table)

        layout.addWidget(QLabel("Reference Images"))
        layout.addLayout(self._btn_row("Add Image", self._add_image,
                                       "Remove Selected", self._remove_image,
                                       self._export_image))
        self.img_table = self._make_table()
        layout.addWidget(self.img_table)

        self._cad_files: list[AdditionalCADModel] = []
        self._images: list[ReferenceImage] = []

    # ------------------------------------------------------------------
    def _make_table(self) -> QTableWidget:
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["File Name", "Format", "Size (bytes)", "Checksum", "Description"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return t

    def _btn_row(self, add_label, add_slot, rem_label, rem_slot,
                 exp_slot=None) -> QHBoxLayout:
        row = QHBoxLayout()
        btn_add = QPushButton(add_label)
        btn_add.clicked.connect(add_slot)
        btn_rem = QPushButton(rem_label)
        btn_rem.clicked.connect(rem_slot)
        btn_exp = QPushButton("Export Selected")
        btn_exp.clicked.connect(exp_slot or (lambda: None))
        row.addWidget(btn_add)
        row.addWidget(btn_rem)
        row.addWidget(btn_exp)
        row.addStretch()
        return row

    def _set_row(self, table: QTableWidget, row: int, file_name, fmt, size, checksum, desc):
        for col, val in enumerate([file_name, fmt, size, checksum, desc]):
            item = QTableWidgetItem(str(val))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, col, item)

    # ------------------------------------------------------------------
    # CAD
    # ------------------------------------------------------------------
    def _add_cad(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select CAD File(s)", "", "CAD Files (*.stl *.step *.stp *.iges *.3mf)"
        )
        for path in paths:
            fname = os.path.basename(path)
            fmt = os.path.splitext(fname)[1].lstrip(".").upper()
            cad = AdditionalCADModel(
                file_name=fname, file_format=fmt,
                file_size=str(os.path.getsize(path)),
                checksum=file_checksum(path),
                description="", source_path=path,
            )
            self._cad_files.append(cad)
            row = self.cad_table.rowCount()
            self.cad_table.insertRow(row)
            self._set_row(self.cad_table, row, cad.file_name, cad.file_format,
                          cad.file_size, cad.checksum, cad.description)


    def _export_file(self, file_name: str, source_path: str,
                     zip_arc_prefix: str) -> None:
        import os, shutil, zipfile
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        dest, _ = QFileDialog.getSaveFileName(self, "Export File", file_name)
        if not dest:
            return

        if source_path and os.path.isfile(source_path):
            shutil.copy2(source_path, dest)
            QMessageBox.information(self, "Export", f"Saved to:\n{dest}")
            return

        tdp_path = getattr(self, "_current_tdp_path", None)
        if tdp_path and os.path.isfile(tdp_path):
            arc_name = f"{zip_arc_prefix}{file_name}"
            try:
                with zipfile.ZipFile(tdp_path) as zf:
                    if arc_name in zf.namelist():
                        with zf.open(arc_name) as sf, open(dest, "wb") as df:
                            df.write(sf.read())
                        QMessageBox.information(self, "Export", f"Saved to:\n{dest}")
                        return
            except Exception as e:
                QMessageBox.warning(self, "Export", f"Could not read archive:\n{e}")
                return

        QMessageBox.warning(self, "Export",
            "File not available for export.\n"
            "The original source file may have been moved or the "
            "package has not been saved yet.")

    def _export_cad(self):
        rows = sorted({i.row() for i in self.cad_table.selectionModel().selectedRows()})
        if not rows:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export", "Select a row first.")
            return
        f = self._cad_files[rows[0]]
        self._export_file(f.file_name, f.source_path, "Optional/CAD/")

    def _export_image(self):
        rows = sorted({i.row() for i in self.img_table.selectionModel().selectedRows()})
        if not rows:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export", "Select a row first.")
            return
        f = self._images[rows[0]]
        self._export_file(f.file_name, f.source_path, "Optional/Images/")

    def _remove_cad(self):
        rows = sorted({i.row() for i in self.cad_table.selectionModel().selectedRows()}, reverse=True)
        for row in rows:
            self.cad_table.removeRow(row)
            self._cad_files.pop(row)

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------
    def _add_image(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Image(s)", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        for path in paths:
            fname = os.path.basename(path)
            fmt = os.path.splitext(fname)[1].lstrip(".").upper()
            img = ReferenceImage(
                file_name=fname, file_format=fmt,
                file_size=str(os.path.getsize(path)),
                checksum=file_checksum(path),
                description="", source_path=path,
            )
            self._images.append(img)
            row = self.img_table.rowCount()
            self.img_table.insertRow(row)
            self._set_row(self.img_table, row, img.file_name, img.file_format,
                          img.file_size, img.checksum, img.description)

    def _remove_image(self):
        rows = sorted({i.row() for i in self.img_table.selectionModel().selectedRows()}, reverse=True)
        for row in rows:
            self.img_table.removeRow(row)
            self._images.pop(row)

    # ------------------------------------------------------------------
    # Data I/O
    # ------------------------------------------------------------------
    def has_errors(self) -> bool:
        return False  # No required fields on this tab

    def get_data(self) -> OptionalData:
        return OptionalData(additional_cad=list(self._cad_files), images=list(self._images))

    def load_data(self, opt: OptionalData):
        self.cad_table.setRowCount(0)
        self._cad_files = []
        for cad in opt.additional_cad:
            self._cad_files.append(cad)
            row = self.cad_table.rowCount()
            self.cad_table.insertRow(row)
            self._set_row(self.cad_table, row, cad.file_name, cad.file_format,
                          cad.file_size, cad.checksum, cad.description)

        self.img_table.setRowCount(0)
        self._images = []
        for img in opt.images:
            self._images.append(img)
            row = self.img_table.rowCount()
            self.img_table.insertRow(row)
            self._set_row(self.img_table, row, img.file_name, img.file_format,
                          img.file_size, img.checksum, img.description)
