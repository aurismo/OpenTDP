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

# services/tdp_io.py
"""
Handles all disk I/O for TDP packages.

A .tdp file is a ZIP archive containing:
  TDP.xml          — the main XML document
  Geometry/        — geometry files (STL, 3MF only; open triangle-mesh formats)
  BuildFiles/      — AM build files (gcode, 3mf, …)
  Optional/CAD/    — additional CAD models
  Optional/Images/ — reference images
  Attachments/     — step attachments (flat, prefixed by step id)
"""
import os
import re
import shutil
import zipfile
import hashlib
import uuid
import getpass
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Tuple

from models.tdp_package import TDPPackage
from models.version import ChangeEntry
from services import xml_serializer
from services import json_serializer
from services import checksum_service


class TDPSaveError(Exception):
    pass


class TDPLoadError(Exception):
    pass


# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------

def save_tdp(output_path: str, package: TDPPackage, author: str = "",
             history_source_dir: str = None) -> None:
    """
    Refresh all checksums, record a ChangeEntry, serialise to XML,
    copy all referenced files, and write a .tdp ZIP archive.

    history_source_dir: the extraction directory of the .tdp file this
    package was loaded from (main_window.py's self._extract_dir), if any.
    Since each save rewrites the .tdp archive from scratch, this lets every
    prior History/<ChangeID>.txt debug dump be carried forward into the new
    archive instead of being lost.
    """
    output_path = str(output_path)
    if not output_path.endswith(".tdp"):
        output_path += ".tdp"

    # 1. Refresh all file checksums
    checksum_service.refresh_geometry_checksums(package.geometry)
    checksum_service.refresh_buildfile_checksums(package.build_files)
    checksum_service.refresh_optional_checksums(package.optional)
    checksum_service.refresh_attachment_checksums(package.process_options)

    # 2. Modified Date is automatic and updated on every save (spec 10070),
    #    regardless of which tab was actually edited.
    package.metadata.modified_date = datetime.now().strftime("%Y-%m-%d")

    # 3. Compute the package content checksum: SHA-256 over a canonical,
    #    fieldId-ordered string built from the package data, excluding the
    #    checksum field itself and the always-changes-on-save bookkeeping
    #    fields (spec 1.4; see compute_package_checksum for the exact
    #    exclusion list). Computed BEFORE the ChangeEntry is created so
    #    that entry can record this exact value.
    checksum_entries, checksum_canonical = _build_checksum_input(package)
    content_checksum = hashlib.sha256(checksum_canonical.encode("utf-8")).hexdigest()
    package.version.checksum = content_checksum

    # 4. Add automatic ChangeEntry, stamped with the checksum computed
    #    above — an append-only audit trail of what the content checksum
    #    was at each save. Consecutive entries showing the same value is
    #    the direct, visible proof that no real content changed between
    #    two saves, even though Timestamp/ChangeID always differ.
    entry = _record_change_entry(package, author, content_checksum)

    # 5. Build this save's debug dump, prefixed with who was logged in
    #    (the OS account) and which application "Author" / ChangeID it
    #    belongs to, and drop a loose copy next to the .tdp for quick
    #    inspection without unzipping anything.
    try:
        os_user = getpass.getuser()
    except Exception:
        os_user = "unknown"
    debug_text = _build_checksum_debug_text(
        checksum_entries, checksum_canonical, content_checksum,
        change_id=entry.change_id, author=entry.author, os_user=os_user,
    )
    _write_loose_debug_file(output_path, debug_text)

    # 6. Generate XML (now includes the final checksum and change entry)
    xml_str = xml_serializer.to_xml_string(package)

    # 6b. Generate TDP.json: the same data, keyed purely by "d<fieldId>"
    #     (see json_serializer module docstring). Built from the XML
    #     above, so the two files can never disagree on field identity.
    json_str = json_serializer.to_json_string(package)

    # 7. Write ZIP
    tmp_path = output_path + ".tmp"
    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("TDP.xml", xml_str.encode("utf-8"))
            zf.writestr("TDP.json", json_str.encode("utf-8"))
            _pack_geometries(zf, package)
            _pack_build_files(zf, package)
            _pack_optional(zf, package)
            _pack_attachments(zf, package)

            # History/: one debug dump per save, permanently kept inside
            # the archive and named by that save's ChangeID. The archive
            # is rebuilt from scratch every save, so carry forward every
            # History/*.txt already present in the file being re-saved
            # before adding this save's own entry.
            carried_forward = set()
            if history_source_dir:
                history_dir = os.path.join(history_source_dir, "History")
                if os.path.isdir(history_dir):
                    for fname in sorted(os.listdir(history_dir)):
                        fpath = os.path.join(history_dir, fname)
                        if os.path.isfile(fpath):
                            arcname = f"History/{fname}"
                            zf.write(fpath, arcname)
                            carried_forward.add(arcname)
            new_history_arcname = history_arcname(entry.change_id)
            if new_history_arcname not in carried_forward:
                zf.writestr(new_history_arcname, debug_text)

        # Atomic replace
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(tmp_path, output_path)
    except Exception as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise TDPSaveError(f"Failed to write TDP: {exc}") from exc


def _record_change_entry(package: TDPPackage, author: str, checksum: str) -> ChangeEntry:
    entry = ChangeEntry(
        change_id=f"CH-{uuid.uuid4().hex[:8].upper()}",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        author=author or package.metadata.author or "Unknown",
        description="Package saved",
        checksum=checksum,
    )
    package.version.change_history.append(entry)
    return entry


# Fields deliberately excluded from the package checksum. Everything else
# tagged with a fieldId anywhere in TDP.xml — including every individual
# file's own SHA-256 (Geometry, BuildFiles, Attachments, Optional CAD/
# Images) — is included, so the checksum still changes whenever any real
# content or referenced file changes.
_CHECKSUM_EXCLUDED_FIELD_IDS = {
    11040,  # Version/Checksum itself — self-referential, must be excluded
    11100,  # ChangeHistory/ChangeEntry/ChangeID    — fresh random id every save
    11110,  # ChangeHistory/ChangeEntry/Timestamp   — save-time clock value
    11120,  # ChangeHistory/ChangeEntry/Author       \  bookkeeping about the
    11130,  # ChangeHistory/ChangeEntry/Description  /  save event, not content
    10070,  # Metadata/ModifiedDate — auto-stamped to "today" on every save
}


def _field_entries(root: ET.Element):
    """
    Yield (field_id, doc_order, sub_order, attrs, text) for every value in
    the document that carries a fieldId, in document order. Covers both:
      - plain leaf fields, e.g. <TDP_ID fieldId="10010">TDP-0001</TDP_ID>
      - a fieldId-tagged container whose untagged children each hold one
        value of a repeating field, e.g. <InspectionMethods fieldId="15600">
        <Method>...</Method><Method>...</Method></InspectionMethods>
    Element attributes other than fieldId (e.g. Parameter/@name) are
    included alongside the text so they are not silently dropped.
    """
    for doc_order, el in enumerate(root.iter()):
        fid = el.get("fieldId")
        if not fid:
            continue
        attrs = tuple(sorted((k, v) for k, v in el.attrib.items() if k != "fieldId"))
        untagged_children = [c for c in el if c.get("fieldId") is None]
        if untagged_children:
            for sub_order, child in enumerate(untagged_children):
                yield (int(fid), doc_order, sub_order, (), (child.text or "").strip())
        else:
            yield (int(fid), doc_order, 0, attrs, (el.text or "").strip())


def _build_checksum_input(package: TDPPackage):
    """
    Build the ordered list of (field_id, doc_order, sub_order, attrs, text)
    entries and the resulting canonical string used for the package
    checksum. Shared by compute_package_checksum() and the
    checksum_debug.txt writer so both always see exactly the same data.
    """
    xml_str = xml_serializer.to_xml_string(package)
    root = ET.fromstring(xml_str)

    entries = [
        e for e in _field_entries(root)
        if e[0] not in _CHECKSUM_EXCLUDED_FIELD_IDS
    ]
    entries.sort(key=lambda e: (e[0], e[1], e[2]))

    parts = []
    for fid, _, _, attrs, text in entries:
        attr_part = ";".join(f"{k}={v}" for k, v in attrs)
        parts.append(f"{fid}\x1f{attr_part}\x1f{text}")
    canonical = "\x1e".join(parts)
    return entries, canonical


def compute_package_checksum(package: TDPPackage) -> str:
    """
    SHA-256 of a canonical string built from every fieldId-tagged value in
    the package, ordered numerically by fieldId (the same field index used
    throughout TDP.xml and the specification), then by document order for
    repeated fields (e.g. multiple GeometryFile records).

    Excludes the fields in _CHECKSUM_EXCLUDED_FIELD_IDS — see that constant
    for why. Built directly from the generated XML, so runtime-only data
    that is never written to TDP.xml (e.g. source_path) is automatically
    absent without needing separate stripping.

    Public: this is the ONE place the package checksum is computed, used
    by save_tdp() and by anything that needs to preview/verify it (e.g.
    the Version tab's "Preview" button) — nothing else should hash the
    package independently, or it will drift out of sync with what save_tdp
    actually produces.

    Any consumer can reproduce and verify this value by parsing TDP.xml,
    applying the same field selection/ordering/exclusion rules, and
    hashing the resulting string the same way.
    """
    _, canonical = _build_checksum_input(package)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def history_arcname(change_id: str) -> str:
    """Archive path for a save's permanent History debug dump."""
    return f"History/{_safe_component(change_id, 'entry')}.txt"


def _build_checksum_debug_text(entries, canonical: str, checksum: str, *,
                                change_id: str = "", author: str = "",
                                os_user: str = "") -> str:
    """
    Build the human-readable checksum debug dump text: every field that
    went into the package checksum, in the exact order concatenated, plus
    the assembled canonical string and the resulting SHA-256 — prefixed
    with who was logged into the OS and which change entry this save
    corresponds to, so the audit trail in History/ is self-identifying.
    """
    lines = [
        f"OS user account logged in at save time : {os_user}",
        f"Application 'Author' recorded for save : {author}",
        f"Change History entry (ChangeID)        : {change_id}",
        "=" * 78,
        "",
        "TDP package checksum debug dump",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Fields included in the checksum, in the exact order they are",
        "concatenated (sorted by fieldId, then document order):",
        "-" * 78,
        f"{'fieldId':>8}  {'attrs':<30}  text",
        "-" * 78,
    ]
    for fid, _doc_order, _sub_order, attrs, text in entries:
        attr_str = ";".join(f"{k}={v}" for k, v in attrs)
        lines.append(f"{fid:>8}  {attr_str:<30}  {text!r}")
    lines += [
        "-" * 78,
        "",
        "Fields deliberately excluded (never affect the checksum):",
    ]
    for fid in sorted(_CHECKSUM_EXCLUDED_FIELD_IDS):
        lines.append(f"  {fid}")
    lines += [
        "",
        "Canonical string that gets hashed",
        "(field separator = 0x1F, entry separator = 0x1E, shown here as | and § ):",
        canonical.replace("\x1f", "|").replace("\x1e", " § "),
        "",
        f"SHA-256 (Version/Checksum): {checksum}",
    ]
    return "\n".join(lines)


def _write_loose_debug_file(output_path: str, debug_text: str) -> None:
    """
    Write the latest checksum_debug.txt next to output_path — a quick,
    no-unzip-needed copy of the most recent save's debug dump. The
    permanent, per-save history lives inside the archive under History/
    (see history_arcname / save_tdp).
    """
    debug_dir = os.path.dirname(os.path.abspath(output_path)) or "."
    debug_path = os.path.join(debug_dir, "checksum_debug.txt")
    try:
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(debug_text)
    except OSError:
        # Debug output is a convenience, not part of the .tdp itself —
        # never let a failure to write it break the actual save.
        pass


def _pack_geometries(zf: zipfile.ZipFile, package: TDPPackage) -> None:
    for g in package.geometry:
        if g.source_path and os.path.exists(g.source_path):
            zf.write(g.source_path, f"Geometry/{g.file_name}")


def _pack_build_files(zf: zipfile.ZipFile, package: TDPPackage) -> None:
    for bf in package.build_files:
        if bf.source_path and os.path.exists(bf.source_path):
            zf.write(bf.source_path, f"BuildFiles/{bf.file_name}")


def _pack_optional(zf: zipfile.ZipFile, package: TDPPackage) -> None:
    for cad in package.optional.additional_cad:
        if cad.source_path and os.path.exists(cad.source_path):
            zf.write(cad.source_path, f"Optional/CAD/{cad.file_name}")
    for img in package.optional.images:
        if img.source_path and os.path.exists(img.source_path):
            zf.write(img.source_path, f"Optional/Images/{img.file_name}")


def _attachment_file_name(step_id: str, file_name: str) -> str:
    """
    Legacy (v20260909a-fix1) flat file name for a step attachment:
    "<StepID>_<filename>". Kept only so .tdp files saved by that
    intermediate build can still have their attachments located on load;
    new saves use attachment_arc_dir() instead (Manufacturing/<Option>/<Step>/).
    """
    return f"{step_id}_{file_name}"


def _safe_component(value: str, fallback: str) -> str:
    """Sanitise a string for use as a single archive/folder path segment."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", (value or "").strip())
    return cleaned or fallback


def attachment_arc_dir(option_id: str, step_id: str) -> str:
    """
    Folder (with trailing slash) inside a .tdp archive for a given Process
    Option's Process Step attachments:

        Manufacturing/<ProcessOption>/<ProcessStep>/

    One folder per Process Option, and inside it one folder per Process
    Step, mirroring how the Manufacturing tab organises options and steps.
    Used by both the packer (tdp_io) and the exporter (ui/step_editor.py)
    so the two can never drift out of sync.
    """
    opt_folder = _safe_component(option_id, "Option")
    step_folder = _safe_component(step_id, "Step")
    return f"Manufacturing/{opt_folder}/{step_folder}/"


def _pack_attachments(zf: zipfile.ZipFile, package: TDPPackage) -> None:
    for opt in package.process_options:
        for step in opt.steps:
            for att in step.attachments:
                if att.source_path and os.path.exists(att.source_path):
                    arcname = attachment_arc_dir(opt.id, step.id) + att.file_name
                    zf.write(att.source_path, arcname)


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------

def load_tdp(tdp_path: str) -> Tuple[TDPPackage, str]:
    """
    Extract a .tdp archive to a temp directory, parse the XML,
    and fix all SourcePath references to point at the extracted files.
    Returns (package, extracted_dir) — caller is responsible for cleanup.
    """
    tdp_path = str(tdp_path)
    if not os.path.exists(tdp_path):
        raise TDPLoadError(f"File not found: {tdp_path}")

    extract_dir = tdp_path + "_extracted"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    try:
        with zipfile.ZipFile(tdp_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as exc:
        raise TDPLoadError(f"Failed to extract TDP: {exc}") from exc

    xml_path = os.path.join(extract_dir, "TDP.xml")
    if not os.path.exists(xml_path):
        raise TDPLoadError("TDP.xml missing from archive")

    try:
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_str = f.read()
        package = xml_serializer.from_xml_string(xml_str)
    except Exception as exc:
        raise TDPLoadError(f"Failed to parse TDP.xml: {exc}") from exc

    # Repoint SourcePaths to extracted location
    _repoint_paths(package, extract_dir)

    return package, extract_dir


def _repoint_paths(package: TDPPackage, base: str) -> None:
    for g in package.geometry:
        candidate = os.path.join(base, "Geometry", g.file_name)
        if os.path.exists(candidate):
            g.source_path = candidate

    for bf in package.build_files:
        candidate = os.path.join(base, "BuildFiles", bf.file_name)
        if os.path.exists(candidate):
            bf.source_path = candidate

    for cad in package.optional.additional_cad:
        candidate = os.path.join(base, "Optional", "CAD", cad.file_name)
        if os.path.exists(candidate):
            cad.source_path = candidate

    for img in package.optional.images:
        candidate = os.path.join(base, "Optional", "Images", img.file_name)
        if os.path.exists(candidate):
            img.source_path = candidate

    for opt in package.process_options:
        for step in opt.steps:
            for att in step.attachments:
                # 1. Current layout: Manufacturing/<OptionID>/<StepID>/<file>
                candidate = os.path.join(
                    base, *attachment_arc_dir(opt.id, step.id).split("/")[:-1],
                    att.file_name,
                )
                if os.path.exists(candidate):
                    att.source_path = candidate
                    continue
                # 2. Legacy fallback: Attachments/<StepID>_<file> (fix1 build)
                legacy_flat = os.path.join(
                    base, "Attachments", _attachment_file_name(step.id, att.file_name)
                )
                if os.path.exists(legacy_flat):
                    att.source_path = legacy_flat
                    continue
                # 3. Legacy fallback: Attachments/<StepID>/<file> (original build)
                legacy_nested = os.path.join(base, "Attachments", step.id, att.file_name)
                if os.path.exists(legacy_nested):
                    att.source_path = legacy_nested
