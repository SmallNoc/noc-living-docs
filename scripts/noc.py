#!/usr/bin/env python3
"""Unified CLI for NOC Living Docs."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
START = "# noc-living-docs:start"
END = "# noc-living-docs:end"


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
            "",
            START,
            f"raise SystemExit(subprocess.call([sys.executable, {cli_path!r}, 'check', '--staged', '--warn-only']))",
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
                return 0 if args.warn_only else 1
            return 0
        print("WARNING: docs changed, but not for affected feature(s): " + ", ".join(mapped))
        return 0 if args.warn_only else 1

    print("WARNING: code changed but no noc_docs files changed.")
    if mapped:
        print("Affected mapped feature(s): " + ", ".join(mapped))
    else:
        print("No feature mapping found. Update noc_docs or run index after documenting the feature.")
    print("If docs are intentionally unchanged, mention that in the commit or final agent response.")
    return 0 if args.warn_only else 1


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
    check.add_argument("--warn-only", action="store_true", help="Return success even when docs are missing.")
    check.set_defaults(func=command_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
