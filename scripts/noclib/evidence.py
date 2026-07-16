"""Code and verification evidence helpers for feature archives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


MAX_COMMAND_CHARS = 300
MAX_CWD_CHARS = 200
MAX_SCOPE_CHARS = 200
MAX_SUMMARY_CHARS = 500


class EvidenceError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def collect_code_evidence(target: Path, mode: str = "staged") -> dict[str, Any]:
    if mode != "staged":
        return base_collect_result(target, mode, False, ["unsupported_mode"])
    if shutil.which("git") is None:
        return base_collect_result(target, mode, False, ["git_unavailable"])
    repo = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if repo.returncode != 0:
        return base_collect_result(target, mode, False, ["not_git_repository"])
    root = Path(repo.stdout.strip())
    name_status = run_git(target, ["diff", "--cached", "--name-status", "-M"])
    shortstat = run_git(target, ["diff", "--cached", "--shortstat"])
    changed_paths = parse_name_status(name_status.stdout)
    signals = []
    for item in changed_paths:
        signals.extend(signals_for_path(item["path"]))
    return {
        "schema_version": "1.0",
        "git_available": True,
        "mode": mode,
        "repository_root": relative_repo_root(target, root),
        "changed_paths": changed_paths,
        "diff_summary": parse_shortstat(shortstat.stdout),
        "signals": signals,
        "warnings": [],
    }


def base_collect_result(target: Path, mode: str, git_available: bool, warnings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "git_available": git_available,
        "mode": mode,
        "repository_root": ".",
        "changed_paths": [],
        "diff_summary": {"files_changed": 0, "insertions": 0, "deletions": 0},
        "signals": [],
        "warnings": warnings,
    }


def run_git(target: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), "-c", "core.quotepath=false", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def parse_name_status(value: str) -> list[dict[str, str]]:
    result = []
    mapping = {"A": "added", "M": "modified", "D": "deleted"}
    for line in value.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            result.append({"path": normalize_path(parts[2]), "old_path": normalize_path(parts[1]), "change_type": "renamed"})
        elif status[:1] in mapping and len(parts) >= 2:
            result.append({"path": normalize_path(parts[1]), "change_type": mapping[status[:1]]})
    return result


def parse_shortstat(value: str) -> dict[str, int]:
    files = re.search(r"(\d+) files? changed", value)
    insertions = re.search(r"(\d+) insertions?", value)
    deletions = re.search(r"(\d+) deletions?", value)
    return {
        "files_changed": int(files.group(1)) if files else 0,
        "insertions": int(insertions.group(1)) if insertions else 0,
        "deletions": int(deletions.group(1)) if deletions else 0,
    }


def signals_for_path(path: str) -> list[dict[str, str]]:
    normalized = path.lower()
    name = Path(normalized).name
    signals = []
    rules = [
        ("test_change", normalized.startswith(("tests/", "test/")) or name.startswith("test_") or name.endswith("test.java"), "test path or filename"),
        ("api_change", any(token in normalized for token in ["controller", "routes", "openapi", "swagger"]), "API route/openapi/controller path"),
        ("database_change", "migration" in normalized or "schema" in normalized or normalized.endswith(".sql"), "migration/schema/sql path"),
        ("config_change", name.startswith("application") and name.endswith((".yml", ".yaml")) or normalized.endswith((".yaml", ".yml", ".toml", ".ini")), "configuration filename"),
        ("security_change", any(token in normalized for token in ["auth", "security", "permission"]), "auth/security/permission path"),
        ("documentation_change", normalized.startswith(("noc_docs/", "docs/")) or name.startswith("readme"), "documentation path"),
    ]
    for signal_type, matched, basis in rules:
        if matched:
            signals.append({"type": signal_type, "path": path, "basis": basis, "confidence": "high"})
    return signals


def record_verification_evidence(target: Path, feature_id: str, evidence_file: Path) -> tuple[int, dict[str, Any]]:
    try:
        config = load_json(target / "noc_docs/.living-docs/config.json")
    except EvidenceError:
        return 1, {"status": "unsupported_layout"}
    if config.get("protocol_version") != 2 or config.get("layout") != "feature-archive":
        return 1, {"status": "unsupported_layout"}
    if not is_ascii_kebab_case(feature_id):
        return 1, {"status": "invalid_feature_id"}
    if not (target / "noc_docs/features" / feature_id / "overview.md").is_file():
        return 1, {"status": "feature_not_found"}
    try:
        data = load_json(evidence_file)
        normalized = normalize_verification_payload(target, data, feature_id)
    except EvidenceError as error:
        return 1, {"status": error.status, "error": error.message}
    evidence_id = evidence_id_for(normalized)
    rel = f"noc_docs/.living-docs/evidence/{feature_id}/{evidence_id}.json"
    path = target / rel
    if path.is_file():
        from scripts.noclib.indexes import write_feature_archive_indexes

        write_feature_archive_indexes(target)
        return 0, {"status": "existing", "evidence_id": evidence_id, "path": rel}
    atomic_write_text(path, stable_json({"id": evidence_id, **normalized}))
    from scripts.noclib.indexes import write_feature_archive_indexes

    write_feature_archive_indexes(target)
    return 0, {"status": "created", "evidence_id": evidence_id, "path": rel, "result": normalized["result"], "feature_id": feature_id}


def normalize_verification_payload(target: Path, data: dict[str, Any], feature_id: str) -> dict[str, Any]:
    if data.get("schema_version") != "1.0":
        raise EvidenceError("invalid_verification_evidence", "schema_version must be 1.0")
    if data.get("feature_id") != feature_id:
        raise EvidenceError("invalid_verification_evidence", "feature_id mismatch")
    validate_verification_result(data)
    started = parse_datetime(data["started_at"])
    finished = parse_datetime(data["finished_at"])
    if finished < started:
        raise EvidenceError("invalid_verification_evidence", "finished_at cannot be earlier than started_at")
    source = data.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("actor"), str) or not source["actor"].strip():
        raise EvidenceError("invalid_verification_evidence", "source.actor is required")
    return {
        "schema_version": "1.0",
        "feature_id": feature_id,
        "command": truncate(redact(data["command"]), MAX_COMMAND_CHARS),
        "cwd": normalize_cwd(target, str(data["cwd"])),
        "started_at": data["started_at"],
        "finished_at": data["finished_at"],
        "exit_code": data.get("exit_code"),
        "result": data["result"],
        "scope": truncate(str(data["scope"]), MAX_SCOPE_CHARS),
        "output_summary": truncate(redact(str(data["output_summary"])), MAX_SUMMARY_CHARS),
        "source": {"actor": source["actor"]},
        "recorded_at": data["finished_at"],
    }


def build_evidence_index(target: Path) -> dict[str, Any]:
    root = target / "noc_docs/.living-docs/evidence"
    evidence = []
    if root.is_dir():
        for path in sorted(root.glob("*/*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid evidence {path.relative_to(target).as_posix()}") from exc
            for key in ["id", "feature_id", "result", "scope", "command", "recorded_at"]:
                if not data.get(key):
                    raise ValueError(f"invalid evidence {path.relative_to(target).as_posix()}: missing {key}")
            evidence.append(
                {
                    "id": data["id"],
                    "feature_id": data["feature_id"],
                    "result": data["result"],
                    "scope": data["scope"],
                    "command": data["command"],
                    "recorded_at": data["recorded_at"],
                    "path": path.relative_to(target).as_posix(),
                }
            )
    return {"schema_version": "1.0", "evidence": evidence}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError("invalid_verification_evidence", str(exc)) from exc
    if not isinstance(data, dict):
        raise EvidenceError("invalid_verification_evidence", "JSON must be object")
    return data


def evidence_id_for(data: dict[str, Any]) -> str:
    keys = ["feature_id", "command", "cwd", "started_at", "finished_at", "exit_code", "result", "scope"]
    raw = json.dumps({key: data.get(key) for key in keys}, ensure_ascii=False, sort_keys=True)
    return "ev-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def redact(value: str) -> str:
    patterns = [
        (r"(?i)Authorization:\s*Bearer\s+[A-Za-z0-9._~+/=-]+", "Authorization: Bearer [REDACTED]"),
        (r"(?i)(token|api_key|password|secret)=([^\s&]+)", r"\1=[REDACTED]"),
        (r"(?i)([?&](?:token|key|password|api_key)=)[^&\s]+", r"\1[REDACTED]"),
        (r"Bearer\s+eyJ[A-Za-z0-9._-]+", "Bearer [REDACTED]"),
    ]
    result = value
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def truncate(value: str, maximum: int) -> str:
    return value[:maximum]


def normalize_cwd(target: Path, cwd: str) -> str:
    value = cwd.replace("\\", "/")
    path = Path(cwd)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(target.resolve()).as_posix() or "."
        except ValueError:
            return "."
    return truncate(value or ".", MAX_CWD_CHARS)


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError("invalid_verification_evidence", "invalid datetime") from exc


def normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def relative_repo_root(target: Path, root: Path) -> str:
    try:
        return root.resolve().relative_to(target.resolve()).as_posix() or "."
    except ValueError:
        return "."


def is_ascii_kebab_case(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def validate_verification_result(value: dict[str, Any]) -> None:
    required = ["command", "cwd", "started_at", "finished_at", "result", "scope", "output_summary"]
    for field in required:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise EvidenceError("invalid_verification_evidence", f"{field} is required")
    result = value.get("result")
    exit_code = value.get("exit_code")
    if result not in {"passed", "failed", "not_run", "unknown"}:
        raise EvidenceError("invalid_verification_evidence", "result is invalid")
    if exit_code is not None and not isinstance(exit_code, int):
        raise EvidenceError("invalid_verification_evidence", "exit_code must be integer or null")
    if result == "passed" and exit_code != 0:
        raise EvidenceError("invalid_verification_evidence", "passed requires exit_code 0")
    if result == "failed" and exit_code == 0:
        raise EvidenceError("invalid_verification_evidence", "failed requires non-zero exit_code")


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
