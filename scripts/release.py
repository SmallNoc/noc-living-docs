#!/usr/bin/env python3
"""Release helper for NOC Living Docs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare or validate a NOC Living Docs release.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate VERSION, CHANGELOG, and current tag.")
    mode.add_argument("--version", help="Set an explicit release version.")
    mode.add_argument("--bump", choices=["major", "minor", "patch"], help="Bump VERSION.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Release date for changelog entries.")
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_version(root: Path) -> str:
    path = root / "VERSION"
    if not path.exists():
        fail("VERSION is missing")
    version = path.read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        fail(f"VERSION must use MAJOR.MINOR.PATCH, got {version!r}")
    return version


def changelog_entry(root: Path, version: str) -> str | None:
    path = root / "CHANGELOG.md"
    if not path.exists():
        fail("CHANGELOG.md is missing")
    text = path.read_text(encoding="utf-8")
    heading = f"## [{version}]"
    start = text.find(heading)
    if start == -1:
        return None
    next_heading = text.find("\n## [", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def check_pyproject_version(root: Path, version: str) -> None:
    path = root / "pyproject.toml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        fail("pyproject.toml is missing project version")
    if match.group(1) != version:
        fail(f"pyproject.toml version {match.group(1)} does not match VERSION {version}")


def check_readme_version(root: Path, version: str) -> None:
    path = root / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    markers = [
        f"Current version: `{version}`.",
        f"当前版本：`{version}`。",
    ]
    if not any(marker in text for marker in markers):
        fail(f"README.md is missing current version {version}")


def check_skill_manifest_version(root: Path, version: str) -> None:
    path = root / ".agents" / "skills" / "project-living-docs" / "noc-skill.json"
    if not path.exists():
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Skill manifest is not valid JSON: {exc}")
    manifest_version = manifest.get("version")
    if manifest_version != version:
        fail(f"Skill manifest version {manifest_version} does not match VERSION {version}")


def current_exact_tag(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "describe", "--tags", "--exact-match"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def version_has_worktree_changes(root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "--", "VERSION"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 1


def command_check(root: Path) -> None:
    version = read_version(root)
    entry = changelog_entry(root, version)
    if entry is None:
        fail(f"CHANGELOG.md is missing entry for {version}")
    if "TODO" in entry:
        fail(f"CHANGELOG.md entry for {version} still contains TODO")
    check_pyproject_version(root, version)
    check_readme_version(root, version)
    check_skill_manifest_version(root, version)
    tag = current_exact_tag(root)
    if tag and not version_has_worktree_changes(root) and tag != f"v{version}":
        fail(f"current tag {tag} does not match VERSION {version}")
    github_ref_type = os.environ.get("GITHUB_REF_TYPE")
    github_ref_name = os.environ.get("GITHUB_REF_NAME")
    if github_ref_type == "tag" and github_ref_name and github_ref_name != f"v{version}":
        fail(f"GitHub tag {github_ref_name} does not match VERSION {version}")
    print(f"Release check passed for {version}")


def bump_version(version: str, part: str) -> str:
    major, minor, patch = [int(piece) for piece in version.split(".")]
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def unreleased_entry(text: str) -> str | None:
    heading = "## Unreleased"
    start = text.find(heading)
    if start == -1:
        return None
    next_heading = text.find("\n## [", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def unreleased_body(text: str) -> str | None:
    entry = unreleased_entry(text)
    if entry is None:
        return None
    body = entry[len("## Unreleased") :].strip()
    return body or None


def remove_unreleased_body(text: str) -> str:
    entry = unreleased_entry(text)
    if entry is None:
        return text
    return text.replace(entry, "## Unreleased\n\n", 1)


def ensure_changelog_entry(root: Path, version: str, release_date: str) -> None:
    path = root / "CHANGELOG.md"
    if not path.exists():
        path.write_text("# Changelog\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if f"## [{version}]" in text:
        return
    body = unreleased_body(text)
    if body:
        text = remove_unreleased_body(text)
    else:
        body = (
            "### Added\n\n"
            "- TODO: summarize added behavior.\n\n"
            "### Changed\n\n"
            "- TODO: summarize changed behavior."
        )
    entry = f"## [{version}] - {release_date}\n\n{body.strip()}\n\n"
    if "## Unreleased\n\n" in text:
        text = text.replace("## Unreleased\n\n", "## Unreleased\n\n" + entry, 1)
    elif text.startswith("# Changelog\n"):
        entry = "\n" + entry.rstrip() + "\n"
        text = text.replace("# Changelog\n", "# Changelog\n" + entry, 1)
    else:
        text = "# Changelog\n\n" + entry + text
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def command_prepare(root: Path, version: str, release_date: str) -> None:
    if not VERSION_RE.match(version):
        fail(f"version must use MAJOR.MINOR.PATCH, got {version!r}")
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    ensure_changelog_entry(root, version, release_date)
    print(f"Prepared release {version}")


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    if args.check:
        command_check(root)
        return
    version = args.version or bump_version(read_version(root), args.bump)
    command_prepare(root, version, args.date)


if __name__ == "__main__":
    main()
