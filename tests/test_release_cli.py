from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import os
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "scripts/release.py"


def run(
    args: list[str],
    cwd: Path = ROOT,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    child_env = {**os.environ, **(env or {})}
    if env is None:
        child_env.pop("GITHUB_REF_TYPE", None)
        child_env.pop("GITHUB_REF_NAME", None)
    result = subprocess.run(
        [sys.executable, str(RELEASE), *args],
        cwd=cwd,
        env=child_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def git(project: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"git failed: {args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


class ReleaseCliTests(unittest.TestCase):
    def test_check_accepts_matching_version_changelog_and_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            git(project, ["config", "user.email", "test@example.com"])
            git(project, ["config", "user.name", "Test User"])
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            git(project, ["add", "."])
            git(project, ["commit", "-m", "release"])
            git(project, ["tag", "v0.4.0"])

            result = run(["--check"], cwd=project)

            self.assertIn("Release check passed for 0.4.0", result.stdout)

    def test_check_rejects_tag_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            git(project, ["config", "user.email", "test@example.com"])
            git(project, ["config", "user.name", "Test User"])
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            git(project, ["add", "."])
            git(project, ["commit", "-m", "release"])
            git(project, ["tag", "v0.5.0"])

            result = run(["--check"], cwd=project, check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("current tag v0.5.0 does not match VERSION 0.4.0", result.stderr)

    def test_check_allows_version_preparation_on_previous_release_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            git(project, ["config", "user.email", "test@example.com"])
            git(project, ["config", "user.name", "Test User"])
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            git(project, ["add", "."])
            git(project, ["commit", "-m", "release"])
            git(project, ["tag", "v0.4.0"])
            (project / "VERSION").write_text("0.5.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.5.0] - 2026-07-13\n", encoding="utf-8")

            result = run(["--check"], cwd=project)

            self.assertIn("Release check passed for 0.5.0", result.stdout)

    def test_check_rejects_todo_placeholders_in_current_changelog_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text(
                "# Changelog\n\n## [0.4.0] - 2026-07-04\n\n- TODO: summarize.\n",
                encoding="utf-8",
            )

            result = run(["--check"], cwd=project, check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("CHANGELOG.md entry for 0.4.0 still contains TODO", result.stderr)

    def test_check_rejects_pyproject_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            (project / "pyproject.toml").write_text('[project]\nversion = "0.4.1"\n', encoding="utf-8")

            result = run(["--check"], cwd=project, check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("pyproject.toml version 0.4.1 does not match VERSION 0.4.0", result.stderr)

    def test_check_rejects_readme_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            (project / "README.md").write_text("Current version: `0.4.1`.\n", encoding="utf-8")

            result = run(["--check"], cwd=project, check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("README.md is missing current version 0.4.0", result.stderr)

    def test_check_rejects_skill_manifest_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")
            manifest = project / ".agents" / "skills" / "project-living-docs" / "noc-skill.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({"name": "project-living-docs", "version": "0.4.1"}),
                encoding="utf-8",
            )

            result = run(["--check"], cwd=project, check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Skill manifest version 0.4.1 does not match VERSION 0.4.0", result.stderr)

    def test_check_rejects_github_ref_tag_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")

            result = run(
                ["--check"],
                cwd=project,
                check=False,
                env={"GITHUB_REF_TYPE": "tag", "GITHUB_REF_NAME": "v0.5.0"},
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("GitHub tag v0.5.0 does not match VERSION 0.4.0", result.stderr)

    def test_bump_patch_updates_version_and_changelog_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text("# Changelog\n\n## [0.4.0] - 2026-07-04\n", encoding="utf-8")

            run(["--bump", "patch", "--date", "2026-07-04"], cwd=project)

            self.assertEqual((project / "VERSION").read_text(encoding="utf-8"), "0.4.1\n")
            changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [0.4.1] - 2026-07-04", changelog)
            self.assertIn("### Added", changelog)

    def test_explicit_version_moves_unreleased_notes_to_version_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "VERSION").write_text("0.4.0\n", encoding="utf-8")
            (project / "CHANGELOG.md").write_text(
                "# Changelog\n\n"
                "## Unreleased\n\n"
                "### Added\n\n"
                "- Added release automation.\n\n"
                "## [0.4.0] - 2026-07-04\n",
                encoding="utf-8",
            )

            run(["--version", "0.5.0", "--date", "2026-07-04"], cwd=project)

            self.assertEqual((project / "VERSION").read_text(encoding="utf-8"), "0.5.0\n")
            changelog = (project / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## Unreleased\n\n", changelog)
            self.assertIn("## [0.5.0] - 2026-07-04\n\n### Added\n\n- Added release automation.", changelog)
            self.assertLess(changelog.index("## Unreleased"), changelog.index("## [0.5.0]"))


if __name__ == "__main__":
    unittest.main()
