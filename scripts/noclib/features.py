"""Feature archive creation helpers."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from scripts.noclib.candidates import normalize_text
from scripts.noclib.indexes import write_feature_archive_indexes
from scripts.noclib.overview import default_overview_sections, parse_frontmatter_file
from scripts.noclib.schemas import is_ascii_kebab_case


RESERVED_FEATURE_IDS = {"features", "domains", "legacy", "index", "decisions", "evidence"}


def ensure_feature(
    target: Path,
    feature_id: str,
    name: str,
    aliases: list[str],
    intent: str | None,
) -> tuple[int, dict[str, Any]]:
    config = _load_config(target)
    if config.get("protocol_version") != 2 or config.get("layout") != "feature-archive":
        return 1, {"status": "error", "error": "feature ensure requires feature-archive layout"}
    id_error = validate_feature_id(feature_id)
    if id_error:
        return 1, {"status": "error", "error": id_error}
    if not name.strip():
        return 1, {"status": "error", "error": "name is required"}
    aliases = dedupe_aliases(aliases)
    features_root = target / "noc_docs/features"
    features_root.mkdir(parents=True, exist_ok=True)
    feature_dir = features_root / feature_id
    overview = feature_dir / "overview.md"
    overview_rel = overview.relative_to(target).as_posix()
    if overview.is_file():
        return 0, {"status": "existing", "feature": {"id": feature_id, "overview_path": overview_rel}}
    conflict = find_name_conflict(features_root, feature_id, name, aliases)
    if conflict:
        return 2, {"status": "conflict", "conflict": conflict}
    content = render_overview(feature_id, name.strip(), aliases, intent, str(config.get("language") or "zh-CN"))
    temporary = Path(tempfile.mkdtemp(prefix=f".{feature_id}.", dir=features_root))
    try:
        (temporary / "overview.md").write_text(content, encoding="utf-8", newline="\n")
        temporary.rename(feature_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        if feature_dir.exists() and not overview.exists():
            shutil.rmtree(feature_dir, ignore_errors=True)
        raise
    write_feature_archive_indexes(target)
    return 0, {
        "status": "created",
        "feature": {
            "id": feature_id,
            "name": name.strip(),
            "aliases": aliases,
            "overview_path": overview_rel,
        },
    }


def validate_feature_id(feature_id: str) -> str | None:
    if not feature_id:
        return "feature id is required"
    if "/" in feature_id or "\\" in feature_id or ".." in Path(feature_id).parts:
        return "feature id must be a simple ASCII kebab-case name"
    if feature_id in RESERVED_FEATURE_IDS:
        return "feature id is reserved"
    if not is_ascii_kebab_case(feature_id):
        return "feature id must be ASCII kebab-case"
    return None


def dedupe_aliases(aliases: list[str]) -> list[str]:
    result = []
    seen = set()
    for alias in aliases:
        stripped = alias.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        result.append(stripped)
    return result


def find_name_conflict(features_root: Path, feature_id: str, name: str, aliases: list[str]) -> dict[str, Any] | None:
    wanted = {normalize_text(name), *(normalize_text(alias) for alias in aliases)}
    wanted.discard("")
    if not features_root.is_dir():
        return None
    for overview in sorted(features_root.glob("*/overview.md")):
        if overview.parent.name == feature_id:
            continue
        frontmatter = parse_frontmatter_file(overview)
        existing = {normalize_text(str(frontmatter.get("name", "")))}
        existing.update(normalize_text(alias) for alias in frontmatter.get("aliases", []) if isinstance(alias, str))
        if wanted & existing:
            return {
                "id": frontmatter.get("id", overview.parent.name),
                "overview_path": overview.relative_to(features_root.parents[1]).as_posix(),
            }
    return None


def render_overview(feature_id: str, name: str, aliases: list[str], intent: str | None, language: str) -> str:
    today = date.today().isoformat()
    alias_text = "".join(f"  - {alias}\n" for alias in aliases)
    text = (
        "---\n"
        f"id: {feature_id}\n"
        f"name: {name}\n"
        "aliases:\n"
        f"{alias_text}"
        "status: proposed\n"
        "schema_version: 1\n"
        f"created_at: {today}\n"
        f"updated_at: {today}\n"
        f"language: {language}\n"
        "---\n\n"
        f"# {name}\n"
    )
    if intent:
        return text + "\n## 已确认需求\n\n" + f"- {intent.strip()}\n"
    goal = "功能目标" if language == "zh-CN" else default_overview_sections(language)[0]
    note = "待补充。该功能档案已创建，需求仍需来自用户确认或代码事实。" if language == "zh-CN" else "To be completed from confirmed user requirements or code facts."
    return text + f"\n## {goal}\n\n{note}\n"


def _load_config(target: Path) -> dict[str, Any]:
    try:
        value = json.loads((target / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}
