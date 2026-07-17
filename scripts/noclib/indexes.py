"""Deterministic feature-archive index builders."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from scripts.noclib.overview import parse_frontmatter_file
from scripts.noclib.schemas import validate_overview_frontmatter
from scripts.noclib.evidence import build_evidence_index


PROJECT_MEMORY = ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"]
DERIVED_INDEXES = [
    "noc_docs/.living-docs/routing.json",
    "noc_docs/.living-docs/feature-index.json",
    "noc_docs/.living-docs/evidence-index.json",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        Path(tmp_name).replace(path)
    except Exception:
        try:
            Path(tmp_name).unlink()
        except OSError:
            pass
        raise


def build_feature_index(target: Path) -> dict[str, Any]:
    features_root = target / "noc_docs/features"
    features: list[dict[str, Any]] = []
    if features_root.is_dir():
        for feature_dir in sorted(features_root.iterdir()):
            if not feature_dir.is_dir() or feature_dir.name.startswith("."):
                continue
            overview = feature_dir / "overview.md"
            if not overview.is_file():
                raise ValueError(f"missing {overview.relative_to(target).as_posix()}")
            frontmatter = parse_frontmatter_file(overview)
            errors = validate_overview_frontmatter(frontmatter)
            if errors:
                raise ValueError(f"{overview.relative_to(target).as_posix()} invalid: {'; '.join(errors)}")
            features.append(
                {
                    "id": frontmatter["id"],
                    "name": frontmatter["name"],
                    "aliases": frontmatter.get("aliases", []),
                    "status": frontmatter["status"],
                    "language": frontmatter["language"],
                    "overview_path": overview.relative_to(target).as_posix(),
                    "updated_at": frontmatter["updated_at"],
                }
            )
    return {"schema_version": "1.0", "features": features}


def build_routing_index() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "protocol_version": 2,
        "layout": "feature-archive",
        "layout_version": "1.0",
        "project_memory": PROJECT_MEMORY,
        "feature_archive": {
            "root": "noc_docs/features",
            "index": "noc_docs/.living-docs/feature-index.json",
        },
        "routes": [
            {
                "path": "**",
                "read_before_code": PROJECT_MEMORY,
                "feature_index": "noc_docs/.living-docs/feature-index.json",
            }
        ],
    }


def build_manifest(target: Path, generated: dict[str, str]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted((target / "noc_docs").rglob("*.md")):
        rel = path.relative_to(target).as_posix()
        data = path.read_bytes()
        files[rel] = {"sha256": sha256_bytes(data), "bytes": len(data), "role": "fact"}
    config = target / "noc_docs/.living-docs/config.json"
    if config.is_file():
        rel = config.relative_to(target).as_posix()
        data = config.read_bytes()
        files[rel] = {"sha256": sha256_bytes(data), "bytes": len(data), "role": "config"}
    for rel, content in sorted(generated.items()):
        data = content.encode("utf-8")
        files[rel] = {"sha256": sha256_bytes(data), "bytes": len(data), "role": "derived"}
    return {
        "schema_version": "1.0",
        "protocol_version": 2,
        "layout": "feature-archive",
        "layout_version": "1.0",
        "fact_sources": [*PROJECT_MEMORY, "noc_docs/features/*/overview.md"],
        "derived_files": [*DERIVED_INDEXES, "noc_docs/.living-docs/manifest.json"],
        "files": files,
    }


def build_feature_archive_indexes(target: Path) -> dict[str, str]:
    payloads: dict[str, dict[str, Any]] = {
        "noc_docs/.living-docs/routing.json": build_routing_index(),
        "noc_docs/.living-docs/feature-index.json": build_feature_index(target),
        "noc_docs/.living-docs/evidence-index.json": build_evidence_index(target),
    }
    rendered = {rel: stable_json(payload) for rel, payload in payloads.items()}
    rendered["noc_docs/.living-docs/manifest.json"] = stable_json(build_manifest(target, rendered))
    return rendered


def write_feature_archive_indexes(target: Path) -> None:
    rendered = build_feature_archive_indexes(target)
    for rel, content in rendered.items():
        atomic_write_text(target / rel, content)
