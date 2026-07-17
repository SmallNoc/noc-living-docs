"""Read-only NOC documentation layout detection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LayoutInfo:
    protocol_version: int | None
    layout: str
    layout_version: str | None
    mode: str | None
    documentation_root: str
    config_path: Path | None


def load_config(target: Path) -> dict[str, Any]:
    path = target / "noc_docs/.living-docs/config.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def detect_layout(target: Path) -> LayoutInfo:
    config_path = target / "noc_docs/.living-docs/config.json"
    config = load_config(target)
    documentation_root = str(config.get("documentation_root") or "noc_docs")
    protocol_version = config.get("protocol_version")
    mode = config.get("mode")
    layout = config.get("layout")
    layout_version = config.get("layout_version")

    if protocol_version == 2:
        if layout == "simplified":
            return LayoutInfo(2, "simplified", layout_version or "1.0", None, documentation_root, config_path)
        if layout == "feature-archive":
            return LayoutInfo(2, "feature-archive", layout_version, None, documentation_root, config_path)
        return LayoutInfo(2, str(layout or "unknown"), layout_version, None, documentation_root, config_path)

    if mode == "domain":
        return LayoutInfo(1, "domain", None, "domain", documentation_root, config_path)
    if mode == "small":
        return LayoutInfo(1, "small", None, "small", documentation_root, config_path)

    noc_docs = target / documentation_root
    if (noc_docs / "domains").is_dir() and not (noc_docs / "features").is_dir():
        return LayoutInfo(1, "domain", None, "domain", documentation_root, config_path if config_path.exists() else None)
    return LayoutInfo(1 if noc_docs.exists() else None, "small", None, "small", documentation_root, config_path if config_path.exists() else None)


def is_simplified_v2(info: LayoutInfo) -> bool:
    return info.protocol_version == 2 and info.layout == "simplified"


def is_feature_archive_v2(info: LayoutInfo) -> bool:
    return info.protocol_version == 2 and info.layout == "feature-archive" and info.layout_version == "1.0"


def is_v1_small(info: LayoutInfo) -> bool:
    return info.protocol_version == 1 and info.layout == "small"


def is_v1_domain(info: LayoutInfo) -> bool:
    return info.protocol_version == 1 and info.layout == "domain"
