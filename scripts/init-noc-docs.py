#!/usr/bin/env python3
"""Initialize NOC Living Docs in a target project."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
START = "<!-- noc-living-docs:start -->"
END = "<!-- noc-living-docs:end -->"
PROJECT_MARKERS = {
    "pom.xml",
    "package.json",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize NOC Living Docs in a project.")
    parser.add_argument("target", nargs="?", default=".", help="Target project directory.")
    parser.add_argument(
        "--mode",
        choices=["auto", "small", "domain"],
        default="auto",
        help="Documentation layout mode.",
    )
    parser.add_argument(
        "--agent-file",
        choices=["AGENTS.md", "CLAUDE.md", "GEMINI.md"],
        default="AGENTS.md",
        help="Agent entry file to create or merge.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files inside noc_docs when they already exist. Existing agent rules are still preserved.",
    )
    return parser.parse_args()


def detect_mode(target: Path, requested: str) -> tuple[str, list[str]]:
    if requested != "auto":
        return requested, [f"user selected {requested} mode"]

    reasons: list[str] = []
    score = 0

    monorepo_markers = ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "rush.json"]
    if any((target / marker).exists() for marker in monorepo_markers):
        score += 2
        reasons.append("monorepo marker detected")

    top_level_projects = []
    for child in target.iterdir():
        if not child.is_dir() or child.name.startswith(".") or child.name in {"node_modules", "target", "build", "dist", "out"}:
            continue
        if any((child / marker).exists() for marker in PROJECT_MARKERS):
            top_level_projects.append(child)
    if len(top_level_projects) >= 3:
        reasons.append(f"detected {len(top_level_projects)} top-level project directories")
        return "domain", reasons

    app_service_dirs = []
    for name in ["apps", "packages", "services"]:
        path = target / name
        if path.is_dir():
            app_service_dirs.extend([p for p in path.iterdir() if p.is_dir()])
    if len(app_service_dirs) >= 3:
        reasons.append(f"detected {len(app_service_dirs)} app/service directories")
        return "domain", reasons

    domain_like_dirs = []
    for base in ["src/domains", "src/modules", "src/features", "domains", "modules"]:
        path = target / base
        if path.is_dir():
            domain_like_dirs.extend([p for p in path.iterdir() if p.is_dir()])
    if len(domain_like_dirs) >= 20:
        reasons.append(f"detected {len(domain_like_dirs)} probable features")
        return "domain", reasons
    elif len(domain_like_dirs) >= 8:
        score += 1
        reasons.append(f"detected {len(domain_like_dirs)} top-level modules")

    domain_names = {"auth", "billing", "payment", "admin", "reporting", "tenant", "security"}
    detected_domains = {p.name.lower() for p in domain_like_dirs if p.name.lower() in domain_names}
    if len(detected_domains) >= 3:
        reasons.append(f"detected probable domains: {', '.join(sorted(detected_domains))}")
        return "domain", reasons

    if score >= 5:
        return "domain", reasons or ["auto score selected domain mode"]
    return "small", reasons or ["defaulted to small mode"]


def managed_block_from_template(agent_file: str) -> str:
    template = (TEMPLATES / agent_file).read_text(encoding="utf-8")
    if START not in template or END not in template:
        raise RuntimeError(f"template {agent_file} is missing managed block markers")
    start = template.index(START)
    end = template.index(END) + len(END)
    return template[start:end]


def merge_agent_file(target: Path, agent_file: str) -> str:
    path = target / agent_file
    block = managed_block_from_template(agent_file)

    if not path.exists():
        title = "# Agent Protocol\n\n" if agent_file == "AGENTS.md" else f"# {agent_file.removesuffix('.md')} Protocol\n\n"
        path.write_text(title + block + "\n", encoding="utf-8")
        return f"created {agent_file}"

    existing = path.read_text(encoding="utf-8")
    if START in existing and END in existing:
        before = existing[: existing.index(START)]
        after = existing[existing.index(END) + len(END) :]
        path.write_text(before + block + after, encoding="utf-8")
        return f"updated managed block in {agent_file}"

    separator = "\n\n" if existing.endswith("\n") else "\n\n"
    path.write_text(existing + separator + block + "\n", encoding="utf-8")
    return f"appended managed block to {agent_file}"


def copy_file(src: Path, dst: Path, force: bool, created: list[str], skipped: list[str]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        skipped.append(str(dst))
        return
    shutil.copy2(src, dst)
    created.append(str(dst))


def copy_common(target: Path, force: bool, created: list[str], skipped: list[str]) -> None:
    common_files = [
        "project-status.md",
        "docs-map.md",
        "development/git-workflow.md",
        "development/testing.md",
        "development/documentation-policy.md",
        ".living-docs/config.json",
        ".living-docs/manifest.json",
        ".living-docs/feature-map.json",
        ".living-docs/docs-index.json",
    ]
    for rel in common_files:
        copy_file(TEMPLATES / "noc_docs" / rel, target / "noc_docs" / rel, force, created, skipped)


def copy_mode(target: Path, mode: str, force: bool, created: list[str], skipped: list[str]) -> None:
    if mode == "small":
        files = [
            "features/index.md",
            "features/_feature/agent-guide.md",
            "features/_feature/requirements.md",
            "features/_feature/status.md",
            "features/_feature/guardrails.md",
            "features/_feature/test-record.md",
            "features/_feature/change-record.md",
            "features/_feature/notes.md",
        ]
    else:
        files = [
            "domains/index.md",
            "domains/_domain/index.md",
            "domains/_domain/guardrails.md",
            "domains/_domain/features/_feature/agent-guide.md",
            "domains/_domain/features/_feature/requirements.md",
            "domains/_domain/features/_feature/status.md",
            "domains/_domain/features/_feature/guardrails.md",
            "domains/_domain/features/_feature/test-record.md",
            "domains/_domain/features/_feature/change-record.md",
            "domains/_domain/features/_feature/notes.md",
        ]
    for rel in files:
        copy_file(TEMPLATES / "noc_docs" / rel, target / "noc_docs" / rel, force, created, skipped)


def update_config(target: Path, mode: str) -> None:
    path = target / "noc_docs/.living-docs/config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["mode"] = mode
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    mode, reasons = detect_mode(target, args.mode)
    created: list[str] = []
    skipped: list[str] = []

    agent_result = merge_agent_file(target, args.agent_file)
    copy_common(target, args.force, created, skipped)
    copy_mode(target, mode, args.force, created, skipped)
    update_config(target, mode)

    print(f"NOC Living Docs initialized in {target}")
    print(f"Mode: {mode}")
    print("Reasons:")
    for reason in reasons:
        print(f"- {reason}")
    print(f"Agent file: {agent_result}")
    print(f"Created/updated files: {len(created)}")
    print(f"Skipped existing files: {len(skipped)}")


if __name__ == "__main__":
    main()

