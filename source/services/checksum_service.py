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

# services/checksum_service.py
import hashlib
import os


def file_checksum(path: str, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    """Return hex digest of a file, or empty string if path is missing."""
    if not path or not os.path.exists(path):
        return ""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _refresh_one(obj) -> None:
    """
    Recompute obj.checksum from obj.source_path, but only when the source
    is currently reachable. If it briefly isn't (e.g. a temp extraction
    folder not yet/no longer present), keep the previously stored checksum
    instead of silently wiping it to "" — a transient path issue must not
    look like the file's content changed, and must not spuriously change
    the package-level checksum on saves where nothing actually changed.
    """
    if obj.source_path and os.path.exists(obj.source_path):
        obj.checksum = file_checksum(obj.source_path)


def refresh_geometry_checksums(geometries) -> None:
    for g in geometries:
        _refresh_one(g)


def refresh_buildfile_checksums(build_files) -> None:
    for bf in build_files:
        _refresh_one(bf)


def refresh_optional_checksums(optional) -> None:
    for cad in optional.additional_cad:
        _refresh_one(cad)
    for img in optional.images:
        _refresh_one(img)


def refresh_attachment_checksums(steps) -> None:
    for option in steps:
        for step in option.steps:
            for att in step.attachments:
                _refresh_one(att)
