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


def refresh_geometry_checksums(geometries) -> None:
    for g in geometries:
        g.checksum = file_checksum(g.source_path)


def refresh_buildfile_checksums(build_files) -> None:
    for bf in build_files:
        bf.checksum = file_checksum(bf.source_path)


def refresh_optional_checksums(optional) -> None:
    for cad in optional.additional_cad:
        cad.checksum = file_checksum(cad.source_path)
    for img in optional.images:
        img.checksum = file_checksum(img.source_path)


def refresh_attachment_checksums(steps) -> None:
    for option in steps:
        for step in option.steps:
            for att in step.attachments:
                att.checksum = file_checksum(att.source_path)
