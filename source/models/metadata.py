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

# models/metadata.py
from dataclasses import dataclass


@dataclass
class Metadata:
    tdp_id: str = ""
    additional_ids: str = ""
    name: str = ""
    description: str = ""
    version: str = ""
    created_date: str = ""
    modified_date: str = ""
    lifecycle_status: str = "Draft"
    author: str = ""
    organization: str = ""
    contact: str = ""
    licensing: str = ""
    information_classification: str = "Internal"
    confidentiality_level: str = ""
    criticality_level: str = ""   # computed from Quality risk scores, not user-editable

    def to_xml_dict(self) -> dict:
        return {
            "TDP_ID": self.tdp_id,
            "AdditionalIDs": self.additional_ids,
            "Name": self.name,
            "Description": self.description,
            "Version": self.version,
            "CreatedDate": self.created_date,
            "ModifiedDate": self.modified_date,
            "LifecycleStatus": self.lifecycle_status,
            "Author": self.author,
            "Organization": self.organization,
            "Contact": self.contact,
            "Licensing": self.licensing,
            "InformationClassification": self.information_classification,
            "ConfidentialityLevel": self.confidentiality_level,
            "CriticalityLevel": self.criticality_level,
        }

    @staticmethod
    def from_xml_dict(d: dict) -> "Metadata":
        return Metadata(
            tdp_id=d.get("TDP_ID", ""),
            additional_ids=d.get("AdditionalIDs", ""),
            name=d.get("Name", ""),
            description=d.get("Description", ""),
            version=d.get("Version", ""),
            created_date=d.get("CreatedDate", ""),
            modified_date=d.get("ModifiedDate", ""),
            lifecycle_status=d.get("LifecycleStatus", "Draft"),
            author=d.get("Author", ""),
            organization=d.get("Organization", ""),
            contact=d.get("Contact", ""),
            licensing=d.get("Licensing", ""),
            information_classification=d.get("InformationClassification", "Internal"),
            confidentiality_level=d.get("ConfidentialityLevel", ""),
            criticality_level=d.get("CriticalityLevel", "Low"),
        )
