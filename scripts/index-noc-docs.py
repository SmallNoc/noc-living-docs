#!/usr/bin/env python3
"""Build lightweight routing indexes for NOC Living Docs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DOC_ROOT = "noc_docs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index noc_docs for agent routing.")
    parser.add_argument("target", nargs="?", default=".", help="Project directory containing noc_docs.")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def summary(text: str) -> str:
    lines = []
    in_frontmatter = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not lines:
            in_frontmatter = True
            continue
        if stripped == "---" and in_frontmatter:
            in_frontmatter = False
            continue
        if in_frontmatter or not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
        if len(" ".join(lines)) > 240:
            break
    return " ".join(lines)[:320]


def tags_for(path: Path) -> list[str]:
    parts = [p.lower() for p in path.parts]
    tags = []
    for key in [
        "requirements",
        "status",
        "guardrails",
        "test-record",
        "change-record",
        "agent-guide",
        "notes",
        "development",
        "features",
        "domains",
    ]:
        if key in path.name.lower() or key in parts:
            tags.append(key)
    return sorted(set(tags))


def detect_mode(noc_docs: Path) -> str:
    if (noc_docs / "domains").exists() and not (noc_docs / "features").exists():
        return "domain"
    if (noc_docs / "domains").exists():
        return "domain"
    return "small"


def load_config(noc_docs: Path) -> dict:
    path = noc_docs / ".living-docs/config.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def index_simplified(target: Path, noc_docs: Path) -> None:
    index_dir = noc_docs / ".living-docs"
    routing_path = index_dir / "routing.json"
    manifest_path = index_dir / "manifest.json"
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = {}
    for relative in manifest.get("managed_files", []):
        path = target / relative
        if path.is_file() and path != manifest_path:
            files[relative] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    manifest.update(protocol_version=2, layout="simplified", files=files)
    routing.update(protocol_version=2, layout="simplified")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    routing_path.write_text(json.dumps(routing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_existing_feature_map(noc_docs: Path) -> dict:
    path = noc_docs / ".living-docs/feature-map.json"
    if not path.exists():
        return {"features": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"features": {}}


def build_feature_map(target: Path, noc_docs: Path, mode: str) -> dict:
    result: dict = {"mode": mode, "features": {}}
    existing = load_existing_feature_map(noc_docs).get("features", {})

    if mode == "domain":
        for feature_dir in sorted(noc_docs.glob("domains/*/features/*")):
            if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
                continue
            domain = feature_dir.parts[-3]
            feature_id = feature_dir.name
            result["features"][feature_id] = feature_entry(target, feature_dir, domain, existing.get(feature_id, {}))
    else:
        for feature_dir in sorted((noc_docs / "features").glob("*")) if (noc_docs / "features").exists() else []:
            if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
                continue
            result["features"][feature_dir.name] = feature_entry(target, feature_dir, None, existing.get(feature_dir.name, {}))

    return result


def feature_entry(target: Path, feature_dir: Path, domain: str | None, existing: dict) -> dict:
    def rel(name: str) -> str:
        return (feature_dir / name).relative_to(target).as_posix()

    doc_names = {
        "agent-guide.md": "entry",
        "requirements.md": "requirements",
        "status.md": "status",
        "guardrails.md": "guardrails",
        "test-record.md": "tests",
        "change-record.md": "change_record",
        "notes.md": "notes",
    }
    existing_docs = [feature_dir / name for name in doc_names if (feature_dir / name).exists()]
    missing_docs = [name for name in doc_names if not (feature_dir / name).exists()]
    last_doc_update = None
    if existing_docs:
        last_doc_update = datetime.fromtimestamp(
            max(path.stat().st_mtime for path in existing_docs),
            timezone.utc,
        ).isoformat()

    preserved = {
        key: value
        for key, value in existing.items()
        if key
        not in {
            "entry",
            "requirements",
            "status",
            "guardrails",
            "tests",
            "change_record",
            "notes",
            "domain",
            "freshness",
            "completeness",
        }
    }
    entry = {
        **preserved,
        **{field: rel(name) for name, field in doc_names.items()},
        "freshness": {
            "last_doc_update": last_doc_update,
            "last_indexed": datetime.now(timezone.utc).isoformat(),
        },
        "completeness": {
            "required_docs": sorted(doc_names),
            "missing_docs": missing_docs,
            "complete": not missing_docs,
        },
    }
    entry.setdefault("paths", [])
    if domain:
        entry["domain"] = domain
    return entry


def main() -> None:
    args = parse_args()
    target = Path(args.target).resolve()
    noc_docs = target / DOC_ROOT
    if not noc_docs.exists():
        raise SystemExit(f"ERROR: {noc_docs} does not exist")

    config = load_config(noc_docs)
    if config.get("protocol_version") == 2 and config.get("layout") == "simplified":
        index_simplified(target, noc_docs)
        print("Indexed simplified project memory.")
        return

    index_dir = noc_docs / ".living-docs"
    index_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    manifest = {"generated_at": now, "files": {}}
    docs_index = {"generated_at": now, "documents": {}}

    for path in sorted(noc_docs.rglob("*.md")):
        rel = path.relative_to(target).as_posix()
        text = path.read_text(encoding="utf-8")
        manifest["files"][rel] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "last_indexed": now,
        }
        docs_index["documents"][rel] = {
            "title": first_heading(text),
            "summary": summary(text),
            "tags": tags_for(path.relative_to(noc_docs)),
        }

    mode = detect_mode(noc_docs)
    feature_map = build_feature_map(target, noc_docs, mode)

    (index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (index_dir / "docs-index.json").write_text(json.dumps(docs_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (index_dir / "feature-map.json").write_text(json.dumps(feature_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Indexed {len(manifest['files'])} document(s).")
    print(f"Mode: {mode}")
    print(f"Features: {len(feature_map['features'])}")


if __name__ == "__main__":
    main()
