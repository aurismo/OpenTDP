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

# models/version.py
from dataclasses import dataclass, field
from typing import List


@dataclass
class ChangeEntry:
    change_id: str = ""
    timestamp: str = ""
    author: str = ""
    description: str = ""
    # The package content-checksum at the moment this entry was recorded.
    # Purely an audit-trail record — it carries no fieldId and is therefore
    # never itself part of the checksum calculation (see
    # services/tdp_io.py:_field_entries, which only ever includes elements
    # tagged with a fieldId). Lets anyone compare consecutive entries to see
    # at a glance whether the package's actual content changed between two
    # saves, or only bookkeeping (timestamp, change id) did.
    checksum: str = ""

    def to_xml_dict(self) -> dict:
        return {
            "ChangeID": self.change_id,
            "Timestamp": self.timestamp,
            "Author": self.author,
            "Description": self.description,
            "Checksum": self.checksum,
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "ChangeEntry":
        return ChangeEntry(
            change_id=d.get("ChangeID", ""),
            timestamp=d.get("Timestamp", ""),
            author=d.get("Author", ""),
            description=d.get("Description", ""),
            checksum=d.get("Checksum", ""),
        )


@dataclass
class VersionInfo:
    unique_id: str = ""
    assembly_id: str = ""
    revision: str = ""
    checksum: str = ""
    signature: str = ""
    encryption_enabled: bool = False
    encryption_algorithm: str = ""
    change_history: List[ChangeEntry] = field(default_factory=list)

    def to_xml_dict(self) -> dict:
        return {
            "UniqueID": self.unique_id,
            "AssemblyID": self.assembly_id,
            "Revision": self.revision,
            "Checksum": self.checksum,
            "Signature": self.signature,
            "EncryptionEnabled": "true" if self.encryption_enabled else "false",
            "EncryptionAlgorithm": self.encryption_algorithm,
            "ChangeHistory": [e.to_xml_dict() for e in self.change_history],
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "VersionInfo":
        return VersionInfo(
            unique_id=d.get("UniqueID", ""),
            assembly_id=d.get("AssemblyID", ""),
            revision=d.get("Revision", ""),
            checksum=d.get("Checksum", ""),
            signature=d.get("Signature", ""),
            encryption_enabled=d.get("EncryptionEnabled", "false") == "true",
            encryption_algorithm=d.get("EncryptionAlgorithm", ""),
            change_history=[
                ChangeEntry.from_xml_dict(e) for e in d.get("ChangeHistory", [])
            ],
        )
