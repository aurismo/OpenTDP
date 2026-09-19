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

# services/json_serializer.py
"""
Builds TDP.json: the same data as TDP.xml, but every key is "d<fieldId>"
(e.g. "d10020") — never a plain-language tag name. TDP.xml (via
xml_serializer.to_xml_string) is the single source of truth for which
fieldId belongs to which value, so this module parses the generated XML
rather than walking the package model again; the two files can never
disagree about a field's identity.

Shape rules:
  - A leaf field becomes its text as a plain JSON string, under "d<fieldId>".
  - A repeating group (multiple GeometryFile, ProcessOption, Step,
    ChangeEntry, Attachment, Parameter, ... ) becomes a JSON array. Where
    the group's container element has no fieldId of its own in TDP.xml, a
    synthetic id from _SYNTHETIC_IDS is used purely as a stable numeric
    key — it is never a spec-numbered field.
  - A non-repeating, fieldId-less wrapper (e.g. Quality/Traceability,
    Quality/Risks, Quality/Approval, Step/Duration) is flattened directly
    into its parent object rather than needing a key of its own.
  - Parameter is a special case: fieldId 15900 tags the element and its
    @name attribute, while its own text is the value (fieldId 15910 by
    convention — see models/manufacturing.py). Represented as
    {"d15900": name, "d15910": value} per instance.
  - ChangeEntry/Checksum (the per-save audit checksum — see
    models/version.py) deliberately carries no fieldId in TDP.xml so it
    never enters the package checksum calculation; it still needs a
    numeric key here, so a synthetic one is used.
"""
import json
import xml.etree.ElementTree as ET

from models.tdp_package import TDPPackage
from services import xml_serializer

# Containers that hold a repeating group of records and carry no fieldId
# of their own in TDP.xml. Every direct child becomes one array item.
# Mapped to the synthetic (non-spec) id used as this list's own key.
_LIST_CONTAINERS = {
    "ChangeHistory": "11090",   # -> array of ChangeEntry
    "Geometry": "12000",        # -> array of GeometryFile
    "ProcessOptions": "14000",  # -> array of ProcessOption
    "Steps": "15005",           # -> array of Step (per ProcessOption)
    "BuildFiles": "16000",      # -> array of BuildFile
    "AdditionalCAD": "17000",   # -> array of CADFile
    "Images": "17090",          # -> array of Image
    "Attachments": "15940",     # -> array of Attachment (per Step)
    "Parameters": "15890",      # -> array of {"d15900": name, "d15910": value}
}

# Other fieldId-less elements that carry real (non-empty) leaf data and
# need a synthetic numeric key, keyed as "<tag>@<parent tag>" to keep them
# unambiguous from any same-named element elsewhere that DOES already
# carry a real fieldId (e.g. Version/Checksum, Geometry/Checksum, ...).
_SYNTHETIC_LEAF_IDS = {
    "Checksum@ChangeEntry": "11095",  # per-save audit checksum
    "id@ProcessOption": "14005",      # internal archive-folder id, not spec-numbered
}


def _convert(el: ET.Element):
    """Recursively convert one XML element into a JSON-safe Python value."""
    tag = el.tag

    if tag == "Parameter":
        return {
            "d15900": el.get("name", ""),
            "d15910": (el.text or "").strip(),
        }

    if tag in _LIST_CONTAINERS:
        return [_convert(c) for c in el]

    children = list(el)
    if not children:
        return (el.text or "").strip()

    # A generic repeating group whose children carry no fieldId of their
    # own, but whose CONTAINER already has a real fieldId of its own
    # (e.g. InspectionMethods/Method, HazmatClasses/Class) — the id lives
    # on the container, so this only needs to collapse the children into
    # a plain list; no synthetic id is needed here.
    tags = {c.tag for c in children}
    if len(tags) == 1 and all(c.get("fieldId") is None for c in children):
        return [_convert(c) for c in children]

    result = {}
    for c in children:
        ctag = c.tag
        fid = c.get("fieldId")
        if not fid:
            fid = _LIST_CONTAINERS.get(ctag) or _SYNTHETIC_LEAF_IDS.get(f"{ctag}@{tag}")
        value = _convert(c)

        if fid:
            key = f"d{fid}"
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        elif isinstance(value, dict):
            # Non-repeating, fieldId-less wrapper (e.g. Traceability,
            # Risks, Approval, Duration, Standards, Inputs, Outputs,
            # BuildFileRefs) — flatten directly into this object.
            result.update(value)
        elif value not in ("", [], {}):
            # A fieldId-less element with real data we don't yet have a
            # mapping for. Fail loudly rather than silently dropping data
            # — add it to _SYNTHETIC_LEAF_IDS / _LIST_CONTAINERS above.
            raise ValueError(
                f"TDP.json: no fieldId or synthetic id for <{ctag}> "
                f"under <{tag}> (value={value!r})"
            )
    return result


def to_json_string(package: TDPPackage) -> str:
    """Build the TDP.json text for a package (see module docstring)."""
    xml_str = xml_serializer.to_xml_string(package)
    root = ET.fromstring(xml_str)
    data = _convert(root)
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
