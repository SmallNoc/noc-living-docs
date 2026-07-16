"""Structured feature-archive overview updates."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.noclib.features import validate_feature_id
from scripts.noclib.indexes import atomic_write_text, sha256_bytes, write_feature_archive_indexes


MAX_VERIFICATION_RESULTS = 3
MAX_OUTPUT_SUMMARY_CHARS = 500
MANAGED_ID_RE = re.compile(r"<!--\s*noc:id=([a-z0-9]+(?:-[a-z0-9]+)*)\s*-->")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATCH_KEYS = (
    "confirmed_requirements_add",
    "confirmed_requirements_update",
    "confirmed_requirements_remove",
    "implementation_upsert",
    "constraints_add",
    "constraints_remove",
    "code_paths_add",
    "code_paths_remove",
    "verification_methods_upsert",
    "verification_result",
    "major_change_append",
    "pending_questions_add",
    "pending_questions_resolve",
)
SECTION_BY_OPERATION = {
    "confirmed_requirements_add": "已确认需求",
    "confirmed_requirements_update": "已确认需求",
    "confirmed_requirements_remove": "已确认需求",
    "implementation_upsert": "当前实现",
    "constraints_add": "重要约束",
    "constraints_remove": "重要约束",
    "code_paths_add": "代码范围",
    "code_paths_remove": "代码范围",
    "verification_methods_upsert": "验证方式",
    "verification_result": "最近验证结果",
    "major_change_append": "最近重大变更",
    "pending_questions_add": "待确认事项",
    "pending_questions_resolve": "待确认事项",
}


class UpdateError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def update_feature(target: Path, feature_id: str, patch_file: Path) -> tuple[int, dict[str, Any]]:
    id_error = validate_feature_id(feature_id)
    if id_error:
        return 1, {"status": "invalid_feature_id", "error": id_error}
    config = load_json(target / "noc_docs/.living-docs/config.json")
    if config.get("protocol_version") != 2 or config.get("layout") != "feature-archive":
        return 1, {"status": "unsupported_layout", "error": "feature update requires feature-archive layout"}
    overview = target / "noc_docs/features" / feature_id / "overview.md"
    if not overview.is_file():
        return 1, {"status": "feature_not_found", "feature_id": feature_id}
    try:
        payload = load_json(patch_file)
        validate_patch_payload(payload, feature_id)
    except UpdateError as error:
        return 1, {"status": error.status, "error": error.message}
    before_text = overview.read_text(encoding="utf-8")
    before_sha = sha256_bytes(overview.read_bytes())
    expected = payload.get("expected_overview_sha256")
    if expected is not None and expected != before_sha:
        return 2, {
            "status": "conflict",
            "reason": "overview_changed",
            "expected_sha256": expected,
            "actual_sha256": before_sha,
        }
    try:
        after_text, result = apply_patch_text(before_text, payload["patch"])
    except UpdateError as error:
        return 2 if error.status == "duplicate_content_conflict" else 1, {"status": error.status, "error": error.message}
    after_sha = sha256_text(after_text)
    concurrency = "passed" if expected is not None else "not_requested"
    base = {
        "feature_id": feature_id,
        "overview_path": overview.relative_to(target).as_posix(),
        "updated_sections": sorted(result["updated_sections"]),
        "applied": result["applied"],
        "ignored_duplicates": result["ignored_duplicates"],
        "not_found": result["not_found"],
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "concurrency_check": concurrency,
    }
    if after_text == before_text:
        return 0, {"status": "unchanged", **base, "backup_path": None, "index_status": "not_run"}
    backup = backup_overview(target, feature_id, before_text)
    atomic_write_text(overview, after_text)
    index_status = "updated"
    index_error = None
    try:
        write_feature_archive_indexes(target)
    except Exception as exc:  # pragma: no cover - defensive reporting path
        index_status = "failed"
        index_error = str(exc)
    response = {"status": "updated", **base, "backup_path": backup.relative_to(target).as_posix(), "index_status": index_status}
    if index_error:
        response["index_error"] = index_error
        response["next_command"] = f"noc index {target}"
    return 0, response


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError("invalid_patch", str(exc)) from exc
    if not isinstance(data, dict):
        raise UpdateError("invalid_patch", "JSON payload must be an object")
    return data


def validate_patch_payload(payload: dict[str, Any], feature_id: str) -> None:
    if payload.get("schema_version") != "1.0":
        raise UpdateError("invalid_patch", "schema_version must be 1.0")
    if payload.get("feature_id") != feature_id:
        raise UpdateError("invalid_patch", "feature_id must match --id")
    if validate_feature_id(str(payload.get("feature_id", ""))):
        raise UpdateError("invalid_patch", "feature_id must be ASCII kebab-case")
    source = payload.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("actor"), str) or not source["actor"].strip():
        raise UpdateError("invalid_patch", "source.actor is required")
    patch = payload.get("patch")
    if not isinstance(patch, dict):
        raise UpdateError("invalid_patch", "patch must be an object")
    unknown = sorted(set(patch) - set(PATCH_KEYS))
    if unknown:
        raise UpdateError("invalid_patch", f"unknown patch field: {unknown[0]}")
    for key, value in patch.items():
        validate_patch_operation(key, value)


def validate_patch_operation(key: str, value: Any) -> None:
    if key == "verification_result":
        if value is not None:
            validate_verification_result(value)
        return
    if key in {"code_paths_add", "code_paths_remove"}:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise UpdateError("invalid_patch", f"{key} must be a list of strings")
        for item in value:
            normalize_safe_path(item)
        return
    if not isinstance(value, list):
        raise UpdateError("invalid_patch", f"{key} must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise UpdateError("invalid_patch", f"{key} items must be objects")
        if key.endswith("_remove"):
            validate_id_only_item(item)
        elif key == "pending_questions_resolve":
            validate_id_only_item(item)
            if not isinstance(item.get("resolution"), str) or not item["resolution"].strip():
                raise UpdateError("invalid_patch", "resolution is required")
            validate_date(item.get("resolved_at"), "resolved_at")
        elif key == "major_change_append":
            validate_major_change(item)
        elif key == "verification_methods_upsert":
            validate_id_only_item(item)
            for field in ["command", "scope"]:
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise UpdateError("invalid_patch", f"{field} is required")
        else:
            validate_text_item(item)


def validate_id_only_item(item: dict[str, Any]) -> None:
    if validate_feature_id(str(item.get("id", ""))):
        raise UpdateError("invalid_patch", "item id must be ASCII kebab-case")


def validate_text_item(item: dict[str, Any]) -> None:
    validate_id_only_item(item)
    if not isinstance(item.get("text"), str) or not item["text"].strip():
        raise UpdateError("invalid_patch", "text is required")
    if not isinstance(item.get("source"), str) or not item["source"].strip():
        raise UpdateError("invalid_patch", "source is required")


def validate_major_change(item: dict[str, Any]) -> None:
    validate_id_only_item(item)
    validate_date(item.get("date"), "date")
    if not isinstance(item.get("summary"), str) or not item["summary"].strip():
        raise UpdateError("invalid_patch", "summary is required")
    if not isinstance(item.get("details"), list) or not all(isinstance(detail, str) for detail in item["details"]):
        raise UpdateError("invalid_patch", "details must be a list of strings")
    if not isinstance(item.get("source"), str) or not item["source"].strip():
        raise UpdateError("invalid_patch", "source is required")


def validate_date(value: Any, label: str) -> None:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise UpdateError("invalid_patch", f"{label} must be YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise UpdateError("invalid_patch", f"{label} must be a valid date") from exc


def validate_verification_result(value: Any) -> None:
    if not isinstance(value, dict):
        raise UpdateError("invalid_verification_result", "verification_result must be an object")
    required = ["command", "cwd", "started_at", "finished_at", "result", "scope", "output_summary"]
    for field in required:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise UpdateError("invalid_verification_result", f"{field} is required")
    result = value.get("result")
    exit_code = value.get("exit_code")
    if result not in {"passed", "failed", "not_run", "unknown"}:
        raise UpdateError("invalid_verification_result", "result is invalid")
    if exit_code is not None and not isinstance(exit_code, int):
        raise UpdateError("invalid_verification_result", "exit_code must be integer or null")
    if result == "passed" and exit_code != 0:
        raise UpdateError("invalid_verification_result", "passed requires exit_code 0")
    if result == "failed" and exit_code == 0:
        raise UpdateError("invalid_verification_result", "failed requires non-zero exit_code")


def apply_patch_text(text: str, patch: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    lines = text.splitlines()
    state: dict[str, Any] = {"applied": [], "ignored_duplicates": [], "not_found": [], "updated_sections": set()}
    for key in PATCH_KEYS:
        value = patch.get(key)
        if value in (None, []):
            continue
        if key == "verification_result":
            apply_verification_result(lines, value, state)
        elif key in {"code_paths_add", "code_paths_remove"}:
            apply_code_paths(lines, key, value, state)
        elif key == "verification_methods_upsert":
            apply_verification_methods(lines, key, value, state)
        elif key == "major_change_append":
            apply_major_changes(lines, key, value, state)
        elif key == "pending_questions_resolve":
            remove_items(lines, key, value, SECTION_BY_OPERATION[key], state)
        elif key.endswith("_remove"):
            remove_items(lines, key, value, SECTION_BY_OPERATION[key], state)
        else:
            apply_managed_items(lines, key, value, SECTION_BY_OPERATION[key], state)
    return "\n".join(lines).rstrip() + "\n", state


def apply_managed_items(lines: list[str], operation: str, items: list[dict[str, Any]], section: str, state: dict[str, Any]) -> None:
    ensure_section(lines, section)
    start, end = section_content_bounds(lines, section)
    existing = managed_items(lines[start:end])
    for item in items:
        item_id = item["id"]
        rendered = f"- {item['text'].strip()} <!-- noc:id={item_id} -->"
        text_key = normalize_text(item["text"])
        duplicate = next((current_id for current_id, line in existing.items() if normalize_text(managed_text(line)) == text_key and current_id != item_id), None)
        if duplicate:
            raise UpdateError("duplicate_content_conflict", f"{item_id} duplicates content in {duplicate}")
        if item_id in existing:
            absolute = start + existing_index(lines[start:end], item_id)
            if lines[absolute] == rendered:
                state["ignored_duplicates"].append({"operation": operation, "id": item_id})
                continue
            if operation.endswith("_add"):
                raise UpdateError("duplicate_content_conflict", f"{item_id} already exists with different text")
            lines[absolute] = rendered
        else:
            if operation.endswith("_update"):
                raise UpdateError("invalid_patch", f"{item_id} not found")
            insert_bullet(lines, end, rendered)
        state["applied"].append({"operation": operation, "id": item_id})
        state["updated_sections"].add(section)
        start, end = section_content_bounds(lines, section)
        existing = managed_items(lines[start:end])


def remove_items(lines: list[str], operation: str, items: list[dict[str, Any]], section: str, state: dict[str, Any]) -> None:
    bounds = maybe_section_content_bounds(lines, section)
    if bounds is None:
        for item in items:
            state["not_found"].append({"operation": operation, "id": item["id"]})
        return
    start, _ = bounds
    for item in items:
        relative = existing_index(lines[start:maybe_section_content_bounds(lines, section)[1]], item["id"])
        if relative < 0:
            state["not_found"].append({"operation": operation, "id": item["id"]})
            continue
        del lines[start + relative]
        state["applied"].append({"operation": operation, "id": item["id"]})
        state["updated_sections"].add(section)


def apply_code_paths(lines: list[str], operation: str, paths: list[str], state: dict[str, Any]) -> None:
    section = SECTION_BY_OPERATION[operation]
    normalized = [normalize_safe_path(path) for path in paths]
    if operation.endswith("_add"):
        ensure_section(lines, section)
    bounds = maybe_section_content_bounds(lines, section)
    if bounds is None:
        for path in normalized:
            state["not_found"].append({"operation": operation, "path": path})
        return
    start, end = bounds
    current = {code_path_from_line(line): index for index, line in enumerate(lines[start:end]) if code_path_from_line(line)}
    for path in normalized:
        rendered = f"- `{path}`"
        if operation.endswith("_add"):
            if path in current:
                state["ignored_duplicates"].append({"operation": operation, "path": path})
                continue
            insert_bullet(lines, end, rendered)
            state["applied"].append({"operation": operation, "path": path})
            state["updated_sections"].add(section)
            start, end = section_content_bounds(lines, section)
            current = {code_path_from_line(line): index for index, line in enumerate(lines[start:end]) if code_path_from_line(line)}
        else:
            if path not in current:
                state["not_found"].append({"operation": operation, "path": path})
                continue
            del lines[start + current[path]]
            state["applied"].append({"operation": operation, "path": path})
            state["updated_sections"].add(section)
            start, end = section_content_bounds(lines, section)
            current = {code_path_from_line(line): index for index, line in enumerate(lines[start:end]) if code_path_from_line(line)}


def apply_verification_result(lines: list[str], value: dict[str, Any], state: dict[str, Any]) -> None:
    section = "最近验证结果"
    ensure_section(lines, section)
    summary = sanitize_summary(value["output_summary"])
    exit_code = "null" if value.get("exit_code") is None else str(value["exit_code"])
    rendered = (
        f"- {value['finished_at']} {value['result']} `{value['command']}` "
        f"(cwd: `{value['cwd']}`, exit_code: {exit_code}, scope: {value['scope']}) - {summary}"
    )
    start, end = section_content_bounds(lines, section)
    entries = [line for line in lines[start:end] if line.startswith("- ")]
    if rendered in entries:
        state["ignored_duplicates"].append({"operation": "verification_result", "command": value["command"]})
        return
    insert_bullet(lines, end, rendered)
    trim_section_bullets(lines, section, MAX_VERIFICATION_RESULTS)
    state["applied"].append({"operation": "verification_result", "command": value["command"]})
    state["updated_sections"].add(section)


def apply_verification_methods(lines: list[str], operation: str, items: list[dict[str, Any]], state: dict[str, Any]) -> None:
    section = "验证方式"
    ensure_section(lines, section)
    start, end = section_content_bounds(lines, section)
    existing = managed_items(lines[start:end])
    for item in items:
        rendered = f"- `{item['command'].strip()}` - {item['scope'].strip()} <!-- noc:id={item['id']} -->"
        if item["id"] in existing:
            absolute = start + existing_index(lines[start:end], item["id"])
            if lines[absolute] == rendered:
                state["ignored_duplicates"].append({"operation": operation, "id": item["id"]})
                continue
            lines[absolute] = rendered
        else:
            insert_bullet(lines, end, rendered)
        state["applied"].append({"operation": operation, "id": item["id"]})
        state["updated_sections"].add(section)
        start, end = section_content_bounds(lines, section)
        existing = managed_items(lines[start:end])


def apply_major_changes(lines: list[str], operation: str, items: list[dict[str, Any]], state: dict[str, Any]) -> None:
    section = "最近重大变更"
    ensure_section(lines, section)
    start, end = section_content_bounds(lines, section)
    existing = managed_items(lines[start:end])
    for item in items:
        if item["id"] in existing:
            state["ignored_duplicates"].append({"operation": operation, "id": item["id"]})
            continue
        rendered = f"- {item['date']} {item['summary'].strip()} <!-- noc:id={item['id']} -->"
        insert_bullet(lines, end, rendered)
        start, end = section_content_bounds(lines, section)
        insert_at = start + existing_index(lines[start:end], item["id"]) + 1
        for detail in item["details"]:
            lines.insert(insert_at, f"  - {detail}")
            insert_at += 1
        state["applied"].append({"operation": operation, "id": item["id"]})
        state["updated_sections"].add(section)
        start, end = section_content_bounds(lines, section)
        existing = managed_items(lines[start:end])


def ensure_section(lines: list[str], title: str) -> None:
    if maybe_section_content_bounds(lines, title) is not None:
        return
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend([f"## {title}", ""])


def maybe_section_content_bounds(lines: list[str], title: str) -> tuple[int, int] | None:
    heading = f"## {title}"
    for index, line in enumerate(lines):
        if line.strip() == heading:
            end = len(lines)
            for probe in range(index + 1, len(lines)):
                if lines[probe].startswith("## "):
                    end = probe
                    break
            return index + 1, end
    return None


def section_content_bounds(lines: list[str], title: str) -> tuple[int, int]:
    bounds = maybe_section_content_bounds(lines, title)
    if bounds is None:
        raise AssertionError(f"missing section {title}")
    return bounds


def insert_bullet(lines: list[str], end: int, rendered: str) -> None:
    insert_at = end
    while insert_at > 0 and lines[insert_at - 1] == "":
        insert_at -= 1
    lines.insert(insert_at, rendered)
    if insert_at + 1 >= len(lines) or lines[insert_at + 1] != "":
        lines.insert(insert_at + 1, "")


def trim_section_bullets(lines: list[str], section: str, maximum: int) -> None:
    start, end = section_content_bounds(lines, section)
    bullet_indexes = [start + index for index, line in enumerate(lines[start:end]) if line.startswith("- ")]
    for index in bullet_indexes[: max(0, len(bullet_indexes) - maximum)]:
        lines[index] = None  # type: ignore[assignment]
    lines[:] = [line for line in lines if line is not None]


def managed_items(section_lines: list[str]) -> dict[str, str]:
    result = {}
    for line in section_lines:
        match = MANAGED_ID_RE.search(line)
        if match:
            result[match.group(1)] = line
    return result


def existing_index(section_lines: list[str], item_id: str) -> int:
    for index, line in enumerate(section_lines):
        match = MANAGED_ID_RE.search(line)
        if match and match.group(1) == item_id:
            return index
    return -1


def managed_text(line: str) -> str:
    return MANAGED_ID_RE.sub("", line).removeprefix("- ").strip()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def code_path_from_line(line: str) -> str | None:
    match = re.match(r"- `([^`]+)`\s*$", line.strip())
    return match.group(1) if match else None


def normalize_safe_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise UpdateError("unsafe_path", "path must be relative")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise UpdateError("unsafe_path", "path traversal is not allowed")
    return "/".join(parts)


def sanitize_summary(value: str) -> str:
    stripped = re.sub(r"(?i)(api[_-]?key|token|password|secret)=\S+", r"\1=<redacted>", value.strip())
    return stripped[:MAX_OUTPUT_SUMMARY_CHARS]


def backup_overview(target: Path, feature_id: str, text: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup = target / "noc_docs/.living-docs/backups" / timestamp / "features" / feature_id / "overview.md"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(text, encoding="utf-8", newline="\n")
    return backup


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))
