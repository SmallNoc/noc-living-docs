#!/usr/bin/env python3
"""Initialize NOC Living Docs in a target project."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
START = "<!-- noc-living-docs:start -->"
END = "<!-- noc-living-docs:end -->"
SIMPLIFIED_AGENT_BLOCK = """<!-- noc-living-docs:start -->

## NOC Project Memory

1. Before changing code, use `noc work <project> --path <code/path> --json` and read the minimal project memory it returns.
2. Update project memory only when the change creates a new fact that future sessions must know.
3. Routine implementation fixes, formatting, and small refactors do not require memory updates.
4. Users do not need to run NOC advanced commands manually.
5. If `noc` is unavailable, install `noc-living-docs` and run `noc setup`.

<!-- noc-living-docs:end -->"""
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
    parser.add_argument("--layout", choices=["legacy", "simplified"], default="legacy", help=argparse.SUPPRESS)
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


def managed_block_from_template(agent_file: str, layout: str = "legacy") -> str:
    if layout == "simplified":
        return SIMPLIFIED_AGENT_BLOCK
    template = (TEMPLATES / agent_file).read_text(encoding="utf-8")
    if START not in template or END not in template:
        raise RuntimeError(f"template {agent_file} is missing managed block markers")
    start = template.index(START)
    end = template.index(END) + len(END)
    return template[start:end]


def merge_agent_file(target: Path, agent_file: str, layout: str = "legacy") -> str:
    path = target / agent_file
    block = managed_block_from_template(agent_file, layout)

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


def detected_project_facts(target: Path) -> dict[str, list[str]]:
    markers = sorted(marker for marker in PROJECT_MARKERS if (target / marker).is_file())
    readmes = sorted(path.name for path in target.iterdir() if path.is_file() and path.name.lower().startswith("readme"))
    source_candidates = ["src", "app", "apps", "lib", "packages", "services"]
    test_candidates = ["tests", "test", "spec", "src/test"]
    sources = [path for path in source_candidates if (target / path).is_dir()]
    tests = [path for path in test_candidates if (target / path).is_dir()]
    return {"markers": markers, "readmes": readmes, "sources": sources, "tests": tests}


def bullet(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "待确认"


def simplified_project_text(target: Path, facts: dict[str, list[str]]) -> str:
    title = target.name
    if facts["readmes"]:
        readme = target / facts["readmes"][0]
        for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("# ") and line[2:].strip():
                title = line[2:].strip()
                break
    return f"""# Project Memory: {title}

## 项目目标

待确认。请以项目源码和用户明确说明为准。

## 当前阶段

待确认。

## 主要能力

待确认。

## 已识别结构

- 项目标志：{bullet(facts['markers'])}
- README：{bullet(facts['readmes'])}
- 主要源码目录：{bullet(facts['sources'])}
- 测试目录：{bullet(facts['tests'])}

## 技术边界

仅记录可从仓库确认的技术事实；其他边界待确认。
"""


def verification_candidates(facts: dict[str, list[str]]) -> list[str]:
    markers = set(facts["markers"])
    candidates = []
    if "pyproject.toml" in markers:
        candidates.append("`python -m pytest`（需确认项目是否使用 pytest）")
    if "package.json" in markers:
        candidates.append("`npm test`（需确认 package scripts）")
    if "pom.xml" in markers:
        candidates.append("`mvn test`（需确认 Maven 配置）")
    if {"build.gradle", "build.gradle.kts"} & markers:
        candidates.append("`./gradlew test`（Windows 可使用 `gradlew.bat test`，需确认 Gradle 配置）")
    return candidates


def write_if_missing(path: Path, content: str, managed: list[str], target: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    managed.append(path.relative_to(target).as_posix())


def initialize_simplified(target: Path, agent_file: str) -> None:
    facts = detected_project_facts(target)
    managed: list[str] = []
    merge_agent_file(target, agent_file, "simplified")
    write_if_missing(target / "noc_docs/project.md", simplified_project_text(target, facts), managed, target)
    write_if_missing(
        target / "noc_docs/guardrails.md",
        "# Project Guardrails\n\n## 硬约束\n\n- 不编造无法从项目文件或用户说明确认的事实。\n- 保留用户已有内容，破坏性操作必须先确认。\n\n## 项目特定约束\n\n待确认。\n",
        managed,
        target,
    )
    write_if_missing(
        target / "noc_docs/verification.md",
        "# Project Verification\n\n## 标准验证\n\n"
        + ("\n".join(f"- {item}" for item in verification_candidates(facts)) or "待确认。请从项目配置、现有测试和 CI 文件确定命令。")
        + "\n\n## 已识别测试目录\n\n"
        + bullet(facts["tests"])
        + "\n",
        managed,
        target,
    )
    living = target / "noc_docs/.living-docs"
    living.mkdir(parents=True, exist_ok=True)
    config = {
        "protocol": "noc-living-docs",
        "protocol_version": 2,
        "layout": "simplified",
        "documentation_root": "noc_docs",
        "language": "zh-CN",
        "machine_keys": "en-US",
    }
    routing = {
        "protocol_version": 2,
        "layout": "simplified",
        "routes": [{"path": "**", "memory": ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"]}],
        "detected_paths": {"source": facts["sources"], "tests": facts["tests"]},
    }
    managed.extend(["noc_docs/.living-docs/config.json", "noc_docs/.living-docs/routing.json", "noc_docs/.living-docs/manifest.json"])
    (living / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (living / "routing.json").write_text(json.dumps(routing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files = {}
    for relative in managed:
        path = target / relative
        if path.name == "manifest.json":
            continue
        files[relative] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    manifest = {"protocol_version": 2, "layout": "simplified", "managed_files": managed, "files": files}
    (living / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    if args.layout == "simplified":
        initialize_simplified(target, args.agent_file)
        return

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

