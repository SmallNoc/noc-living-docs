#!/usr/bin/env python3
"""Unified CLI for NOC Living Docs."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
START = "# noc-living-docs:start"
END = "# noc-living-docs:end"
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


def run_script(name: str, args: list[str]) -> int:
    script = SCRIPT_DIR / name
    return subprocess.call([sys.executable, str(script), *args])


def command_init(args: argparse.Namespace) -> int:
    forwarded = [str(args.target), "--mode", args.mode, "--agent-file", args.agent_file]
    if args.force:
        forwarded.append("--force")
    code = run_script("init-noc-docs.py", forwarded)
    if code == 0 and args.index:
        code = run_script("index-noc-docs.py", [str(args.target)])
    return code


def command_index(args: argparse.Namespace) -> int:
    return run_script("index-noc-docs.py", [str(args.target)])


def command_validate(args: argparse.Namespace) -> int:
    forwarded = []
    if args.target:
        forwarded.extend(["--target", str(args.target)])
    return run_script("validate-noc-docs.py", forwarded)


def git_root(target: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(f"ERROR: {target} is not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def hook_block() -> str:
    python_path = Path(sys.executable).resolve().as_posix()
    cli_path = Path(__file__).resolve().as_posix()
    return "\n".join(
        [
            f"#!{python_path}",
            "import subprocess",
            "import sys",
            "import shutil",
            "",
            START,
            f"fallback = [sys.executable, {cli_path!r}, 'check', '--staged', '--environment', 'local']",
            "entry = shutil.which('noc')",
            "cmd = [entry, 'check', '--staged', '--environment', 'local'] if entry else fallback",
            "raise SystemExit(subprocess.call(cmd))",
            END,
            "",
        ]
    )


def command_hook(args: argparse.Namespace) -> int:
    root = git_root(Path(args.target).resolve())
    hook_path = root / ".git/hooks/pre-commit"

    if args.action == "status":
        if not hook_path.exists():
            print("NOC pre-commit hook is not installed.")
            return 0
        text = hook_path.read_text(encoding="utf-8")
        print("NOC pre-commit hook is installed." if START in text and END in text else "Pre-commit hook exists without NOC block.")
        return 0

    if args.action == "uninstall":
        if not hook_path.exists():
            print("No pre-commit hook to uninstall.")
            return 0
        text = hook_path.read_text(encoding="utf-8")
        if START in text and END in text:
            before = text[: text.index(START)]
            after = text[text.index(END) + len(END) :]
            cleaned = (before + after).strip()
            if cleaned in {"", "#!/bin/sh"}:
                hook_path.unlink()
                print("Removed NOC pre-commit hook.")
            else:
                hook_path.write_text(cleaned + "\n", encoding="utf-8", newline="\n")
                print("Removed NOC pre-commit hook block.")
        else:
            print("No NOC hook block found.")
        return 0

    hook_path.parent.mkdir(parents=True, exist_ok=True)
    existing = hook_path.read_text(encoding="utf-8") if hook_path.exists() else ""
    block = hook_block()
    if START in existing and END in existing:
        before = existing[: existing.index(START)]
        after = existing[existing.index(END) + len(END) :]
        if before.strip() in {"", "#!/bin/sh"} and not after.strip():
            text = block
        else:
            text = before + "\n".join(block.splitlines()[4:]) + after
        action = "Updated"
    else:
        text = block if not existing.strip() else existing.rstrip() + "\n\n" + "\n".join(block.splitlines()[4:])
        action = "Installed"
    hook_path.write_text(text, encoding="utf-8", newline="\n")
    try:
        hook_path.chmod(hook_path.stat().st_mode | 0o111)
    except OSError:
        pass
    print(f"{action} NOC pre-commit hook at {hook_path}")
    return 0


def changed_files(target: Path, staged: bool) -> list[str]:
    args = ["git", "-C", str(target), "diff", "--name-only"]
    if staged:
        args.insert(4, "--cached")
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "ERROR: git diff failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def load_feature_map(target: Path) -> dict:
    path = target / "noc_docs/.living-docs/feature-map.json"
    if not path.exists():
        return {"features": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def command_check(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    strictness, strictness_source = resolve_check_strictness(target, args)
    print(f"Strictness: {strictness} (source: {strictness_source})")
    files = changed_files(target, args.staged)
    code_files = [f for f in files if not f.startswith("noc_docs/") and is_code_file(f)]
    docs_files = [f for f in files if f.startswith("noc_docs/")]

    if not code_files:
        print("No staged code changes requiring NOC docs check." if args.staged else "No code changes requiring NOC docs check.")
        return 0

    feature_map = load_feature_map(target)
    mapped: list[str] = []
    for feature_id, info in feature_map.get("features", {}).items():
        paths = info.get("paths", [])
        for changed in code_files:
            if any(path_matches(changed, pattern) for pattern in paths):
                mapped.append(feature_id)

    mapped = sorted(set(mapped))
    if docs_files:
        if not mapped:
            print(f"NOC docs changed with code: {len(docs_files)} doc file(s).")
            return 0
        covered = [feature_id for feature_id in mapped if feature_docs_changed(feature_map["features"].get(feature_id, {}), docs_files)]
        if covered:
            print("NOC docs changed for affected feature(s): " + ", ".join(covered))
            missing = sorted(set(mapped) - set(covered))
            if missing:
                print("WARNING: missing docs for affected feature(s): " + ", ".join(missing))
                emit_github_annotation(args, "missing docs for affected feature(s): " + ", ".join(missing), "warning" if strictness == "warn" else "error")
                return check_result(strictness)
            return 0
        print("WARNING: docs changed, but not for affected feature(s): " + ", ".join(mapped))
        emit_github_annotation(args, "docs changed, but not for affected feature(s): " + ", ".join(mapped), "warning" if strictness == "warn" else "error")
        return check_result(strictness)

    print("WARNING: code changed but no noc_docs files changed.")
    print_change_hints(code_files)
    if mapped:
        print("Affected mapped feature(s): " + ", ".join(mapped))
    else:
        print("No feature mapping found. Update noc_docs or run index after documenting the feature.")
    print("If docs are intentionally unchanged, mention that in the commit or final agent response.")
    emit_github_annotation(args, "code changed but no noc_docs files changed", "warning" if strictness == "warn" else "error")
    return check_result(strictness)


def resolve_check_strictness(target: Path, args: argparse.Namespace) -> tuple[str, str]:
    if args.warn_only:
        return "warn", "--warn-only"
    if args.strictness:
        return args.strictness, "--strictness"

    config = load_config(target)
    check_config = config.get("check", {}) if isinstance(config, dict) else {}
    strictness_config = check_config.get("strictness", {}) if isinstance(check_config, dict) else {}
    environment = args.environment or ("ci" if os.environ.get("CI") else "manual")

    if isinstance(strictness_config, dict):
        environments = strictness_config.get("environments", {})
        if isinstance(environments, dict) and environment in environments:
            value = environments[environment]
            if value in {"off", "warn", "fail"}:
                return value, f"config environment {environment}"
        value = strictness_config.get("default")
        if value in {"off", "warn", "fail"}:
            return value, "config default"

    if environment == "local":
        return "warn", "local environment"
    if environment == "ci":
        return "fail", "CI environment"
    return "fail", "default"


def load_config(target: Path) -> dict:
    path = target / "noc_docs/.living-docs/config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def check_result(strictness: str) -> int:
    if strictness in {"off", "warn"}:
        return 0
    return 1


def emit_github_annotation(args: argparse.Namespace, message: str, level: str) -> None:
    if not getattr(args, "github_annotations", False):
        return
    command = "warning" if level == "warning" else "error"
    print(f"::{command} title=NOC Living Docs::{message}")


def print_change_hints(code_files: list[str]) -> None:
    change_types = detect_change_types(code_files)
    if not change_types:
        return
    suggested_docs = suggested_docs_for(change_types)
    print("Detected change type(s): " + ", ".join(change_types))
    print("Suggested docs: " + ", ".join(suggested_docs))


def detect_change_types(files: list[str]) -> list[str]:
    detected: set[str] = set()
    for file in files:
        normalized = file.replace("\\", "/").lower()
        name = Path(normalized).name
        suffix = Path(normalized).suffix
        if suffix == ".sql" or "migration" in normalized:
            detected.add("schema")
        if name in {"dockerfile", "containerfile", "docker-compose.yml", "docker-compose.yaml"}:
            detected.add("deployment")
        if normalized.startswith(".github/workflows/") or "/.github/workflows/" in normalized:
            detected.add("ci")
        if any(part in normalized for part in ["auth", "permission", "security"]):
            detected.add("security")
        if any(part in normalized for part in ["api", "routes", "controllers"]):
            detected.add("api")
    return sorted(detected)


def suggested_docs_for(change_types: list[str]) -> list[str]:
    docs = ["status.md", "test-record.md"]
    if "deployment" in change_types or "ci" in change_types:
        docs.append("development/testing.md")
    if "security" in change_types:
        docs.append("guardrails.md")
    if "api" in change_types:
        docs.append("requirements.md")
    return list(dict.fromkeys(docs))


def command_suggest_map(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    suggestions = suggest_mappings(target)
    if args.interactive:
        count = interactive_write_suggestions(target, suggestions)
        print(f"Updated feature-map.json with {count} confirmed suggestion(s).")
        return 0
    if args.write:
        if not args.yes:
            print("Refusing to write suggestions without confirmation.")
            print("Use `noc suggest-map <project> --interactive` to review one by one, or `--write --yes` for automation.")
            return 1
        count = write_suggestions(target, suggestions)
        print(f"Updated feature-map.json with {count} suggestion(s).")
        return 0
    print(json.dumps({"suggestions": suggestions}, indent=2, ensure_ascii=False))
    return 0


def command_work(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    feature_map = load_feature_map(target)
    features = resolve_work_features(feature_map, args.feature, args.path or [])

    print("NOC work plan")
    print("=============")
    if args.intent:
        print(f"Intent: {args.intent}")
    if args.path:
        print("Changed or planned path(s): " + ", ".join(args.path))
    print()

    if features:
        for feature_id in features:
            print_feature_work_plan(feature_id, feature_map.get("features", {}).get(feature_id, {}))
    else:
        print("Feature: unresolved")
        print("Read before code:")
        print("- noc_docs/docs-map.md")
        print("- noc_docs/project-status.md")
        print("- noc_docs/.living-docs/feature-map.json")
        print("Before coding:")
        print("- Decide the affected feature or create one under noc_docs/features/ or noc_docs/domains/<domain>/features/.")
        print("- Write the agreed requirement into requirements.md or capture uncertain discussion in notes.md.")
        print("Update after code:")
        print("- status.md when actual behavior changes")
        print("- test-record.md with verification commands and results")
        print("- change-record.md for important changes")
        print("- guardrails.md if new limits or compatibility rules appear")
        print()

    print("Finish:")
    print("- Run: python scripts/noc.py index <project>")
    print("- Before commit, run: python scripts/noc.py check <project> --staged")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    report = DoctorReport()

    report.ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if shutil.which("git"):
        report.ok("Git is available")
    else:
        report.error("Git is not available on PATH")
        report.fix("Install Git and ensure `git` is on PATH.")

    try:
        root = git_root(target)
        report.ok(f"target is inside Git repository: {root}")
    except SystemExit:
        root = None
        report.error("target is not inside a Git repository")
        report.fix("Run `git init` in the project or choose a project already managed by Git.")

    noc_docs = target / "noc_docs"
    if noc_docs.is_dir():
        report.ok("found noc_docs/")
    else:
        report.error("missing noc_docs/")
        report.fix(f"Run: noc init {target}")

    living_docs = noc_docs / ".living-docs"
    config = doctor_json(report, living_docs / "config.json", ["documentation_root", "mode"])
    feature_map = doctor_json(report, living_docs / "feature-map.json", ["mode", "features"])
    doctor_json(report, living_docs / "docs-index.json", ["documents"])
    doctor_json(report, living_docs / "manifest.json", ["files"])

    mode = config.get("mode") if isinstance(config, dict) else None
    feature_mode = feature_map.get("mode") if isinstance(feature_map, dict) else None
    if mode and feature_mode and mode != feature_mode:
        report.warn(f"config mode {mode} differs from feature-map mode {feature_mode}")
        report.fix("Run: noc index <project>")

    has_features = (noc_docs / "features").is_dir()
    has_domains = (noc_docs / "domains").is_dir()
    if mode == "small":
        if has_features and not has_domains:
            report.ok("mode small matches noc_docs/features")
        else:
            report.error("mode small does not match directory structure")
            report.fix("Use `noc init <project> --mode small` or update noc_docs/.living-docs/config.json.")
    elif mode == "domain":
        if has_domains and not has_features:
            report.ok("mode domain matches noc_docs/domains")
        else:
            report.error("mode domain does not match directory structure")
            report.fix("Use `noc init <project> --mode domain` or update noc_docs/.living-docs/config.json.")
    elif mode is not None:
        report.error(f"unknown mode: {mode}")
        report.fix("Set config mode to `small` or `domain`.")

    doctor_hook(report, root)

    print("Fix suggestions:")
    if report.fixes:
        for fix in report.fixes:
            print(f"- {fix}")
    else:
        print("- No action needed.")
    return 1 if report.errors else 0


class DoctorReport:
    def __init__(self) -> None:
        self.errors = 0
        self.warnings = 0
        self.fixes: list[str] = []

    def ok(self, message: str) -> None:
        print(f"OK: {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"WARN: {message}")

    def error(self, message: str) -> None:
        self.errors += 1
        print(f"ERROR: {message}")

    def fix(self, message: str) -> None:
        if message not in self.fixes:
            self.fixes.append(message)


def doctor_json(report: DoctorReport, path: Path, required_keys: list[str]) -> dict:
    rel = path.as_posix()
    if not path.exists():
        report.error(f"missing {rel}")
        report.fix("Run: noc init <project> && noc index <project>")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(f"invalid JSON in {rel}: {exc.msg}")
        report.fix(f"Fix JSON syntax in {rel}.")
        return {}
    report.ok(f"parsed {rel}")
    for key in required_keys:
        if key in data:
            report.ok(f"{rel} contains `{key}`")
        else:
            report.error(f"{rel} missing required key `{key}`")
            report.fix(f"Run: noc index <project> or restore `{key}` in {rel}.")
    return data if isinstance(data, dict) else {}


def doctor_hook(report: DoctorReport, root: Path | None) -> None:
    if root is None:
        return
    hook_path = root / ".git/hooks/pre-commit"
    if not hook_path.exists():
        report.warn("pre-commit hook is not installed")
        report.fix("Run: noc hook install <project>")
        return
    text = hook_path.read_text(encoding="utf-8", errors="replace")
    if START not in text or END not in text:
        report.warn("pre-commit hook exists without NOC managed block")
        report.fix("Run: noc hook install <project> to add the NOC managed block.")
        return
    if "'noc'" in text or '"noc"' in text or "scripts/noc.py" in text:
        report.ok("pre-commit hook references noc")
    else:
        report.error("pre-commit hook NOC block does not reference a valid entry")
        report.fix("Run: noc hook install <project> to refresh the hook.")


def resolve_work_features(feature_map: dict, feature: str | None, paths: list[str]) -> list[str]:
    all_features = feature_map.get("features", {})
    resolved: set[str] = set()
    if feature:
        resolved.add(feature)
    for changed in paths:
        for feature_id, info in all_features.items():
            if any(path_matches(changed, pattern) for pattern in info.get("paths", [])):
                resolved.add(feature_id)
    return sorted(resolved)


def print_feature_work_plan(feature_id: str, info: dict) -> None:
    print(f"Feature: {feature_id}")
    if info.get("domain"):
        print(f"Domain: {info['domain']}")

    read_docs = work_docs(info, ["entry", "requirements", "status", "guardrails", "tests"])
    print("Read before code:")
    for doc in read_docs:
        print(f"- {doc}")
    if not read_docs:
        print("- noc_docs/docs-map.md")
        print("- noc_docs/project-status.md")

    print("Before coding:")
    if info.get("requirements"):
        print(f"- Put the agreed requirement or behavior change in {info['requirements']}.")
    else:
        print("- Create or update requirements.md with the agreed requirement.")
    if info.get("notes"):
        print(f"- Put uncertain discussion or open questions in {info['notes']}.")

    print("Update after code:")
    after_docs = [
        ("status", "when actual behavior changes"),
        ("tests", "with verification commands and results"),
        ("change_record", "for important changes and reasons"),
        ("guardrails", "if new limits, risks, or compatibility rules appear"),
        ("requirements", "only when intended behavior changes"),
    ]
    printed = False
    for key, reason in after_docs:
        if info.get(key):
            print(f"- {info[key]} {reason}")
            printed = True
    if not printed:
        print("- status.md when actual behavior changes")
        print("- test-record.md with verification commands and results")
        print("- change-record.md for important changes and reasons")
        print("- guardrails.md if new limits, risks, or compatibility rules appear")
        print("- requirements.md only when intended behavior changes")
    print()


def work_docs(info: dict, keys: list[str]) -> list[str]:
    docs = []
    for key in keys:
        value = info.get(key)
        if isinstance(value, str) and value not in docs:
            docs.append(value)
    return docs


def suggest_mappings(target: Path) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    suggestions.extend(suggest_top_level_project_mappings(target))
    suggestions.extend(suggest_java_package_mappings(target))
    for base in ["src", "app", "apps", "packages", "services", "modules", "domains"]:
        root = target / base
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith(".") or child.name.startswith("_"):
                continue
            if child.name in {"main", "test"} and base == "src":
                continue
            if not directory_has_code(child):
                continue
            suggestions.append(
                {
                    "feature": child.name,
                    "path": child.relative_to(target).as_posix() + "/",
                }
            )
    return dedupe_suggestions(suggestions)


def suggest_top_level_project_mappings(target: Path) -> list[dict[str, str]]:
    ignored = {"node_modules", "target", "build", "dist", "out", "noc_docs"}
    suggestions = []
    for child in sorted(target.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name in ignored:
            continue
        if any((child / marker).exists() for marker in PROJECT_MARKERS):
            suggestions.append(
                {
                    "feature": child.name,
                    "path": child.relative_to(target).as_posix() + "/",
                }
            )
    return suggestions


def suggest_java_package_mappings(target: Path) -> list[dict[str, str]]:
    java_root = target / "src/main/java"
    if not java_root.is_dir():
        return []
    branch_root = java_root
    while True:
        child_dirs = [child for child in branch_root.iterdir() if child.is_dir() and not child.name.startswith(".")]
        java_files = [child for child in branch_root.iterdir() if child.is_file() and child.suffix == ".java"]
        if len(child_dirs) != 1 or java_files:
            break
        branch_root = child_dirs[0]
    suggestions = []
    for child in sorted(branch_root.iterdir()):
        if child.is_dir() and directory_has_code(child):
            suggestions.append(
                {
                    "feature": child.name,
                    "path": child.relative_to(target).as_posix() + "/",
                }
            )
    return suggestions


def dedupe_suggestions(suggestions: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    for suggestion in suggestions:
        key = (suggestion["feature"], suggestion["path"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(suggestion)
    return deduped


def suggestion_reason(path: str) -> str:
    if path.startswith("src/main/java/"):
        return "detected Java package branch containing code files"
    if path.split("/", 1)[0] in {"src", "app", "apps", "packages", "services", "modules", "domains"}:
        return "detected code directory under a common project root"
    return "detected top-level project directory with a project marker"


def interactive_write_suggestions(target: Path, suggestions: list[dict[str, str]]) -> int:
    if not sys.stdin.isatty() and sys.stdin.closed:
        print("Cannot run interactive confirmation without stdin.")
        print("Use --write --yes for automation or omit --write to print suggestions.")
        return 0

    existing = load_feature_map(target).get("features", {})
    accepted: list[dict[str, str]] = []
    for suggestion in suggestions:
        feature_id = suggestion["feature"]
        candidate_path = suggestion["path"]
        existing_paths = existing.get(feature_id, {}).get("paths", [])
        print(f"Feature: {feature_id}")
        print(f"Candidate path: {candidate_path}")
        print(f"Reason: {suggestion_reason(candidate_path)}")
        print("Existing feature: " + ("yes" if feature_id in existing else "no"))
        if candidate_path in existing_paths:
            print("Already mapped: yes")
            print()
            continue
        try:
            answer = input("Write this path to feature-map.json? [y/N] ").strip().lower()
        except EOFError:
            print()
            print("Interactive confirmation needs stdin.")
            print("Use --write --yes for automation or omit --write to print suggestions.")
            break
        if answer in {"y", "yes"}:
            accepted.append(suggestion)
        print()
    return write_suggestions(target, accepted)


def directory_has_code(path: Path) -> bool:
    for child in path.rglob("*"):
        if child.is_file() and is_code_file(child.name):
            return True
    return False


def write_suggestions(target: Path, suggestions: list[dict[str, str]]) -> int:
    path = target / "noc_docs/.living-docs/feature-map.json"
    if path.exists():
        feature_map = json.loads(path.read_text(encoding="utf-8"))
    else:
        feature_map = {"mode": "small", "features": {}}
    features = feature_map.setdefault("features", {})
    added = 0
    for suggestion in suggestions:
        feature_id = suggestion["feature"]
        candidate_path = suggestion["path"]
        entry = features.setdefault(feature_id, {})
        paths = entry.setdefault("paths", [])
        if candidate_path not in paths:
            paths.append(candidate_path)
            added += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feature_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return added


def is_code_file(path: str) -> bool:
    name = Path(path).name
    return Path(path).suffix.lower() in CODE_EXTS or name in CODE_FILENAMES


def path_matches(changed: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/").lstrip("./")
    changed = changed.replace("\\", "/")
    if not normalized:
        return False
    if any(char in normalized for char in "*?[]"):
        return fnmatch.fnmatch(changed, normalized)
    if normalized.endswith("/"):
        return changed.startswith(normalized)
    return changed == normalized or changed.startswith(normalized.rstrip("/") + "/")


def feature_docs_changed(info: dict, docs_files: list[str]) -> bool:
    doc_paths = {
        value.replace("\\", "/")
        for key, value in info.items()
        if key
        in {
            "entry",
            "requirements",
            "status",
            "guardrails",
            "tests",
            "change_record",
            "notes",
        }
        and isinstance(value, str)
    }
    entry = info.get("entry")
    if isinstance(entry, str):
        doc_paths.add(str(Path(entry).parent).replace("\\", "/") + "/")
    for doc in docs_files:
        if any(path_matches(doc, expected) for expected in doc_paths):
            return True
    return False


CODE_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".json",
    ".jsonc",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sql",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    ".env",
    ".env.example",
    ".proto",
    ".graphql",
    ".gql",
    ".skill",
    ".tcl",
}


CODE_FILENAMES = {
    "Dockerfile",
    "Containerfile",
    "Makefile",
    "Justfile",
    "Procfile",
    "docker-compose.yaml",
    "docker-compose.yml",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOC Living Docs CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize NOC Living Docs in a project.")
    init.add_argument("target", nargs="?", default=".")
    init.add_argument("--mode", choices=["auto", "small", "domain"], default="auto")
    init.add_argument("--agent-file", choices=["AGENTS.md", "CLAUDE.md", "GEMINI.md"], default="AGENTS.md")
    init.add_argument("--force", action="store_true")
    init.add_argument("--no-index", dest="index", action="store_false")
    init.set_defaults(func=command_init)

    index = sub.add_parser("index", help="Build routing indexes.")
    index.add_argument("target", nargs="?", default=".")
    index.set_defaults(func=command_index)

    validate = sub.add_parser("validate", help="Validate repository or target project.")
    validate.add_argument("--target")
    validate.set_defaults(func=command_validate)

    hook = sub.add_parser("hook", help="Install, uninstall, or inspect Git hook.")
    hook.add_argument("action", choices=["install", "uninstall", "status"])
    hook.add_argument("target", nargs="?", default=".")
    hook.set_defaults(func=command_hook)

    check = sub.add_parser("check", help="Check whether code changes need NOC docs updates.")
    check.add_argument("target", nargs="?", default=".")
    check.add_argument("--staged", action="store_true")
    check.add_argument("--strictness", choices=["off", "warn", "fail"], help="Override check strictness.")
    check.add_argument("--environment", choices=["manual", "local", "ci"], help="Select strictness environment.")
    check.add_argument("--github-annotations", action="store_true", help="Emit GitHub Actions warning/error annotations.")
    check.add_argument("--warn-only", action="store_true", help="Return success even when docs are missing.")
    check.set_defaults(func=command_check)

    suggest_map = sub.add_parser("suggest-map", help="Suggest feature path mappings.")
    suggest_map.add_argument("target", nargs="?", default=".")
    suggest_map.add_argument("--write", action="store_true", help="Merge suggestions into feature-map.json without overwriting existing paths.")
    suggest_map.add_argument("--yes", action="store_true", help="Confirm --write without interactive review.")
    suggest_map.add_argument("--interactive", action="store_true", help="Confirm suggestions one by one before writing.")
    suggest_map.set_defaults(func=command_suggest_map)

    work = sub.add_parser("work", help="Print the docs workflow for a planned code change.")
    work.add_argument("target", nargs="?", default=".")
    work.add_argument("--feature", help="Affected feature id.")
    work.add_argument("--path", action="append", help="Planned or changed code path. Can be repeated.")
    work.add_argument("--intent", help="Short description of the agreed requirement or change.")
    work.set_defaults(func=command_work)

    doctor = sub.add_parser("doctor", help="Check local NOC setup and print repair suggestions.")
    doctor.add_argument("target", nargs="?", default=".")
    doctor.set_defaults(func=command_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
