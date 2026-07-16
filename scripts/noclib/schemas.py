"""Schema validation helpers for NOC feature archives."""

from __future__ import annotations

import re
from typing import Any


SUPPORTED_PROTOCOL_VERSION = 2
FEATURE_ARCHIVE_LAYOUT = "feature-archive"
FEATURE_ARCHIVE_LAYOUT_VERSION = "1.0"
SIMPLIFIED_LAYOUT = "simplified"
SIMPLIFIED_LAYOUT_VERSION = "1.0"
OVERVIEW_SCHEMA_VERSION = 1

VALID_FEATURE_STATUSES = {"proposed", "active", "deprecated", "removed"}
VALID_VERIFICATION_RESULTS = {"passed", "failed", "not_run", "unknown"}
VALID_CODE_EVIDENCE_MODES = {"staged", "unstaged", "changed", "unknown"}
_ASCII_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_ascii_kebab_case(value: str) -> bool:
    return bool(_ASCII_KEBAB_RE.fullmatch(value))


def validate_config_schema(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_strings = {
        "protocol": "noc-living-docs",
        "layout": FEATURE_ARCHIVE_LAYOUT,
        "layout_version": FEATURE_ARCHIVE_LAYOUT_VERSION,
        "documentation_root": "noc_docs",
        "language": None,
        "machine_keys": "en-US",
    }
    for key, expected in required_strings.items():
        value = data.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{key} is required")
        elif expected is not None and value != expected:
            errors.append(f"{key} must be {expected}")
    if data.get("protocol_version") != SUPPORTED_PROTOCOL_VERSION:
        errors.append("protocol_version must be 2")
    if data.get("feature_id_style") not in {None, "ascii-kebab-case"}:
        errors.append("feature_id_style must be ascii-kebab-case")

    routing = data.get("routing")
    if routing is not None:
        if not isinstance(routing, dict):
            errors.append("routing must be an object")
        else:
            for key in ["high_confidence", "medium_confidence", "ambiguity_delta"]:
                value = routing.get(key)
                if not isinstance(value, (int, float)):
                    errors.append(f"routing.{key} must be a number")
    return errors


def validate_overview_frontmatter(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    feature_id = data.get("id")
    if not isinstance(feature_id, str) or not is_ascii_kebab_case(feature_id):
        errors.append("id must be ASCII kebab-case")
    for key in ["name", "created_at", "updated_at", "language"]:
        if not isinstance(data.get(key), str) or not data.get(key):
            errors.append(f"{key} is required")
    if data.get("status") not in VALID_FEATURE_STATUSES:
        errors.append("status must be proposed, active, deprecated, or removed")
    if data.get("schema_version") != OVERVIEW_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    aliases = data.get("aliases")
    if aliases is not None and (
        not isinstance(aliases, list) or not all(isinstance(alias, str) and alias for alias in aliases)
    ):
        errors.append("aliases must be a list of non-empty strings")
    return errors


def validate_candidate_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
    else:
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                errors.append(f"candidates[{index}] must be an object")
                continue
            feature_id = candidate.get("id")
            if not isinstance(feature_id, str) or not is_ascii_kebab_case(feature_id):
                errors.append(f"candidates[{index}].id must be ASCII kebab-case")
            if candidate.get("confidence") not in {"high", "medium", "low"}:
                errors.append(f"candidates[{index}].confidence must be high, medium, or low")
            score = candidate.get("score")
            if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                errors.append(f"candidates[{index}].score must be between 0 and 1")
    ambiguity = data.get("ambiguity")
    if ambiguity is not None and not isinstance(ambiguity, dict):
        errors.append("ambiguity must be an object")
    return errors


def validate_feature_patch_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    feature_id = data.get("feature_id")
    if not isinstance(feature_id, str) or not is_ascii_kebab_case(feature_id):
        errors.append("feature_id must be ASCII kebab-case")
    if not isinstance(data.get("source"), dict):
        errors.append("source must be an object")
    patch = data.get("patch")
    if not isinstance(patch, dict):
        errors.append("patch must be an object")
        return errors
    result = patch.get("verification_result")
    if result is not None:
        errors.extend(_validate_verification_result(result, "verification_result"))
    return errors


def validate_evidence_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    code_evidence = data.get("code_evidence")
    if code_evidence is not None:
        if not isinstance(code_evidence, dict):
            errors.append("code_evidence must be an object")
        elif code_evidence.get("mode") not in VALID_CODE_EVIDENCE_MODES:
            errors.append("code_evidence.mode must be staged, unstaged, changed, or unknown")
    verification = data.get("verification_evidence", [])
    if not isinstance(verification, list):
        errors.append("verification_evidence must be a list")
    else:
        for index, result in enumerate(verification):
            errors.extend(_validate_verification_result(result, f"verification_evidence[{index}]"))
    return errors


def _validate_verification_result(value: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    result = value.get("result")
    exit_code = value.get("exit_code")
    if result not in VALID_VERIFICATION_RESULTS:
        errors.append(f"{label}.result must be passed, failed, not_run, or unknown")
    if exit_code is not None and not isinstance(exit_code, int):
        errors.append(f"{label}.exit_code must be an integer")
    if result == "passed" and exit_code != 0:
        errors.append(f"{label} passed requires exit_code 0")
    return errors
