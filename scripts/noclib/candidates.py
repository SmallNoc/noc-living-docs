"""Deterministic feature candidate scoring for feature archives."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.noclib.indexes import PROJECT_MEMORY
from scripts.noclib.overview import parse_frontmatter_file


DEFAULT_THRESHOLDS = {"high_confidence": 0.78, "medium_confidence": 0.55, "ambiguity_delta": 0.12}


def normalize_text(value: str) -> str:
    lowered = value.lower().replace("\\", "/")
    cleaned = re.sub(r"[^\w\u4e00-\u9fff/.-]+", " ", lowered, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def tokens(value: str) -> set[str]:
    normalized = normalize_text(value)
    result = {part for part in re.split(r"[\s/._-]+", normalized) if len(part) >= 2}
    for char in normalized:
        if "\u4e00" <= char <= "\u9fff":
            result.add(char)
    return result


def load_thresholds(config: dict[str, Any]) -> dict[str, float]:
    routing = config.get("routing") if isinstance(config.get("routing"), dict) else {}
    return {
        "high_confidence": float(routing.get("high_confidence", DEFAULT_THRESHOLDS["high_confidence"])),
        "medium_confidence": float(routing.get("medium_confidence", DEFAULT_THRESHOLDS["medium_confidence"])),
        "ambiguity_delta": float(routing.get("ambiguity_delta", DEFAULT_THRESHOLDS["ambiguity_delta"])),
    }


def feature_archive_work_plan(target: Path, config: dict[str, Any], paths: list[str], intent: str | None) -> dict[str, Any]:
    thresholds = load_thresholds(config)
    candidates = score_candidates(target, paths, intent, thresholds)
    ambiguity = ambiguity_for(candidates, thresholds)
    action = action_for(candidates, ambiguity)
    public_candidates = []
    for candidate in candidates:
        item = dict(candidate)
        item.pop("_strong_sources", None)
        public_candidates.append(item)
    return {
        "schema_version": "1.0",
        "protocol_version": 2,
        "layout": "feature-archive",
        "layout_version": config.get("layout_version", "1.0"),
        "resolution_status": "project_memory",
        "intent": intent,
        "paths": paths,
        "project_documents": PROJECT_MEMORY,
        "features": [
            {
                "id": "feature-archive",
                "read_before_code": PROJECT_MEMORY,
                "before_coding": [],
                "update_after_code": [
                    {"doc": "project memory and feature archive", "reason": "only when future sessions need a new fact"}
                ],
            }
        ],
        "candidates": public_candidates,
        "ambiguity": ambiguity,
        "action": action,
        "next_actions": [],
        "finish_commands": [],
    }


def score_candidates(target: Path, paths: list[str], intent: str | None, thresholds: dict[str, float]) -> list[dict[str, Any]]:
    features = load_features(target)
    scored = []
    for feature in features:
        score, evidence, strong_sources = score_feature(feature, paths, intent)
        score = min(score, 1.0)
        if feature.get("status") in {"deprecated", "removed"}:
            score *= 0.65
            evidence.append({"type": "status_penalty", "value": feature.get("status")})
        score = round(score, 2)
        if score <= 0:
            continue
        confidence = confidence_for(score, thresholds)
        scored.append(
            {
                "id": feature["id"],
                "name": feature["name"],
                "aliases": feature.get("aliases", []),
                "status": feature.get("status", "active"),
                "score": score,
                "confidence": confidence,
                "evidence": evidence,
                "overview_path": feature["overview_path"],
                "read_before_code": [*PROJECT_MEMORY, feature["overview_path"]],
                "_strong_sources": sorted(strong_sources),
            }
        )
    scored.sort(key=lambda item: (-item["score"], item["id"]))
    return scored


def load_features(target: Path) -> list[dict[str, Any]]:
    indexed = target / "noc_docs/.living-docs/feature-index.json"
    if indexed.is_file():
        try:
            data = json.loads(indexed.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        features = data.get("features")
        if isinstance(features, list):
            return [hydrate_feature(target, feature) for feature in features if isinstance(feature, dict)]
    return scan_overviews(target)


def hydrate_feature(target: Path, feature: dict[str, Any]) -> dict[str, Any]:
    overview_path = feature.get("overview_path")
    hydrated = dict(feature)
    if isinstance(overview_path, str) and (target / overview_path).is_file():
        hydrated["body"] = (target / overview_path).read_text(encoding="utf-8", errors="replace")
        frontmatter = parse_frontmatter_file(target / overview_path)
        hydrated.setdefault("aliases", frontmatter.get("aliases", []))
    else:
        hydrated.setdefault("body", "")
    return hydrated


def scan_overviews(target: Path) -> list[dict[str, Any]]:
    features = []
    root = target / "noc_docs/features"
    if not root.is_dir():
        return features
    for overview in sorted(root.glob("*/overview.md")):
        frontmatter = parse_frontmatter_file(overview)
        if not frontmatter:
            continue
        features.append(
            {
                "id": frontmatter.get("id", overview.parent.name),
                "name": frontmatter.get("name", overview.parent.name),
                "aliases": frontmatter.get("aliases", []),
                "status": frontmatter.get("status", "active"),
                "language": frontmatter.get("language"),
                "overview_path": overview.relative_to(target).as_posix(),
                "updated_at": frontmatter.get("updated_at"),
                "body": overview.read_text(encoding="utf-8", errors="replace"),
            }
        )
    return features


def score_feature(feature: dict[str, Any], paths: list[str], intent: str | None) -> tuple[float, list[dict[str, str]], set[str]]:
    score = 0.0
    evidence: list[dict[str, str]] = []
    strong_sources: set[str] = set()
    intent_norm = normalize_text(intent or "")
    if intent_norm:
        fid = normalize_text(feature["id"])
        name = normalize_text(feature.get("name", ""))
        if intent_norm == fid or fid in intent_norm:
            score += 0.85
            evidence.append({"type": "feature_id_match", "value": feature["id"]})
            strong_sources.add("intent")
        has_strong_intent = False
        if name and (intent_norm == name or name in intent_norm):
            score += 0.78
            evidence.append({"type": "name_match", "value": feature.get("name", "")})
            strong_sources.add("intent")
            has_strong_intent = True
        for alias in feature.get("aliases", []):
            alias_norm = normalize_text(alias)
            if alias_norm and (intent_norm == alias_norm or alias_norm in intent_norm):
                score += 0.78
                evidence.append({"type": "alias_match", "value": alias})
                strong_sources.add("intent")
                has_strong_intent = True
        if not has_strong_intent:
            overlap = tokens(intent_norm) & (tokens(feature.get("body", "")) | tokens(feature.get("name", "")))
            weak = sorted(token for token in overlap if len(token) >= 2 and token not in {normalize_text(a) for a in feature.get("aliases", [])})
            if weak:
                score += min(0.12 + len(weak) * 0.04, 0.32)
                evidence.append({"type": "keyword_overlap", "value": " ".join(weak[:5])})
    code_paths = extract_code_paths(feature.get("body", ""))
    for changed in paths:
        normalized_changed = normalize_path(changed)
        for candidate in code_paths:
            if normalized_changed == candidate.rstrip("/"):
                score += 0.85
                evidence.append({"type": "code_path_exact_match", "value": candidate})
                strong_sources.add("path")
            elif candidate.endswith("/") and normalized_changed.startswith(candidate):
                score += 0.72
                evidence.append({"type": "code_path_prefix_match", "value": candidate})
                strong_sources.add("path")
    return score, dedupe_evidence(evidence), strong_sources


def extract_code_paths(body: str) -> list[str]:
    values = []
    for match in re.finditer(r"`([^`]+)`", body):
        value = normalize_path(match.group(1).strip())
        if "/" in value or "\\" in value:
            values.append(value if not value.endswith("\\") else value[:-1] + "/")
    return sorted(dict.fromkeys(values))


def dedupe_evidence(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for item in evidence:
        key = (item["type"], item["value"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def confidence_for(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds["high_confidence"]:
        return "high"
    if score >= thresholds["medium_confidence"]:
        return "medium"
    return "low"


def ambiguity_for(candidates: list[dict[str, Any]], thresholds: dict[str, float]) -> dict[str, Any]:
    if len(candidates) < 2:
        return {"is_ambiguous": False, "top_delta": None}
    top_delta = round(candidates[0]["score"] - candidates[1]["score"], 2)
    return {"is_ambiguous": top_delta < thresholds["ambiguity_delta"], "top_delta": top_delta}


def action_for(candidates: list[dict[str, Any]], ambiguity: dict[str, Any]) -> str:
    if not candidates:
        return "no_match"
    if ambiguity.get("is_ambiguous"):
        return "ask_user"
    return "use_existing"
