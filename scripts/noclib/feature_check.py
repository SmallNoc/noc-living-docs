"""Feature impact checks for feature archives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.noclib.evidence import collect_code_evidence


VALID_CLASSES = {"none", "implementation", "requirement", "major"}


def check_feature_impact(target: Path, impact_file: Path) -> tuple[int, dict[str, Any]]:
    try:
        impact = json.loads(impact_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return 2, failure([], [{"code": "invalid_impact", "message": str(exc)}], [], [], None)
    checks: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    feature_ids = impact.get("feature_ids", [])
    change_class = impact.get("change_class")
    if impact.get("schema_version") != "1.0" or change_class not in VALID_CLASSES:
        errors.append({"code": "invalid_impact", "message": "impact schema_version or change_class is invalid"})
    if not isinstance(feature_ids, list) or not all(isinstance(item, str) for item in feature_ids):
        errors.append({"code": "invalid_impact", "message": "feature_ids must be a list of strings"})
        feature_ids = []
    if change_class != "none" and not feature_ids:
        errors.append({"code": "missing_feature", "message": "change_class requires at least one feature"})
    for feature_id in feature_ids:
        if overview_path(target, feature_id).is_file():
            checks.append({"id": "feature_exists", "status": "passed"})
        else:
            errors.append({"code": "feature_not_found", "message": f"{feature_id} does not exist"})
            checks.append({"id": "feature_exists", "status": "failed"})
    evidence_index = load_evidence_index(target)
    evidence_ids = impact.get("verification_evidence_ids", [])
    evidence_items = []
    for evidence_id in evidence_ids if isinstance(evidence_ids, list) else []:
        item = evidence_index.get(evidence_id)
        if not item:
            errors.append({"code": "missing_verification_evidence", "message": f"{evidence_id} was not found"})
            continue
        evidence_items.append(item)
        if item["feature_id"] not in feature_ids:
            errors.append({"code": "evidence_feature_mismatch", "message": f"{evidence_id} belongs to {item['feature_id']}"})
        if item["result"] != "passed":
            errors.append({"code": "verification_not_passed", "message": f"{evidence_id} result is {item['result']}"})
    if evidence_items:
        checks.append({"id": "verification_evidence_valid", "status": "passed" if not any(error["code"].startswith("verification") or error["code"].startswith("evidence") for error in errors) else "failed"})
    code_evidence = None
    if isinstance(impact.get("code_evidence"), dict) and impact["code_evidence"].get("mode") == "staged":
        code_evidence = collect_code_evidence(target, "staged")
        if code_evidence.get("changed_paths") == [] and change_class in {"implementation", "requirement", "major"}:
            warnings.append({"code": "no_code_evidence", "message": "No staged code evidence was found"})
    documentation_updates = normalize_documentation_updates(impact)
    validate_documentation(target, change_class, feature_ids, documentation_updates, impact.get("major_change_ids", []), errors, warnings, checks)
    if change_class == "none":
        if code_evidence and code_evidence.get("changed_paths"):
            warnings.append({"code": "code_changed_for_none", "message": "Code evidence exists for change_class none"})
    elif change_class == "implementation":
        for update in documentation_updates:
            if update.get("status") == "not_required" and not update.get("reason"):
                errors.append({"code": "missing_documentation_reason", "message": "not_required documentation update needs a reason"})
        if not evidence_items:
            warnings.append({"code": "missing_verification_evidence", "message": "No verification evidence was provided"})
    elif change_class == "requirement":
        if not evidence_ids:
            errors.append({"code": "missing_verification_evidence", "message": "需求变化声明包含验证要求，但没有提供有效验证证据。"})
    elif change_class == "major":
        if not impact.get("major_change_ids"):
            errors.append({"code": "missing_major_change", "message": "major change requires major_change_ids"})
        risk_signals = [signal for signal in (code_evidence or {}).get("signals", []) if signal["type"] in {"api_change", "database_change", "security_change", "config_change"}]
        for signal in risk_signals:
            warnings.append({"code": "major_risk_signal", "message": f"{signal['type']} at {signal['path']}"})
    errors.sort(key=error_priority)
    status = "failed" if errors else "passed"
    checks.append({"id": "documentation_update_consistent", "status": "failed" if any(error["code"].startswith("missing_documentation") or error["code"].startswith("declared_section") for error in errors) else "passed"})
    return (0 if not errors else 1), {
        "status": status,
        "feature_ids": feature_ids,
        "change_class": change_class,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def normalize_documentation_updates(impact: dict[str, Any]) -> list[dict[str, Any]]:
    updates = impact.get("documentation_updates")
    if isinstance(updates, list):
        return [item for item in updates if isinstance(item, dict)]
    update = impact.get("documentation_update")
    if isinstance(update, dict):
        return [update]
    return []


def validate_documentation(
    target: Path,
    change_class: str,
    feature_ids: list[str],
    updates: list[dict[str, Any]],
    major_ids: list[str],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    updates_by_feature = {update.get("feature_id"): update for update in updates}
    for feature_id in feature_ids:
        update = updates_by_feature.get(feature_id) or (updates[0] if len(feature_ids) == 1 and updates else None)
        if change_class in {"requirement", "major"}:
            if not update or update.get("status") != "updated":
                errors.append({"code": "documentation_not_updated", "message": f"{feature_id} documentation must be updated"})
                continue
            sections = set(update.get("updated_sections", []))
            if not {"已确认需求", "当前实现"} <= sections:
                errors.append({"code": "missing_documentation_sections", "message": f"{feature_id} needs requirement and implementation sections"})
            if not ({"验证方式", "最近验证结果"} & sections):
                errors.append({"code": "missing_verification_section", "message": f"{feature_id} needs verification section"})
            if change_class == "major" and "最近重大变更" not in sections:
                errors.append({"code": "missing_major_section", "message": f"{feature_id} needs major change section"})
        if update and update.get("status") == "updated":
            text = overview_path(target, feature_id).read_text(encoding="utf-8", errors="replace") if overview_path(target, feature_id).is_file() else ""
            for section in update.get("updated_sections", []):
                if f"## {section}" not in text:
                    errors.append({"code": "declared_section_missing", "message": f"{section} not found in {feature_id}"})
            for major_id in major_ids or []:
                if f"noc:id={major_id}" not in text:
                    errors.append({"code": "major_change_not_found", "message": f"{major_id} not found in {feature_id}"})


def load_evidence_index(target: Path) -> dict[str, dict[str, Any]]:
    path = target / "noc_docs/.living-docs/evidence-index.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data.get("evidence", []) if isinstance(item, dict) and item.get("id")}


def overview_path(target: Path, feature_id: str) -> Path:
    return target / "noc_docs/features" / feature_id / "overview.md"


def failure(feature_ids: list[str], errors: list[dict[str, str]], warnings: list[dict[str, str]], checks: list[dict[str, str]], change_class: str | None) -> dict[str, Any]:
    return {"status": "failed", "feature_ids": feature_ids, "change_class": change_class, "errors": errors, "warnings": warnings, "checks": checks}


def error_priority(error: dict[str, str]) -> tuple[int, str]:
    order = {
        "declared_section_missing": 0,
        "missing_documentation_sections": 1,
        "missing_verification_section": 2,
        "missing_verification_evidence": 3,
    }
    return order.get(error.get("code", ""), 50), error.get("code", "")
