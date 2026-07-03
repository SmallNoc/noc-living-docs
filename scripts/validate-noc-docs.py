#!/usr/bin/env python3
"""Validate NOC Living Docs repository and project invariants."""

from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- noc-living-docs:start -->"
END = "<!-- noc-living-docs:end -->"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def require(path: str) -> None:
    if not (ROOT / path).exists():
        fail(f"missing required path: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate NOC Living Docs.")
    parser.add_argument(
        "--target",
        help="Optional project directory to validate. Without this, validate the NOC repository.",
    )
    return parser.parse_args()


def check_required_paths() -> None:
    required = [
        "README.md",
        "CHANGELOG.md",
        "VERSION",
        "docs/migration-reports/TEMPLATE.md",
        "protocol/AGENT_PROTOCOL.md",
        "protocol/DOCUMENT_STRUCTURE.md",
        "protocol/LANGUAGE_POLICY.md",
        "protocol/TOKEN_POLICY.md",
        "protocol/CONFLICT_POLICY.md",
        "scripts/noc.py",
        "scripts/init-noc-docs.py",
        "scripts/index-noc-docs.py",
        "scripts/release.py",
        "scripts/validate-noc-docs.py",
        "templates/AGENTS.md",
        "templates/noc_docs/project-status.md",
        "templates/noc_docs/docs-map.md",
        "templates/noc_docs/.living-docs/config.json",
        "skills/codex/project-living-docs/SKILL.md",
    ]
    for path in required:
        require(path)


def check_config() -> None:
    config_path = ROOT / "templates/noc_docs/.living-docs/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("documentation_root") != "noc_docs":
        fail("documentation_root must be noc_docs")
    if config.get("language") != "zh-CN":
        fail("default language must be zh-CN")
    if config.get("machine_keys") != "en-US":
        fail("machine_keys must be en-US")


def check_skill_frontmatter() -> None:
    skill = (ROOT / "skills/codex/project-living-docs/SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\n"):
        fail("Codex skill must start with YAML frontmatter")
    if "name: project-living-docs" not in skill:
        fail("Codex skill name must be project-living-docs")
    if "description: Use when" not in skill:
        fail("Codex skill description must start with Use when")


def check_no_docs_root_template() -> None:
    forbidden = ROOT / "templates/docs"
    if forbidden.exists():
        fail("templates/docs must not exist; use templates/noc_docs")


def check_project(target: Path) -> None:
    noc_docs = target / "noc_docs"
    if not noc_docs.exists():
        fail(f"{target} does not contain noc_docs")
    if (target / "docs").exists():
        print("WARNING: target has docs/; NOC protocol still uses noc_docs/")

    config_path = noc_docs / ".living-docs/config.json"
    if not config_path.exists():
        fail("target missing noc_docs/.living-docs/config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("documentation_root") != "noc_docs":
        fail("target config documentation_root must be noc_docs")

    has_features = (noc_docs / "features").exists()
    has_domains = (noc_docs / "domains").exists()
    mode = config.get("mode")
    if mode == "small" and not has_features:
        fail("small mode target must contain noc_docs/features")
    if mode == "domain" and not has_domains:
        fail("domain mode target must contain noc_docs/domains")
    if has_features and has_domains:
        fail("target must not initialize both noc_docs/features and noc_docs/domains")

    agent_files = [target / name for name in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]]
    existing_agent_files = [path for path in agent_files if path.exists()]
    if not existing_agent_files:
        fail("target must contain at least one agent entry file")
    if not any(START in path.read_text(encoding="utf-8") and END in path.read_text(encoding="utf-8") for path in existing_agent_files):
        fail("no agent entry file contains NOC managed block")


def main() -> None:
    args = parse_args()
    if args.target:
        check_project(Path(args.target).resolve())
        print("NOC project validation passed.")
    else:
        check_required_paths()
        check_config()
        check_skill_frontmatter()
        check_no_docs_root_template()
        print("NOC Living Docs validation passed.")


if __name__ == "__main__":
    main()
