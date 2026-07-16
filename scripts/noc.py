#!/usr/bin/env python3
"""Unified CLI for NOC Living Docs."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.noclib.schemas import validate_config_schema, validate_overview_frontmatter
from scripts.noclib.candidates import feature_archive_work_plan
from scripts.noclib.features import ensure_feature
from scripts.noclib.feature_update import update_feature

SCRIPT_DIR = ROOT / "scripts"
TEMPLATES = ROOT / "templates/noc_docs"
SKILL_NAME = "project-living-docs"
SKILL_MANIFEST = "noc-skill.json"
SKILL_MANAGER = "noc-living-docs"
SKILL_MANAGER_ID = "b7cf6fd1-0f93-4b97-9b39-eec3aebcbd70"
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
FEATURE_DOC_FILES = [
    "agent-guide.md",
    "requirements.md",
    "status.md",
    "guardrails.md",
    "test-record.md",
    "change-record.md",
    "notes.md",
]
FEATURE_TITLE_PREFIXES = {
    "agent-guide.md": "# Agent Guide: ",
    "requirements.md": "# Requirements: ",
    "status.md": "# Current Status: ",
    "guardrails.md": "# Guardrails: ",
    "test-record.md": "# Test Record: ",
    "change-record.md": "# Change Record: ",
    "notes.md": "# Notes: ",
}


def cli_version() -> str:
    source_version = ROOT / "VERSION"
    if source_version.is_file():
        return source_version.read_text(encoding="utf-8").strip()
    try:
        return importlib.metadata.version("noc-living-docs")
    except importlib.metadata.PackageNotFoundError:
        raise RuntimeError("Cannot determine noc-living-docs version")


def default_codex_home(home: Path) -> Path:
    return home / ".codex"


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser().resolve() if configured else default_codex_home(Path.home()).resolve()


def bundled_skill_root() -> Path:
    source_root = ROOT / ".agents/skills" / SKILL_NAME
    if source_root.is_dir():
        return source_root
    return ROOT / "noc_assets/project_living_docs"


def read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def valid_managed_manifest(manifest: dict | None) -> bool:
    if manifest is None:
        return False
    required_files = manifest.get("required_files")
    if not isinstance(required_files, list) or not required_files:
        return False
    if not all(
        isinstance(relative, str)
        and relative
        and not Path(relative).is_absolute()
        and ".." not in Path(relative).parts
        for relative in required_files
    ):
        return False
    return (
        manifest.get("schema_version") == "1.0"
        and manifest.get("name") == SKILL_NAME
        and manifest.get("managed_by") == SKILL_MANAGER
        and manifest.get("manager_id") == SKILL_MANAGER_ID
        and isinstance(manifest.get("version"), str)
        and {"SKILL.md", SKILL_MANIFEST}.issubset(required_files)
    )


def is_managed_skill_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink() and valid_managed_manifest(read_json(path / SKILL_MANIFEST))


def skill_files_match(source: Path, target: Path, manifest: dict) -> bool:
    for relative in manifest.get("required_files", []):
        source_file = source / relative
        target_file = target / relative
        if not source_file.is_file() or not target_file.is_file():
            return False
        if source_file.read_bytes() != target_file.read_bytes():
            return False
    return True


def setup_state(home: Path) -> dict:
    source = bundled_skill_root()
    bundled = read_json(source / SKILL_MANIFEST)
    version = cli_version()
    target = home / "skills" / SKILL_NAME
    state = {
        "schema_version": "1.0",
        "codex_home": str(home),
        "skill_path": str(target),
        "cli_version": version,
        "skill_version": None,
        "status": "error",
        "action": "none",
        "next_action": "noc setup",
        "error_code": "SETUP_ERROR",
    }
    if not valid_managed_manifest(bundled):
        state.update(status="bundle_invalid", next_action="Reinstall noc-living-docs", error_code="BUNDLED_SKILL_INVALID")
        return state
    if bundled.get("version") != version:
        state.update(
            status="bundle_version_mismatch",
            skill_version=bundled.get("version"),
            next_action="Install a noc-living-docs package with matching CLI and Skill versions",
            error_code="BUNDLED_VERSION_MISMATCH",
        )
        return state
    if not target.exists():
        state.update(status="missing", next_action="noc setup", error_code="SKILL_NOT_INSTALLED")
        return state
    if target.is_symlink() or not target.is_dir():
        state.update(status="unmanaged", next_action=f"Choose a different Skill name or remove {target} yourself", error_code="SKILL_NOT_MANAGED")
        return state
    installed = read_json(target / SKILL_MANIFEST)
    if not valid_managed_manifest(installed):
        state.update(status="unmanaged", next_action=f"Keep or move your custom Skill at {target}", error_code="SKILL_NOT_MANAGED")
        return state
    state["skill_version"] = installed.get("version")
    if installed.get("version") != version:
        state.update(status="outdated", next_action="noc setup", error_code="VERSION_MISMATCH")
    elif not skill_files_match(source, target, bundled):
        state.update(status="damaged", next_action="noc setup --repair", error_code="SKILL_DAMAGED")
    else:
        state.update(status="ready", next_action="noc init .", error_code=None)
    return state


class SetupInstallError(Exception):
    pass


def install_managed_skill(home: Path) -> None:
    source = bundled_skill_root()
    target = home / "skills" / SKILL_NAME
    skills_dir = target.parent
    skills_dir.mkdir(parents=True, exist_ok=True)
    backup = skills_dir / f".{SKILL_NAME}.backup"
    if backup.exists():
        if not is_managed_skill_dir(backup):
            raise SetupInstallError(f"Reserved backup path is not NOC-managed: {backup}")
        if not target.exists():
            backup.rename(target)
        elif is_managed_skill_dir(target):
            shutil.rmtree(backup)
        else:
            raise SetupInstallError(f"Cannot reconcile setup backup with unmanaged target: {target}")

    temporary_root = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}.", dir=skills_dir))
    temporary = temporary_root / SKILL_NAME
    try:
        shutil.copytree(source, temporary, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "__init__.py"))
        if target.exists():
            target.rename(backup)
        try:
            temporary.rename(target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.rename(target)
            raise
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    if backup.exists() and is_managed_skill_dir(backup):
        shutil.rmtree(backup)


def print_setup_result(state: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
        return
    status = state["status"]
    if status == "ready":
        if state["action"] == "installed":
            print(f"Installed NOC Codex Skill {state['skill_version']} at {state['skill_path']}.")
        elif state["action"] == "upgraded":
            print(f"Upgraded NOC Codex Skill to {state['skill_version']} at {state['skill_path']}.")
        elif state["action"] == "repaired":
            print(f"Repaired NOC Codex Skill {state['skill_version']} at {state['skill_path']}.")
        else:
            print(f"NOC Codex Skill already up to date and matches CLI version {state['cli_version']}.")
        print("NOC is ready for Codex.")
        print(f"Next: {state['next_action']}")
    elif status == "missing":
        print("Codex integration is not installed.")
        print("Next: noc setup")
    elif status == "damaged":
        print("The NOC-managed Codex Skill is incomplete or modified.")
        print("Next: noc setup --repair")
    elif status == "outdated":
        print(f"Codex Skill version {state['skill_version']} does not match CLI version {state['cli_version']}.")
        print("Next: noc setup")
    elif status == "unmanaged":
        print(f"A user-maintained Skill already exists at {state['skill_path']}; NOC will not overwrite it.")
        print(f"Next: {state['next_action']}")
    elif status == "install_error":
        print("NOC could not safely update the Codex Skill installation.")
        print(f"Next: {state['next_action']}")
    else:
        print("The bundled Codex Skill does not match this CLI installation.")
        print(f"Next: {state['next_action']}")


def command_setup(args: argparse.Namespace) -> int:
    home = codex_home()
    state = setup_state(home)
    if not args.check:
        action = None
        if state["status"] == "missing":
            action = "installed"
        elif state["status"] == "outdated":
            action = "upgraded"
        elif state["status"] == "damaged" and args.repair:
            action = "repaired"
        if action:
            try:
                install_managed_skill(home)
            except (OSError, SetupInstallError) as error:
                state.update(
                    status="install_error",
                    action="none",
                    next_action=str(error),
                    error_code="INSTALL_PATH_CONFLICT" if isinstance(error, SetupInstallError) else "SETUP_IO_ERROR",
                )
            else:
                state = setup_state(home)
                state["action"] = action
    print_setup_result(state, args.json)
    if state["status"] == "ready":
        return 0
    return 2 if state["status"] == "unmanaged" else 1


def run_script(name: str, args: list[str]) -> int:
    script = SCRIPT_DIR / name
    return subprocess.call([sys.executable, str(script), *args])


def command_init(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    existing_config = load_config(target)
    if args.mode is None and existing_config.get("protocol_version") == 2 and existing_config.get("layout") in {"simplified", "feature-archive"}:
        print("Project memory is ready. Continue using Codex normally.")
        return 0
    has_legacy_layout = (target / "noc_docs/features").is_dir() or (target / "noc_docs/domains").is_dir()
    feature_archive = args.mode is None and not has_legacy_layout and existing_config.get("protocol_version") != 1
    if feature_archive:
        state = setup_state(codex_home())
        if state["status"] != "ready":
            actions = {
                "missing": "noc setup",
                "outdated": "noc setup",
                "damaged": "noc setup --repair",
            }
            print(actions.get(state["status"], state.get("next_action") or "noc setup"))
            return 1
        forwarded = [str(target), "--layout", "feature-archive", "--agent-file", args.agent_file]
    else:
        mode = args.mode or detect_docs_mode(target)
        forwarded = [str(target), "--mode", mode, "--agent-file", args.agent_file]
    if args.force:
        forwarded.append("--force")
    code = run_script("init-noc-docs.py", forwarded)
    if code == 0 and (feature_archive or args.index):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "index-noc-docs.py"), str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        code = result.returncode
        if code != 0:
            sys.stderr.write(result.stderr or result.stdout)
    if code == 0 and feature_archive:
        health = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate-noc-docs.py"), "--target", str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        code = health.returncode
        if code != 0:
            sys.stderr.write(health.stderr or health.stdout)
    if code == 0 and feature_archive:
        print("Project memory is ready. Continue using Codex normally.")
    return code


def command_index(args: argparse.Namespace) -> int:
    return run_script("index-noc-docs.py", [str(args.target)])


def command_validate(args: argparse.Namespace) -> int:
    forwarded = []
    target = args.target or args.target_positional
    if target:
        forwarded.extend(["--target", str(target)])
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


def save_feature_map(target: Path, feature_map: dict) -> None:
    path = target / "noc_docs/.living-docs/feature-map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feature_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_config(target: Path) -> dict:
    path = target / "noc_docs/.living-docs/config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def detect_docs_mode(target: Path) -> str:
    config = load_config(target)
    mode = config.get("mode")
    if mode in {"small", "domain"}:
        return mode
    noc_docs = target / "noc_docs"
    if (noc_docs / "domains").exists() and not (noc_docs / "features").exists():
        return "domain"
    return "small"


def normalize_feature_id(value: str, kind: str = "feature", allow_template_name: bool = False) -> str:
    normalized = value.strip()
    if not normalized:
        raise SystemExit(f"ERROR: {kind} id cannot be empty")
    if any(sep in normalized for sep in ["/", "\\"]):
        raise SystemExit(f"ERROR: {kind} id must be a simple name, not a path")
    if normalized.startswith("."):
        raise SystemExit(f"ERROR: {kind} id cannot start with . or _")
    if normalized.startswith("_") and not allow_template_name:
        raise SystemExit(f"ERROR: {kind} id cannot start with . or _")
    return normalized


def require_noc_docs(target: Path) -> None:
    if not (target / "noc_docs").is_dir():
        raise SystemExit(f"ERROR: {target / 'noc_docs'} does not exist. Run `noc init {target}` first.")


def feature_template_dir(mode: str) -> Path:
    if mode == "domain":
        return TEMPLATES / "domains/_domain/features/_feature"
    return TEMPLATES / "features/_feature"


def feature_dir(target: Path, mode: str, feature_id: str, domain: str | None = None) -> Path:
    if mode == "domain":
        if not domain:
            raise SystemExit("ERROR: domain mode requires --domain")
        return target / "noc_docs/domains" / domain / "features" / feature_id
    return target / "noc_docs/features" / feature_id


def domain_dir(target: Path, domain: str) -> Path:
    return target / "noc_docs/domains" / domain


def render_feature_doc(text: str, feature_id: str) -> str:
    return text.replace("FEATURE_NAME", feature_id)


def scaffold_feature_docs(target_dir: Path, template_dir: Path, feature_id: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=False)
    for name in FEATURE_DOC_FILES:
        src = template_dir / name
        text = src.read_text(encoding="utf-8")
        (target_dir / name).write_text(render_feature_doc(text, feature_id), encoding="utf-8")


def feature_status_for_index(feature_dir_path: Path) -> str:
    guide = feature_dir_path / "agent-guide.md"
    if not guide.exists():
        return "planned"
    for line in guide.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("status:"):
            return stripped.split(":", 1)[1].strip() or "planned"
    return "planned"


def feature_index_row(feature_id: str, base_path: str, status: str) -> str:
    return (
        f"| {feature_id} | {status} | ./{base_path}/agent-guide.md | ./{base_path}/requirements.md | "
        f"./{base_path}/status.md | ./{base_path}/guardrails.md | ./{base_path}/test-record.md |"
    )


def replace_table(path: Path, headers: list[str], rows: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip() == headers[0]), None)
    if header_index is None:
        raise SystemExit(f"ERROR: Could not find expected table header in {path}")
    end_index = header_index + 1
    while end_index < len(lines) and lines[end_index].startswith("|"):
        end_index += 1
    new_lines = lines[:header_index] + headers + rows + lines[end_index:]
    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def update_small_features_index(target: Path) -> None:
    index_path = target / "noc_docs/features/index.md"
    features_root = target / "noc_docs/features"
    rows = []
    if features_root.is_dir():
        for child in sorted(features_root.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            rows.append(feature_index_row(child.name, child.name, feature_status_for_index(child)))
    if not rows:
        rows = ["| TODO | planned | ./TODO/agent-guide.md | ./TODO/requirements.md | ./TODO/status.md | ./TODO/guardrails.md | ./TODO/test-record.md |"]
    replace_table(
        index_path,
        [
            "| Feature | Status | Entry | Requirements | Current Status | Guardrails | Tests |",
            "|---|---|---|---|---|---|---|",
        ],
        rows,
    )


def update_domain_feature_index(target: Path, domain: str) -> None:
    index_path = domain_dir(target, domain) / "index.md"
    features_root = domain_dir(target, domain) / "features"
    rows = []
    if features_root.is_dir():
        for child in sorted(features_root.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            rows.append(f"| {child.name} | {feature_status_for_index(child)} | ./features/{child.name}/agent-guide.md |")
    if not rows:
        rows = ["| TODO | planned | ./features/TODO/agent-guide.md |"]
    replace_table(
        index_path,
        [
            "| Feature | Status | Entry |",
            "|---|---|---|",
        ],
        rows,
    )


def update_feature_indexes(target: Path, mode: str, domain: str | None = None) -> None:
    if mode == "domain":
        if not domain:
            raise SystemExit("ERROR: domain mode requires --domain")
        update_domain_feature_index(target, domain)
    else:
        update_small_features_index(target)


def write_feature_paths(target: Path, feature_id: str, paths: list[str], domain: str | None = None) -> None:
    feature_map = load_feature_map(target)
    features = feature_map.setdefault("features", {})
    entry = features.setdefault(feature_id, {})
    existing_paths = entry.setdefault("paths", [])
    for path in paths:
        if path not in existing_paths:
            existing_paths.append(path)
    if domain:
        entry["domain"] = domain
    save_feature_map(target, feature_map)


def run_index_if_requested(target: Path, skip_index: bool) -> None:
    if skip_index:
        return
    code = run_script("index-noc-docs.py", [str(target)])
    if code != 0:
        raise SystemExit(code)


def command_feature_create(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    require_noc_docs(target)
    mode = detect_docs_mode(target)
    feature_id = normalize_feature_id(args.feature)
    domain = normalize_feature_id(args.domain, "domain") if args.domain else None
    if mode == "domain" and domain:
        domain_root = domain_dir(target, domain)
        if not domain_root.is_dir():
            raise SystemExit(f"ERROR: domain `{domain}` does not exist at {domain_root}")
    dst = feature_dir(target, mode, feature_id, domain)
    if dst.exists():
        print(f"ERROR: feature `{feature_id}` already exists at {dst}")
        return 1

    scaffold_feature_docs(dst, feature_template_dir(mode), feature_id)
    update_feature_indexes(target, mode, domain)
    if args.path:
        write_feature_paths(target, feature_id, args.path, domain)
    run_index_if_requested(target, args.no_index)

    print(f"Created feature `{feature_id}` at {dst}")
    if args.path:
        print("Mapped paths: " + ", ".join(args.path))
    return 0


def command_feature_ensure(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    code, payload = ensure_feature(target, args.id, args.name, args.alias or [], args.intent)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return code
    status = payload.get("status")
    if status == "created":
        feature = payload["feature"]
        print(f"Created feature `{feature['id']}` at {feature['overview_path']}")
    elif status == "existing":
        feature = payload["feature"]
        print(f"Feature `{feature['id']}` already exists at {feature['overview_path']}")
    elif status == "conflict":
        conflict = payload["conflict"]
        print(f"ERROR: feature name or alias conflicts with `{conflict['id']}`")
    else:
        print(f"ERROR: {payload.get('error', 'feature ensure failed')}")
    return code


def command_feature_update(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    code, payload = update_feature(target, args.id, Path(args.patch_file).resolve())
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return code
    status = payload.get("status")
    if status == "updated":
        print(f"Updated feature `{payload['feature_id']}` at {payload['overview_path']}")
    elif status == "unchanged":
        print(f"Feature `{payload['feature_id']}` unchanged")
    elif status == "conflict":
        print("ERROR: overview changed; reread the document and regenerate the patch")
    else:
        print(f"ERROR: {payload.get('error', status or 'feature update failed')}")
    return code


def rename_structured_feature_titles(feature_path: Path, old_id: str, new_id: str) -> None:
    for name, prefix in FEATURE_TITLE_PREFIXES.items():
        path = feature_path / name
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        target_line = prefix + old_id
        replacement_line = prefix + new_id
        updated = False
        for index, line in enumerate(lines):
            if line == target_line:
                lines[index] = replacement_line
                updated = True
                break
        if updated:
            path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_feature_rename(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    require_noc_docs(target)
    mode = detect_docs_mode(target)
    old_id = normalize_feature_id(args.old_feature)
    new_id = normalize_feature_id(args.new_feature)
    domain = normalize_feature_id(args.domain, "domain") if args.domain else None
    src = feature_dir(target, mode, old_id, domain)
    dst = feature_dir(target, mode, new_id, domain)
    if not src.is_dir():
        print(f"ERROR: feature `{old_id}` does not exist at {src}")
        return 1
    if dst.exists():
        print(f"ERROR: feature `{new_id}` already exists at {dst}")
        return 1

    shutil.move(str(src), str(dst))
    rename_structured_feature_titles(dst, old_id, new_id)

    feature_map = load_feature_map(target)
    features = feature_map.setdefault("features", {})
    if old_id in features:
        entry = features.pop(old_id)
        if domain:
            entry["domain"] = domain
        features[new_id] = entry
        save_feature_map(target, feature_map)

    update_feature_indexes(target, mode, domain)
    run_index_if_requested(target, args.no_index)

    print(f"Renamed feature `{old_id}` to `{new_id}`")
    return 0


def command_feature_adopt(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    require_noc_docs(target)
    mode = detect_docs_mode(target)
    source_name = normalize_feature_id(args.source_feature, "source feature", allow_template_name=True)
    feature_id = normalize_feature_id(args.feature)
    domain = normalize_feature_id(args.domain, "domain") if args.domain else None
    src = feature_dir(target, mode, source_name, domain)
    dst = feature_dir(target, mode, feature_id, domain)
    if not src.is_dir():
        print(f"ERROR: feature template `{source_name}` does not exist at {src}")
        return 1
    if source_name == feature_id:
        print("ERROR: source and destination feature ids must differ")
        return 1
    if dst.exists():
        print(f"ERROR: feature `{feature_id}` already exists at {dst}")
        return 1

    shutil.move(str(src), str(dst))
    rename_structured_feature_titles(dst, "FEATURE_NAME", feature_id)
    rename_structured_feature_titles(dst, source_name, feature_id)

    feature_map = load_feature_map(target)
    features = feature_map.setdefault("features", {})
    entry = features.pop(source_name, {}) if source_name in features else {}
    existing_paths = entry.get("paths", [])
    for path in args.path or []:
        if path not in existing_paths:
            existing_paths.append(path)
    entry["paths"] = existing_paths
    if domain:
        entry["domain"] = domain
    if entry:
        features[feature_id] = entry
        save_feature_map(target, feature_map)

    update_feature_indexes(target, mode, domain)
    run_index_if_requested(target, args.no_index)

    print(f"Adopted feature template `{source_name}` as `{feature_id}`")
    if args.path:
        print("Mapped paths: " + ", ".join(args.path))
    return 0


def command_check(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if args.memory_impact or args.json:
        return command_memory_impact_check(target, args)
    config = load_config(target)
    if config.get("protocol_version") == 2 and config.get("layout") == "simplified":
        files = changed_files(target, args.staged)
        code_files = [f for f in files if not f.startswith("noc_docs/") and is_code_file(f)]
        print(f"Checked {len(code_files)} code change(s); simplified project memory updates are semantic, not mandatory.")
        return 0
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


MEMORY_IMPACT_DOCS = {
    "project": "noc_docs/project.md",
    "guardrails": "noc_docs/guardrails.md",
    "verification": "noc_docs/verification.md",
}
MEMORY_IMPACT_ORDER = ["project", "guardrails", "verification"]


def command_memory_impact_check(target: Path, args: argparse.Namespace) -> int:
    declared = list(dict.fromkeys(args.memory_impact or ["none"]))
    if "none" in declared and len(declared) > 1:
        result = {
            "memory_impact": declared,
            "required_docs": [],
            "updated_docs": [],
            "status": "invalid_memory_impact",
        }
        print_memory_impact_result(result, args.json)
        return 2

    impacts = [impact for impact in MEMORY_IMPACT_ORDER if impact in declared]
    normalized = ["none"] if not impacts else impacts
    files = changed_files(target, args.staged)
    docs_files = sorted(path.replace("\\", "/") for path in files if path.startswith("noc_docs/"))
    config = load_config(target)
    unexpected_updates = False

    if normalized == ["none"]:
        required_docs: list[str] = []
        if config.get("protocol_version") == 2 and config.get("layout") == "simplified":
            updated_docs = sorted(path for path in docs_files if path in MEMORY_IMPACT_DOCS.values())
        else:
            updated_docs = sorted(path for path in docs_files if path.endswith(".md"))
        missing_categories: list[str] = []
        unexpected_updates = bool(updated_docs)
    elif config.get("protocol_version") == 2 and config.get("layout") in {"simplified", "feature-archive"}:
        required_docs = [MEMORY_IMPACT_DOCS[impact] for impact in normalized]
        updated_docs = sorted(path for path in docs_files if path in MEMORY_IMPACT_DOCS.values())
        missing_categories = [impact for impact in normalized if MEMORY_IMPACT_DOCS[impact] not in updated_docs]
        unexpected_updates = any(path not in required_docs for path in updated_docs)
    else:
        required_by_impact = v1_memory_impact_docs(target, files, normalized)
        required_docs = sorted({path for paths in required_by_impact.values() for path in paths})
        updated_docs = sorted(path for path in docs_files if path.endswith(".md"))
        missing_categories = [
            impact
            for impact, candidates in required_by_impact.items()
            if not any(candidate in updated_docs for candidate in candidates)
        ]
        unexpected_updates = any(path not in required_docs for path in updated_docs)

    if missing_categories:
        status = "missing_required_docs"
    elif unexpected_updates:
        status = "unexpected_memory_updates"
    else:
        status = "ok"
    result = {
        "memory_impact": normalized,
        "required_docs": required_docs,
        "updated_docs": updated_docs,
        "status": status,
    }
    print_memory_impact_result(result, args.json)
    if status == "ok":
        return 0
    strictness, _ = resolve_check_strictness(target, args)
    if not args.json:
        annotation = (
            "declared memory impact is missing corresponding project memory: " + ", ".join(missing_categories)
            if missing_categories
            else "project memory changed outside the declared semantic impact"
        )
        emit_github_annotation(
            args,
            annotation,
            "warning" if strictness == "warn" else "error",
        )
    return check_result(strictness)


def v1_memory_impact_docs(target: Path, files: list[str], impacts: list[str]) -> dict[str, list[str]]:
    feature_map = load_feature_map(target)
    code_files = [path for path in files if not path.startswith("noc_docs/") and is_code_file(path)]
    entries = []
    for info in feature_map.get("features", {}).values():
        if any(any(path_matches(changed, pattern) for pattern in info.get("paths", [])) for changed in code_files):
            entries.append(info)
    keys = {
        "project": ["requirements", "status"],
        "guardrails": ["guardrails"],
        "verification": ["tests"],
    }
    result: dict[str, list[str]] = {}
    for impact in impacts:
        candidates = sorted(
            {
                info[key].replace("\\", "/")
                for info in entries
                for key in keys[impact]
                if isinstance(info.get(key), str)
            }
        )
        result[impact] = candidates
    return result


def print_memory_impact_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print("Memory impact: " + ", ".join(result["memory_impact"]))
    if result["status"] == "ok":
        if result["memory_impact"] == ["none"]:
            print("No project memory update required.")
        elif result["updated_docs"]:
            print("Project memory updated: " + ", ".join(result["updated_docs"]))
    elif result["status"] == "missing_required_docs":
        missing = [path for path in result["required_docs"] if path not in result["updated_docs"]]
        print("WARNING: declared long-term memory impact is missing corresponding updates.")
        if missing:
            print("Required: " + ", ".join(missing))
    elif result["status"] == "unexpected_memory_updates":
        print("WARNING: project memory changed outside the declared semantic impact.")
    else:
        print("ERROR: memory impact `none` cannot be combined with long-term impact categories.")


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


def build_feature_work_plan(feature_id: str, info: dict, match: dict | None = None) -> dict:
    read_docs = work_docs(info, ["entry", "requirements", "status", "guardrails", "tests"])
    if not read_docs:
        read_docs = ["noc_docs/docs-map.md", "noc_docs/project-status.md"]

    before_coding = []
    if info.get("requirements"):
        before_coding.append(
            {
                "doc": info["requirements"],
                "action": "Put the agreed requirement or behavior change in this document.",
            }
        )
    else:
        before_coding.append(
            {
                "doc": "requirements.md",
                "action": "Create or update requirements.md with the agreed requirement.",
            }
        )
    if info.get("notes"):
        before_coding.append(
            {
                "doc": info["notes"],
                "action": "Put uncertain discussion or open questions in this document.",
            }
        )

    update_after_code = []
    for key, reason in [
        ("status", "when actual behavior changes"),
        ("tests", "with verification commands and results"),
        ("change_record", "for important changes and reasons"),
        ("guardrails", "if new limits, risks, or compatibility rules appear"),
        ("requirements", "only when intended behavior changes"),
    ]:
        if info.get(key):
            update_after_code.append({"doc": info[key], "reason": reason})
    if not update_after_code:
        update_after_code = [
            {"doc": "status.md", "reason": "when actual behavior changes"},
            {"doc": "test-record.md", "reason": "with verification commands and results"},
            {"doc": "change-record.md", "reason": "for important changes and reasons"},
            {"doc": "guardrails.md", "reason": "if new limits, risks, or compatibility rules appear"},
            {"doc": "requirements.md", "reason": "only when intended behavior changes"},
        ]

    plan = {
        "id": feature_id,
        "read_before_code": read_docs,
        "before_coding": before_coding,
        "update_after_code": update_after_code,
    }
    if match:
        plan.update(
            {
                "matched_by": match.get("matched_by"),
                "matched_path": match.get("matched_path"),
                "matched_pattern": match.get("matched_pattern"),
                "confidence": match.get("confidence", "high"),
            }
        )
    if info.get("domain"):
        plan["domain"] = info["domain"]
    return plan


def build_unresolved_work_plan(match: dict | None = None) -> dict:
    plan = {
        "id": "unresolved",
        "read_before_code": [
            "noc_docs/docs-map.md",
            "noc_docs/project-status.md",
            "noc_docs/.living-docs/feature-map.json",
        ],
        "before_coding": [
            {
                "doc": "noc_docs/features/ or noc_docs/domains/<domain>/features/",
                "action": "Decide the affected feature or create one.",
            },
            {
                "doc": "requirements.md or notes.md",
                "action": "Write the agreed requirement into requirements.md or capture uncertain discussion in notes.md.",
            },
        ],
        "update_after_code": [
            {"doc": "status.md", "reason": "when actual behavior changes"},
            {"doc": "test-record.md", "reason": "with verification commands and results"},
            {"doc": "change-record.md", "reason": "for important changes"},
            {"doc": "guardrails.md", "reason": "if new limits or compatibility rules appear"},
        ],
    }
    if match:
        plan.update(
            {
                "matched_by": match.get("matched_by"),
                "matched_path": match.get("matched_path"),
                "matched_pattern": match.get("matched_pattern"),
                "confidence": match.get("confidence", "low"),
            }
        )
    return plan


def resolve_work_matches(feature_map: dict, feature: str | None, paths: list[str]) -> list[dict]:
    all_features = feature_map.get("features", {})
    matches: dict[str, dict] = {}
    if feature:
        matches[feature] = {
            "id": feature,
            "matched_by": "feature",
            "matched_path": None,
            "matched_pattern": None,
            "confidence": "high" if feature in all_features else "low",
        }
    for changed in paths:
        for feature_id, info in all_features.items():
            for pattern in info.get("paths", []):
                if path_matches(changed, pattern):
                    matches.setdefault(
                        feature_id,
                        {
                            "id": feature_id,
                            "matched_by": "path",
                            "matched_path": changed,
                            "matched_pattern": pattern,
                            "confidence": "high",
                        },
                    )
                    break
    return [matches[key] for key in sorted(matches)]


def build_work_plan(target: Path, feature: str | None, paths: list[str], intent: str | None) -> dict:
    config = load_config(target)
    if config.get("protocol_version") == 2 and config.get("layout") == "feature-archive":
        return feature_archive_work_plan(target, config, paths, intent)
    if config.get("protocol_version") == 2 and config.get("layout") == "simplified":
        memory = ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"]
        return {
            "schema_version": "1.0",
            "protocol_version": 2,
            "layout": "simplified",
            "resolution_status": "project_memory",
            "intent": intent,
            "paths": paths,
            "features": [{
                "id": "project",
                "read_before_code": memory,
                "before_coding": [],
                "update_after_code": [{"doc": "project memory", "reason": "only when future sessions need a new fact"}],
            }],
            "next_actions": [],
            "finish_commands": [],
        }
    feature_map = load_feature_map(target)
    matches = resolve_work_matches(feature_map, feature, paths)
    all_features = feature_map.get("features", {})
    feature_plans = [
        build_feature_work_plan(match["id"], all_features.get(match["id"], {}), match)
        for match in matches
    ]
    resolution_status = "resolved"
    if not feature_plans:
        resolution_status = "unresolved"
        feature_plans = [
            build_unresolved_work_plan(
                {
                    "matched_by": "fallback",
                    "matched_path": paths[0] if paths else None,
                    "matched_pattern": None,
                    "confidence": "low",
                }
            )
        ]
    elif any(match["id"] not in all_features for match in matches):
        resolution_status = "missing_feature"
    next_actions = []
    if resolution_status == "missing_feature":
        missing = next((match["id"] for match in matches if match["id"] not in all_features), "<feature>")
        path_arg = f" --path {paths[0]}" if paths else ""
        next_actions.append(f"Run: noc feature create <project> {missing}{path_arg}")
    elif resolution_status == "unresolved":
        next_actions.extend(
            [
                "Run: noc suggest-map <project> --interactive",
                "Run: noc feature create <project> <feature> --path <code/path>",
            ]
        )
    return {
        "schema_version": "1.0",
        "protocol_version": 1,
        "layout": detect_docs_mode(target),
        "resolution_status": resolution_status,
        "intent": intent,
        "paths": paths,
        "features": feature_plans,
        "next_actions": next_actions,
        "finish_commands": [
            "python scripts/noc.py index <project>",
            "python scripts/noc.py check <project> --staged",
        ],
    }


def print_work_plan(plan: dict) -> None:
    print("NOC work plan")
    print("=============")
    if plan.get("intent"):
        print(f"Intent: {plan['intent']}")
    if plan.get("paths"):
        print("Changed or planned path(s): " + ", ".join(plan["paths"]))
    print()

    for feature in plan["features"]:
        if feature["id"] == "unresolved":
            print("Feature: unresolved")
        else:
            print(f"Feature: {feature['id']}")
            if feature.get("domain"):
                print(f"Domain: {feature['domain']}")

        print("Read before code:")
        for doc in feature["read_before_code"]:
            print(f"- {doc}")

        print("Before coding:")
        for item in feature["before_coding"]:
            if feature["id"] == "unresolved" and item["doc"].startswith("noc_docs/features/"):
                print("- Decide the affected feature or create one under noc_docs/features/ or noc_docs/domains/<domain>/features/.")
            elif feature["id"] == "unresolved" and item["doc"] == "requirements.md or notes.md":
                print("- Write the agreed requirement into requirements.md or capture uncertain discussion in notes.md.")
            else:
                print(f"- {item['action'].replace('this document', item['doc'])}")

        print("Update after code:")
        for item in feature["update_after_code"]:
            print(f"- {item['doc']} {item['reason']}")
        print()

    print("Finish:")
    print("- Run: python scripts/noc.py index <project>")
    print("- Before commit, run: python scripts/noc.py check <project> --staged")


def command_work(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    paths = list(args.path or [])
    if args.changed:
        paths.extend(changed_files(target, staged=False))
    if args.staged:
        paths.extend(changed_files(target, staged=True))
    paths = list(dict.fromkeys(paths))
    plan = build_work_plan(target, args.feature, paths, args.intent)
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print_work_plan(plan)
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
    raw_config = load_config(target)
    if raw_config.get("protocol_version") == 2 and raw_config.get("layout") == "feature-archive":
        config = doctor_json(report, living_docs / "config.json", ["documentation_root", "protocol_version", "layout", "layout_version"])
        report.ok(language_report(config))
        for error in validate_config_schema(config):
            report.error(f"feature-archive config invalid: {error}")
            report.fix("Fix noc_docs/.living-docs/config.json before running feature-archive workflows.")
        for name in ["project.md", "guardrails.md", "verification.md"]:
            if (noc_docs / name).is_file():
                report.ok(f"found noc_docs/{name}")
            else:
                report.error(f"missing noc_docs/{name}")
                report.fix("Restore the missing project-level memory file.")
        features_root = noc_docs / "features"
        if features_root.is_dir():
            report.ok("found noc_docs/features/")
            for feature_dir_path in sorted(features_root.iterdir()):
                if not feature_dir_path.is_dir() or feature_dir_path.name.startswith("."):
                    continue
                overview = feature_dir_path / "overview.md"
                if not overview.is_file():
                    report.error(f"missing {overview.relative_to(target).as_posix()}")
                    report.fix("Create the missing feature overview through the feature-archive workflow.")
                    continue
                errors = validate_overview_frontmatter(parse_simple_frontmatter(overview))
                if errors:
                    report.error(f"{overview.relative_to(target).as_posix()} invalid: {'; '.join(errors)}")
                    report.fix("Fix the feature overview frontmatter.")
                else:
                    report.ok(f"valid {overview.relative_to(target).as_posix()}")
        else:
            report.error("missing noc_docs/features/")
            report.fix("Run explicit migration or initialize a new feature-archive project.")
        report.ok("protocol 2 feature-archive layout is ready")
        doctor_hook(report, root)
        print("Fix suggestions:")
        print("- No action needed." if not report.fixes else "\n".join(f"- {fix}" for fix in report.fixes))
        return 1 if report.errors else 0

    if raw_config.get("protocol_version") == 2 and raw_config.get("layout") == "simplified":
        config = doctor_json(report, living_docs / "config.json", ["documentation_root", "protocol_version", "layout"])
        report.ok(language_report(config))
        doctor_json(report, living_docs / "routing.json", ["protocol_version", "layout", "routes"])
        doctor_json(report, living_docs / "manifest.json", ["protocol_version", "layout", "managed_files", "files"])
        for name in ["project.md", "guardrails.md", "verification.md"]:
            if (noc_docs / name).is_file():
                report.ok(f"found noc_docs/{name}")
            else:
                report.error(f"missing noc_docs/{name}")
                report.fix("Run: noc init <project>")
        report.ok("protocol 2 simplified layout is ready")
        doctor_hook(report, root)
        print("Fix suggestions:")
        print("- No action needed." if not report.fixes else "\n".join(f"- {fix}" for fix in report.fixes))
        return 1 if report.errors else 0

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


def parse_simple_frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith(" "):
            continue
        key, raw = line.split(":", 1)
        value = raw.strip()
        data[key.strip()] = int(value) if value.isdigit() else value
    return data


def language_report(config: dict) -> str:
    language = config.get("language") if isinstance(config.get("language"), str) else "unspecified"
    machine_keys = config.get("machine_keys") if isinstance(config.get("machine_keys"), str) else "unspecified"
    return f"language: {language}; machine_keys: {machine_keys}"


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
    parser = argparse.ArgumentParser(
        description="NOC Living Docs CLI. After initialization, use Codex normally."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"noc-living-docs {cli_version()}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup", help="Install or check the bundled Codex Skill.")
    setup_mode = setup.add_mutually_exclusive_group()
    setup_mode.add_argument("--check", action="store_true", help="Check setup without changing files.")
    setup_mode.add_argument("--repair", action="store_true", help="Repair a damaged NOC-managed Skill.")
    setup.add_argument("--json", action="store_true", help="Print a machine-readable setup result.")
    setup.set_defaults(func=command_setup)

    init = sub.add_parser("init", help="Initialize NOC Living Docs in a project.")
    init.add_argument("target", nargs="?", default=".")
    init.add_argument("--mode", choices=["auto", "small", "domain"], default=None)
    init.add_argument("--agent-file", choices=["AGENTS.md", "CLAUDE.md", "GEMINI.md"], default="AGENTS.md")
    init.add_argument("--force", action="store_true")
    init.add_argument("--no-index", dest="index", action="store_false")
    init.set_defaults(func=command_init)

    index = sub.add_parser("index", help="[Advanced] Build routing indexes.")
    index.add_argument("target", nargs="?", default=".")
    index.set_defaults(func=command_index)

    validate = sub.add_parser("validate", help="[Advanced] Validate repository or target project.")
    validate.add_argument("target_positional", nargs="?")
    validate.add_argument("--target")
    validate.set_defaults(func=command_validate)

    hook = sub.add_parser("hook", help="[Advanced] Install, uninstall, or inspect Git hook.")
    hook.add_argument("action", choices=["install", "uninstall", "status"])
    hook.add_argument("target", nargs="?", default=".")
    hook.set_defaults(func=command_hook)

    check = sub.add_parser("check", help="[Advanced] Check project-memory updates.")
    check.add_argument("target", nargs="?", default=".")
    check.add_argument("--staged", action="store_true")
    check.add_argument("--strictness", choices=["off", "warn", "fail"], help="Override check strictness.")
    check.add_argument("--environment", choices=["manual", "local", "ci"], help="Select strictness environment.")
    check.add_argument("--github-annotations", action="store_true", help="Emit GitHub Actions warning/error annotations.")
    check.add_argument("--warn-only", action="store_true", help="Return success even when docs are missing.")
    check.add_argument(
        "--memory-impact",
        action="append",
        choices=["none", "project", "guardrails", "verification"],
        help="Declare semantic project-memory impact. Repeat for multiple categories.",
    )
    check.add_argument("--json", action="store_true", help="Print a machine-readable memory-impact result.")
    check.set_defaults(func=command_check)

    suggest_map = sub.add_parser("suggest-map", help="[Advanced] Suggest feature path mappings.")
    suggest_map.add_argument("target", nargs="?", default=".")
    suggest_map.add_argument("--write", action="store_true", help="Merge suggestions into feature-map.json without overwriting existing paths.")
    suggest_map.add_argument("--yes", action="store_true", help="Confirm --write without interactive review.")
    suggest_map.add_argument("--interactive", action="store_true", help="Confirm suggestions one by one before writing.")
    suggest_map.set_defaults(func=command_suggest_map)

    work = sub.add_parser("work", help="[Advanced] Print the project-memory workflow.")
    work.add_argument("target", nargs="?", default=".")
    work.add_argument("--feature", help="Affected feature id.")
    work.add_argument("--path", action="append", help="Planned or changed code path. Can be repeated.")
    work.add_argument("--changed", action="store_true", help="Use changed Git paths from the working tree.")
    work.add_argument("--staged", action="store_true", help="Use staged Git paths.")
    work.add_argument("--intent", help="Short description of the agreed requirement or change.")
    work.add_argument("--json", action="store_true", help="Print the work plan as machine-readable JSON.")
    work.set_defaults(func=command_work)

    doctor = sub.add_parser("doctor", help="[Advanced] Check local NOC setup.")
    doctor.add_argument("target", nargs="?", default=".")
    doctor.set_defaults(func=command_doctor)

    feature = sub.add_parser("feature", help="[Advanced] Manage v1 feature documentation.")
    feature_sub = feature.add_subparsers(dest="feature_command", required=True)

    feature_create = feature_sub.add_parser("create", help="Create a real feature directory from the template.")
    feature_create.add_argument("target", help="Project directory containing noc_docs.")
    feature_create.add_argument("feature", help="Feature id and directory name to create.")
    feature_create.add_argument("--domain", help="Domain id when the project uses domain mode.")
    feature_create.add_argument("--path", action="append", help="Code path to map into feature-map.json. Can be repeated.")
    feature_create.add_argument("--no-index", action="store_true", help="Skip running `noc index` after creation.")
    feature_create.set_defaults(func=command_feature_create)

    feature_ensure = feature_sub.add_parser("ensure", help="Ensure a feature-archive overview exists.")
    feature_ensure.add_argument("target", help="Project directory containing noc_docs.")
    feature_ensure.add_argument("--id", required=True, help="Stable ASCII kebab-case feature id.")
    feature_ensure.add_argument("--name", required=True, help="Display name stored in overview frontmatter.")
    feature_ensure.add_argument("--alias", action="append", help="Alias used for candidate routing. Can be repeated.")
    feature_ensure.add_argument("--intent", help="Confirmed user intent to record as the initial requirement.")
    feature_ensure.add_argument("--json", action="store_true", help="Print the result as machine-readable JSON.")
    feature_ensure.set_defaults(func=command_feature_ensure)

    feature_update = feature_sub.add_parser("update", help="Apply a structured feature-archive overview patch.")
    feature_update.add_argument("target", help="Project directory containing noc_docs.")
    feature_update.add_argument("--id", required=True, help="Stable ASCII kebab-case feature id.")
    feature_update.add_argument("--patch-file", required=True, help="JSON patch file produced by an agent workflow.")
    feature_update.add_argument("--json", action="store_true", help="Print the result as machine-readable JSON.")
    feature_update.set_defaults(func=command_feature_update)

    feature_rename = feature_sub.add_parser("rename", help="Rename an existing feature directory and mapping.")
    feature_rename.add_argument("target", help="Project directory containing noc_docs.")
    feature_rename.add_argument("old_feature", help="Existing feature id.")
    feature_rename.add_argument("new_feature", help="New feature id.")
    feature_rename.add_argument("--domain", help="Domain id when the project uses domain mode.")
    feature_rename.add_argument("--no-index", action="store_true", help="Skip running `noc index` after rename.")
    feature_rename.set_defaults(func=command_feature_rename)

    feature_adopt = feature_sub.add_parser("adopt", help="Adopt an existing placeholder directory as a real feature.")
    feature_adopt.add_argument("target", help="Project directory containing noc_docs.")
    feature_adopt.add_argument("source_feature", help="Existing placeholder or template directory name.")
    feature_adopt.add_argument("feature", help="Real feature id to adopt into.")
    feature_adopt.add_argument("--domain", help="Domain id when the project uses domain mode.")
    feature_adopt.add_argument("--path", action="append", help="Code path to map into feature-map.json. Can be repeated.")
    feature_adopt.add_argument("--no-index", action="store_true", help="Skip running `noc index` after adoption.")
    feature_adopt.set_defaults(func=command_feature_adopt)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
