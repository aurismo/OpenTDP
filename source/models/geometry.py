# SPDX-License-Identifier: GPL-3.0-or-later
#
# TDP Package Builder — OpenTDP "FIN TDP"
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
# Project:      TDP Package Builder
# Version:      v20260909a (Alpha)
# Specification: OpenTDP "FIN TDP"
# Repository:   https://github.com/aurismo/OpenTDP
# Development:  Manual programming, GitHub Copilot, Claude.ai

# models/geometry.py
from dataclasses import dataclass, field


@dataclass
class Geometry:
    id: str = ""
    file_name: str = ""
    source_path: str = ""
    file_format: str = ""
    file_size: str = ""
    checksum: str = ""
    dimensions: str = ""
    preview: bool = False

    def to_xml_dict(self) -> dict:
        return {
            "id": self.id,
            "FileName": self.file_name,
            "SourcePath": "",  # not persisted — runtime path only
            "FileFormat": self.file_format,
            "FileSize": self.file_size,
            "Checksum": self.checksum,
            "Dimensions": self.dimensions,
            "Preview": "true" if self.preview else "false",
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "Geometry":
        return Geometry(
            id=d.get("id", ""),
            file_name=d.get("FileName", ""),
            source_path=d.get("SourcePath", ""),
            file_format=d.get("FileFormat", ""),
            file_size=d.get("FileSize", ""),
            checksum=d.get("Checksum", ""),
            dimensions=d.get("Dimensions", ""),
            preview=d.get("Preview", "false") == "true",
        )
