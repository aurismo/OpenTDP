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

# models/tdp_package.py
from dataclasses import dataclass, field
from typing import List

from models.metadata import Metadata
from models.version import VersionInfo
from models.geometry import Geometry
from models.manufacturing import ManufacturingOverview, ProcessOption
from models.amdata import BuildFile
from models.optional import OptionalData
from models.quality import QualityData
from models.packing import PackingAndSafety


@dataclass
class TDPPackage:
    metadata: Metadata = field(default_factory=Metadata)
    version: VersionInfo = field(default_factory=VersionInfo)
    geometry: List[Geometry] = field(default_factory=list)
    overview: ManufacturingOverview = field(default_factory=ManufacturingOverview)
    process_options: List[ProcessOption] = field(default_factory=list)
    build_files: List[BuildFile] = field(default_factory=list)
    optional: OptionalData = field(default_factory=OptionalData)
    quality: QualityData = field(default_factory=QualityData)
    packing: PackingAndSafety = field(default_factory=PackingAndSafety)
