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

# models/optional.py
from dataclasses import dataclass, field
from typing import List


@dataclass
class AdditionalCADModel:
    file_name: str = ""
    file_format: str = ""
    file_size: str = ""
    checksum: str = ""
    description: str = ""
    source_path: str = ""

    def to_xml_dict(self) -> dict:
        return {
            "FileName": self.file_name,
            "FileFormat": self.file_format,
            "FileSize": self.file_size,
            "Checksum": self.checksum,
            "Description": self.description,
            "SourcePath": "",  # not persisted — runtime path only
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "AdditionalCADModel":
        return AdditionalCADModel(
            file_name=d.get("FileName", ""),
            file_format=d.get("FileFormat", ""),
            file_size=d.get("FileSize", ""),
            checksum=d.get("Checksum", ""),
            description=d.get("Description", ""),
            source_path=d.get("SourcePath", ""),
        )


@dataclass
class ReferenceImage:
    file_name: str = ""
    file_format: str = ""
    file_size: str = ""
    checksum: str = ""
    description: str = ""
    source_path: str = ""

    def to_xml_dict(self) -> dict:
        return {
            "FileName": self.file_name,
            "FileFormat": self.file_format,
            "FileSize": self.file_size,
            "Checksum": self.checksum,
            "Description": self.description,
            "SourcePath": "",  # not persisted — runtime path only
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "ReferenceImage":
        return ReferenceImage(
            file_name=d.get("FileName", ""),
            file_format=d.get("FileFormat", ""),
            file_size=d.get("FileSize", ""),
            checksum=d.get("Checksum", ""),
            description=d.get("Description", ""),
            source_path=d.get("SourcePath", ""),
        )


@dataclass
class OptionalData:
    additional_cad: List[AdditionalCADModel] = field(default_factory=list)
    images: List[ReferenceImage] = field(default_factory=list)

    def to_xml_dict(self) -> dict:
        return {
            "AdditionalCAD": [c.to_xml_dict() for c in self.additional_cad],
            "Images": [i.to_xml_dict() for i in self.images],
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "OptionalData":
        return OptionalData(
            additional_cad=[AdditionalCADModel.from_xml_dict(c) for c in d.get("AdditionalCAD", [])],
            images=[ReferenceImage.from_xml_dict(i) for i in d.get("Images", [])],
        )
