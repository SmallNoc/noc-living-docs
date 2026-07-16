"""Explicit migration helpers for legacy NOC layouts."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.noclib.indexes import atomic_write_text, stable_json, write_feature_archive_indexes
from scripts.noclib.layouts import detect_layout, is_feature_archive_v2, is_simplified_v2, is_v1_domain, is_v1_small, load_config
from scripts.noclib.overview import default_overview_sections, markdown_language_from_existing


PROJECT_MEMORY = ["project.md", "guardrails.md", "verification.md"]
V1_FEATURE_DOCS = ["agent-guide.md", "requirements.md", "status.md", "guardrails.md", "test-record.md", "change-record.md", "notes.md"]
BACKUP_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}[0-9]{6}Z(?:-[0-9]+)?$")
CHINESE_SLUGS = {
    "用": "yong",
    "户": "hu",
    "登": "deng",
    "录": "lu",
    "认": "ren",
    "证": "zheng",
    "支": "zhi",
    "付": "fu",
    "订": "ding",
    "单": "dan",
    "商": "shang",
    "品": "pin",
}


class MigrationError(Exception):
    def __init__(self, status: str, message: str, *, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.payload = payload or {}


def migrate_dry_run(target: Path) -> tuple[int, dict[str, Any]]:
    try:
        plan = plan_migration(target)
    except MigrationError as error:
        return 2, error_payload(error)
    if plan["status"] == "already_target":
        return 0, plan
    plan["status"] = "dry_run"
    return 0, plan


def migrate_apply(target: Path, *, backup: bool) -> tuple[int, dict[str, Any]]:
    if not backup:
        return 2, {"status": "backup_required", "error": "migrate --apply requires --backup"}
    try:
        plan = plan_migration(target)
        if plan["status"] == "already_target":
            return 0, plan
        if not plan["can_apply"]:
            return 2, {**plan, "status": "conflict"}
        backup_info = create_migration_backup(target, reason="pre_migration")
        tmp_root = Path(tempfile.mkdtemp(prefix=".noc-migrate.", dir=target))
        try:
            staged_project = tmp_root / "project"
            shutil.copytree(target / "noc_docs", staged_project / "noc_docs")
            if plan["source_layout"] == "simplified":
                apply_simplified_to_tree(staged_project, plan)
            elif plan["source_layout"] in {"small", "domain"}:
                apply_v1_to_tree(staged_project, plan)
            else:
                raise MigrationError("unsupported_layout", f"unsupported source layout {plan['source_layout']}")
            restore_noc_docs(target, staged_project / "noc_docs", backup_info["backup_path"] / "noc_docs")
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
    except MigrationError as error:
        return 2, error_payload(error)
    except Exception as error:
        try_restore_from_latest_backup(target)
        return 2, {"status": "migration_failed", "error": str(error)}
    return 0, {
        "status": "applied",
        "source_layout": plan["source_layout"],
        "target_layout": "feature-archive",
        "operations": plan["operations"],
        "backup_id": backup_info["backup_id"],
        "backup_path": backup_info["relative_path"],
        "backup_file_count": backup_info["file_count"],
        "rollback": {
            "backup_id": backup_info["backup_id"],
            "rollback_command": f"noc migrate {target} --rollback {backup_info['backup_id']} --json",
        },
    }


def migrate_rollback(target: Path, backup_id: str) -> tuple[int, dict[str, Any]]:
    try:
        backup_path = resolve_backup_path(target, backup_id)
        validate_backup_manifest(backup_path)
        pre = create_migration_backup(target, reason="pre_rollback")
        restore_noc_docs(target, backup_path / "noc_docs", pre["backup_path"] / "noc_docs")
        layout = detect_layout(target)
    except MigrationError as error:
        return 2, error_payload(error)
    except Exception as error:
        return 2, {"status": "rollback_failed", "error": str(error)}
    return 0, {
        "status": "rolled_back",
        "backup_id": backup_id,
        "restored_file_count": count_files(target / "noc_docs"),
        "final_layout": layout.layout,
        "pre_rollback_backup_id": pre["backup_id"],
        "pre_rollback_backup_path": pre["relative_path"],
    }


def plan_migration(target: Path) -> dict[str, Any]:
    target = target.resolve()
    ensure_safe_documentation_root(target)
    info = detect_layout(target)
    if is_feature_archive_v2(info):
        return {
            "status": "already_target",
            "source_layout": "feature-archive",
            "target_layout": "feature-archive",
            "can_apply": True,
            "operations": [],
            "conflicts": [],
            "warnings": [],
            "backup_scope": ["noc_docs"],
        }
    if is_simplified_v2(info):
        return plan_simplified_migration(target)
    if is_v1_small(info) or is_v1_domain(info):
        return plan_v1_migration(target, "domain" if is_v1_domain(info) else "small")
    raise MigrationError("unsupported_layout", f"unsupported source layout {info.layout}")


def ensure_safe_documentation_root(target: Path) -> None:
    config = load_config(target)
    root = config.get("documentation_root", "noc_docs")
    if not isinstance(root, str) or root.replace("\\", "/") != "noc_docs" or Path(root).is_absolute() or ".." in Path(root).parts:
        raise MigrationError("unsafe_path", "documentation_root must be noc_docs")


def plan_simplified_migration(target: Path) -> dict[str, Any]:
    conflicts = feature_root_conflicts(target)
    warnings: list[dict[str, str]] = []
    config = load_config(target)
    language = config.get("language")
    if not isinstance(language, str) or not language:
        language = markdown_language_from_existing([target / "noc_docs" / name for name in PROJECT_MEMORY])
        warnings.append({"code": "language_inferred", "message": f"language inferred as {language}"})
    return {
        "status": "planned",
        "source_layout": "simplified",
        "target_layout": "feature-archive",
        "can_apply": not conflicts,
        "operations": [
            {"operation": "preserve", "path": f"noc_docs/{name}"} for name in PROJECT_MEMORY
        ]
        + [
            {"operation": "create_directory", "path": "noc_docs/features"},
            {"operation": "update_config", "path": "noc_docs/.living-docs/config.json"},
            {"operation": "rebuild_index", "path": "noc_docs/.living-docs/routing.json"},
            {"operation": "rebuild_index", "path": "noc_docs/.living-docs/feature-index.json"},
            {"operation": "rebuild_index", "path": "noc_docs/.living-docs/evidence-index.json"},
            {"operation": "rebuild_index", "path": "noc_docs/.living-docs/manifest.json"},
        ],
        "conflicts": conflicts,
        "warnings": warnings,
        "backup_scope": ["noc_docs"],
        "language": language,
    }


def feature_root_conflicts(target: Path) -> list[dict[str, str]]:
    features = target / "noc_docs/features"
    if not features.exists():
        return []
    visible = [path for path in features.iterdir() if not path.name.startswith(".")]
    if not visible:
        return []
    return [{"code": "target_conflict", "path": "noc_docs/features", "message": "features directory already contains content"}]


def plan_v1_migration(target: Path, layout: str) -> dict[str, Any]:
    feature_entries = discover_v1_features(target, layout)
    conflicts: list[dict[str, str]] = []
    used_ids: set[str] = set()
    features: list[dict[str, Any]] = []
    source_files: list[dict[str, str]] = []
    for entry in feature_entries:
        feature_id = stable_feature_id(entry["source_id"])
        if feature_id in used_ids:
            conflicts.append({"code": "feature_id_conflict", "path": entry["path"], "message": f"duplicate target feature id {feature_id}"})
        used_ids.add(feature_id)
        legacy_domain = entry.get("domain")
        features.append(
            {
                "source_id": entry["source_id"],
                "id": feature_id,
                "name": entry["name"],
                "source_path": entry["path"],
                **({"legacy_domain": legacy_domain} if legacy_domain else {}),
            }
        )
        for path in entry["files"]:
            operation = "map" if path.name in {"agent-guide.md", "requirements.md", "guardrails.md", "test-record.md", "change-record.md"} else "copy_to_legacy"
            source_files.append({"operation": operation, "path": path.relative_to(target).as_posix(), "target_feature_id": feature_id})
    if not feature_entries:
        conflicts.append({"code": "no_features", "path": "noc_docs", "message": "no v1 feature files found"})
    return {
        "status": "planned",
        "source_layout": layout,
        "target_layout": "feature-archive",
        "can_apply": not conflicts,
        "operations": [
            {"operation": "backup", "path": "noc_docs"},
            {"operation": "update_config", "path": "noc_docs/.living-docs/config.json"},
            {"operation": "rebuild_feature_archive", "path": "noc_docs/features"},
        ],
        "source_files": source_files,
        "features": features,
        "conflicts": conflicts,
        "warnings": [{"code": "v1_conservative", "message": "v1 files will be copied to legacy without semantic promotion"}],
        "backup_scope": ["noc_docs"],
        "language": markdown_language_from_existing([path for entry in feature_entries for path in entry["files"]]),
    }


def discover_v1_features(target: Path, layout: str) -> list[dict[str, Any]]:
    roots = [target / "noc_docs/features"] if layout == "small" else sorted((target / "noc_docs/domains").glob("*/features"))
    entries: list[dict[str, Any]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for feature_dir in sorted(root.iterdir()):
            if not feature_dir.is_dir() or feature_dir.name.startswith("."):
                continue
            files = [feature_dir / name for name in V1_FEATURE_DOCS if (feature_dir / name).is_file()]
            if not files:
                continue
            domain = None
            if layout == "domain":
                domain = feature_dir.parent.parent.name
            entries.append(
                {
                    "source_id": feature_dir.name,
                    "name": display_name_from_feature(feature_dir),
                    "path": feature_dir.relative_to(target).as_posix(),
                    "files": files,
                    "domain": domain,
                }
            )
    return entries


def display_name_from_feature(feature_dir: Path) -> str:
    guide = feature_dir / "agent-guide.md"
    if guide.is_file():
        for line in guide.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                if ":" in title:
                    return title.split(":", 1)[1].strip() or feature_dir.name
                return title or feature_dir.name
    return feature_dir.name


def stable_feature_id(value: str) -> str:
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        return value
    parts: list[str] = []
    current = []
    for char in value.lower():
        if "a" <= char <= "z" or "0" <= char <= "9":
            current.append(char)
        elif "\u4e00" <= char <= "\u9fff":
            if current:
                parts.append("".join(current))
                current = []
            parts.append(CHINESE_SLUGS.get(char, f"u{ord(char):x}"))
        else:
            if current:
                parts.append("".join(current))
                current = []
    if current:
        parts.append("".join(current))
    slug = "-".join(part for part in parts if part)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "legacy-feature"


def apply_simplified_to_tree(project: Path, plan: dict[str, Any]) -> None:
    config_path = project / "noc_docs/.living-docs/config.json"
    config = load_config(project)
    config.update(
        {
            "protocol": "noc-living-docs",
            "protocol_version": 2,
            "layout": "feature-archive",
            "layout_version": "1.0",
            "documentation_root": "noc_docs",
            "language": plan["language"],
            "machine_keys": config.get("machine_keys", "en-US"),
            "feature_id_style": config.get("feature_id_style", "ascii-kebab-case"),
        }
    )
    (project / "noc_docs/features").mkdir(parents=True, exist_ok=True)
    atomic_write_text(config_path, stable_json(config))
    write_feature_archive_indexes(project)


def apply_v1_to_tree(project: Path, plan: dict[str, Any]) -> None:
    old_root = project / "noc_docs"
    new_root = project / ".noc-new-docs"
    if new_root.exists():
        shutil.rmtree(new_root)
    (new_root / ".living-docs").mkdir(parents=True)
    for name in PROJECT_MEMORY:
        source = old_root / name
        if source.is_file():
            shutil.copy2(source, new_root / name)
        else:
            (new_root / name).write_text(default_project_memory(name, plan["language"]), encoding="utf-8")
    (new_root / "features").mkdir(parents=True)
    for feature in plan["features"]:
        write_migrated_feature(project, new_root, feature, plan["language"])
    config = {
        "protocol": "noc-living-docs",
        "protocol_version": 2,
        "layout": "feature-archive",
        "layout_version": "1.0",
        "documentation_root": "noc_docs",
        "language": plan["language"],
        "machine_keys": "en-US",
        "feature_id_style": "ascii-kebab-case",
    }
    atomic_write_text(new_root / ".living-docs/config.json", stable_json(config))
    shutil.rmtree(old_root)
    new_root.rename(old_root)
    write_feature_archive_indexes(project)


def default_project_memory(name: str, language: str) -> str:
    if language == "zh-CN":
        titles = {"project.md": "项目", "guardrails.md": "约束", "verification.md": "验证"}
        return f"# {titles.get(name, name)}\n\n由 v1 迁移创建，占位内容待确认。\n"
    titles = {"project.md": "Project", "guardrails.md": "Guardrails", "verification.md": "Verification"}
    return f"# {titles.get(name, name)}\n\nCreated during v1 migration; confirm details before use.\n"


def write_migrated_feature(project: Path, new_root: Path, feature: dict[str, Any], language: str) -> None:
    feature_dir = new_root / "features" / feature["id"]
    legacy_dir = feature_dir / "legacy"
    legacy_dir.mkdir(parents=True)
    source_dir = project / feature["source_path"]
    for source in sorted(source_dir.glob("*.md")):
        shutil.copy2(source, legacy_dir / source.name)
    overview = render_migrated_overview(feature, language)
    atomic_write_text(feature_dir / "overview.md", overview)


def render_migrated_overview(feature: dict[str, Any], language: str) -> str:
    sections = default_overview_sections(language)
    if language == "zh-CN":
        body = [
            f"# {feature['name']}",
            "",
            f"## {sections[0]}",
            "",
            "从 v1 文档保守迁移。原始内容保存在 `legacy/`，迁移不会把未确认内容自动提升为当前事实。",
            "",
            f"## {sections[1]}",
            "",
            "- v1 `requirements.md` 已作为候选需求原文保留在 `legacy/requirements.md`，需要人工确认后再转为已确认需求。",
            "",
            f"## {sections[2]}",
            "",
            "- 未从 v1 `status.md` 自动推断当前实现；原文保存在 `legacy/status.md`。",
            "",
        ]
    else:
        body = [
            f"# {feature['name']}",
            "",
            f"## {sections[0]}",
            "",
            "Conservatively migrated from v1. Original files are preserved under `legacy/`.",
            "",
            f"## {sections[1]}",
            "",
            "- v1 `requirements.md` is preserved as candidate source text in `legacy/requirements.md` pending confirmation.",
            "",
            f"## {sections[2]}",
            "",
            "- v1 `status.md` was not mechanically promoted to current implementation.",
            "",
        ]
    for section in sections[3:]:
        body.extend([f"## {section}", "", "- 待确认。" if language == "zh-CN" else "- Pending confirmation.", ""])
    today = datetime.now(timezone.utc).date().isoformat()
    frontmatter = [
        "---",
        f"id: {feature['id']}",
        f"name: {feature['name']}",
        "status: proposed",
        "schema_version: 1",
        f"created_at: {today}",
        f"updated_at: {today}",
        f"language: {language}",
    ]
    if feature.get("legacy_domain"):
        frontmatter.append(f"legacy_domain: {feature['legacy_domain']}")
    frontmatter.extend(["---", ""])
    return "\n".join(frontmatter + body).rstrip() + "\n"


def create_migration_backup(target: Path, *, reason: str) -> dict[str, Any]:
    backups = target / ".noc-backups/migrations"
    backups.mkdir(parents=True, exist_ok=True)
    backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = backups / backup_id
    counter = 1
    while backup_path.exists():
        backup_id = f"{backup_id}-{counter}"
        backup_path = backups / backup_id
        counter += 1
    if is_relative_to(backup_path, target / "noc_docs"):
        raise MigrationError("unsafe_backup_path", "backup path cannot be inside noc_docs")
    shutil.copytree(target / "noc_docs", backup_path / "noc_docs")
    manifest = build_backup_manifest(backup_path / "noc_docs", reason=reason)
    atomic_write_text(backup_path / "manifest.json", stable_json(manifest))
    validate_backup_manifest(backup_path)
    return {
        "backup_id": backup_id,
        "backup_path": backup_path,
        "relative_path": backup_path.relative_to(target).as_posix(),
        "file_count": len(manifest["files"]),
    }


def build_backup_manifest(root: Path, *, reason: str) -> dict[str, Any]:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root.parent).as_posix()
            data = path.read_bytes()
            files[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return {"schema_version": "1.0", "reason": reason, "root": "noc_docs", "files": files}


def validate_backup_manifest(backup_path: Path) -> None:
    try:
        manifest = json.loads((backup_path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationError("invalid_backup_manifest", "backup manifest is missing or damaged") from exc
    files = manifest.get("files")
    if manifest.get("schema_version") != "1.0" or not isinstance(files, dict):
        raise MigrationError("invalid_backup_manifest", "backup manifest has invalid schema")
    for rel, entry in files.items():
        path = backup_path / rel
        if not is_relative_to(path.resolve(), backup_path.resolve()) or not path.is_file():
            raise MigrationError("invalid_backup_manifest", f"backup file missing: {rel}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry.get("sha256"):
            raise MigrationError("invalid_backup_manifest", f"backup file hash mismatch: {rel}")


def restore_noc_docs(target: Path, source_noc_docs: Path, restore_source: Path) -> None:
    original = target / "noc_docs"
    tmp_old = target / f".noc-docs-replacing-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    try:
        if original.exists():
            original.rename(tmp_old)
        shutil.copytree(source_noc_docs, original)
        if tmp_old.exists():
            shutil.rmtree(tmp_old)
    except Exception:
        if original.exists():
            shutil.rmtree(original, ignore_errors=True)
        if tmp_old.exists():
            tmp_old.rename(original)
        elif restore_source.is_dir():
            shutil.copytree(restore_source, original)
        raise


def try_restore_from_latest_backup(target: Path) -> None:
    backups = target / ".noc-backups/migrations"
    if not backups.is_dir():
        return
    candidates = sorted(path for path in backups.iterdir() if path.is_dir())
    if not candidates:
        return
    latest = candidates[-1] / "noc_docs"
    if latest.is_dir():
        if (target / "noc_docs").exists():
            shutil.rmtree(target / "noc_docs", ignore_errors=True)
        shutil.copytree(latest, target / "noc_docs")


def resolve_backup_path(target: Path, backup_id: str) -> Path:
    if not BACKUP_ID_RE.fullmatch(backup_id):
        raise MigrationError("invalid_backup_id", "backup id is invalid")
    backup_path = (target / ".noc-backups/migrations" / backup_id).resolve()
    allowed_root = (target / ".noc-backups/migrations").resolve()
    if not is_relative_to(backup_path, allowed_root) or not backup_path.is_dir():
        raise MigrationError("invalid_backup_id", "backup id does not belong to this project")
    return backup_path


def count_files(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file())


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def error_payload(error: MigrationError) -> dict[str, Any]:
    return {"status": error.status, "error": error.message, **error.payload}
