from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from hashlib import sha256
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest import mock

from scripts import noc


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/noc.py"


def run_setup(codex_home: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CODEX_HOME": str(codex_home)}
    result = subprocess.run(
        [sys.executable, str(CLI), "setup", *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"setup failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


class SetupCliTests(unittest.TestCase):
    def test_source_checkout_version_wins_over_an_unrelated_installed_distribution(self) -> None:
        with mock.patch("scripts.noc.importlib.metadata.version", return_value="9.9.9"):
            self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), noc.cli_version())

    def test_setup_installs_skill_into_fresh_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "Codex Home"

            result = run_setup(codex_home)

            skill = codex_home / "skills/project-living-docs"
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "references/workflow.md").is_file())
            self.assertTrue((skill / "noc-skill.json").is_file())
            for relative in [
                "SKILL.md",
                "references/workflow.md",
                "references/feature-doc-template.md",
                "references/domain-mode-guide.md",
                "references/codex-prompts.md",
                "evals/project-living-docs.prompts.csv",
            ]:
                self.assertEqual(
                    (ROOT / ".agents/skills/project-living-docs" / relative).read_text(encoding="utf-8").replace("\r\n", "\n"),
                    (skill / relative).read_text(encoding="utf-8").replace("\r\n", "\n"),
                )
            self.assertFalse((codex_home / ".git/hooks/pre-commit").exists())
            self.assertIn("NOC is ready for Codex", result.stdout)
            self.assertIn("noc init .", result.stdout)

    def test_setup_reinstalls_a_missing_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            skill = codex_home / "skills/project-living-docs"
            for path in sorted(skill.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                else:
                    path.rmdir()
            skill.rmdir()

            run_setup(codex_home)

            self.assertTrue((skill / "SKILL.md").is_file())

    def test_repeated_setup_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            skill_file = codex_home / "skills/project-living-docs/SKILL.md"
            before = skill_file.stat().st_mtime_ns

            result = run_setup(codex_home)

            self.assertEqual(before, skill_file.stat().st_mtime_ns)
            self.assertIn("already up to date", result.stdout.lower())

    def test_setup_check_is_read_only_and_reports_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "missing"

            result = run_setup(codex_home, "--check", check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertFalse(codex_home.exists())
            self.assertIn("noc setup", result.stdout)

    def test_setup_check_json_error_is_valid_and_has_stable_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "missing"

            result = run_setup(codex_home, "--check", "--json", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(1, result.returncode)
            self.assertEqual(
                {
                    "schema_version",
                    "codex_home",
                    "skill_path",
                    "cli_version",
                    "skill_version",
                    "status",
                    "action",
                    "next_action",
                    "error_code",
                },
                set(payload),
            )
            self.assertEqual("missing", payload["status"])
            self.assertEqual("SKILL_NOT_INSTALLED", payload["error_code"])
            self.assertFalse(codex_home.exists())

    def test_setup_check_passes_after_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)

            result = run_setup(codex_home, "--check")

            self.assertIn("matches CLI version", result.stdout)

    def test_setup_check_does_not_modify_a_damaged_managed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            skill = codex_home / "skills/project-living-docs"
            (skill / "SKILL.md").write_text("damaged\n", encoding="utf-8")
            before = {
                path.relative_to(skill).as_posix(): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
                for path in skill.rglob("*")
                if path.is_file()
            }

            result = run_setup(codex_home, "--check", check=False)
            after = {
                path.relative_to(skill).as_posix(): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
                for path in skill.rglob("*")
                if path.is_file()
            }

            self.assertEqual(1, result.returncode)
            self.assertEqual(before, after)
            self.assertIn("noc setup --repair", result.stdout)

    def test_setup_repair_restores_damaged_managed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            skill_file = codex_home / "skills/project-living-docs/SKILL.md"
            expected = skill_file.read_text(encoding="utf-8")
            skill_file.write_text("damaged\n", encoding="utf-8")

            result = run_setup(codex_home, "--repair")

            self.assertEqual(expected, skill_file.read_text(encoding="utf-8"))
            self.assertIn("Repaired", result.stdout)

    def test_setup_upgrades_an_old_noc_managed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            manifest_path = codex_home / "skills/project-living-docs/noc-skill.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.9.0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = run_setup(codex_home)

            installed = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(noc.cli_version(), installed["version"])
            self.assertIn("Upgraded", result.stdout)

    def test_setup_upgrade_removes_files_deleted_from_new_skill_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            run_setup(codex_home)
            skill = codex_home / "skills/project-living-docs"
            obsolete = skill / "references/removed-in-new-version.md"
            obsolete.write_text("obsolete\n", encoding="utf-8")
            manifest_path = skill / "noc-skill.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "0.9.0"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            run_setup(codex_home)

            self.assertFalse(obsolete.exists())

    def test_setup_rejects_forged_or_incomplete_managed_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            skill = codex_home / "skills/project-living-docs"
            skill.mkdir(parents=True)
            skill_file = skill / "SKILL.md"
            skill_file.write_text("user maintained\n", encoding="utf-8")
            (skill / "noc-skill.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "name": "some-other-skill",
                        "version": noc.cli_version(),
                        "managed_by": "noc-living-docs",
                        "required_files": ["SKILL.md", "noc-skill.json"],
                    }
                ),
                encoding="utf-8",
            )

            result = run_setup(codex_home, "--repair", "--json", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(2, result.returncode)
            self.assertEqual("unmanaged", payload["status"])
            self.assertEqual("SKILL_NOT_MANAGED", payload["error_code"])
            self.assertEqual("user maintained\n", skill_file.read_text(encoding="utf-8"))

    def test_setup_refuses_to_overwrite_user_managed_same_name_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            skill = codex_home / "skills/project-living-docs"
            skill.mkdir(parents=True)
            skill_file = skill / "SKILL.md"
            skill_file.write_text("user maintained\n", encoding="utf-8")

            result = run_setup(codex_home, check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertEqual("user maintained\n", skill_file.read_text(encoding="utf-8"))
            self.assertIn("will not overwrite", result.stdout)

    def test_setup_does_not_delete_an_unrelated_backup_named_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            backup = codex_home / "skills/.project-living-docs.backup"
            backup.mkdir(parents=True)
            sentinel = backup / "user-file.txt"
            sentinel.write_text("keep me\n", encoding="utf-8")

            result = run_setup(codex_home, "--json", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(1, result.returncode)
            self.assertEqual("INSTALL_PATH_CONFLICT", payload["error_code"])
            self.assertEqual("keep me\n", sentinel.read_text(encoding="utf-8"))

    def test_setup_json_reports_copy_failure_and_removes_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp)
            output = io.StringIO()
            args = SimpleNamespace(check=False, repair=False, json=True)

            with mock.patch("scripts.noc.codex_home", return_value=codex_home), mock.patch(
                "scripts.noc.shutil.copytree", side_effect=OSError("copy failed")
            ), redirect_stdout(output):
                code = noc.command_setup(args)

            payload = json.loads(output.getvalue())
            self.assertEqual(1, code)
            self.assertEqual("install_error", payload["status"])
            self.assertEqual("SETUP_IO_ERROR", payload["error_code"])
            self.assertEqual([], list((codex_home / "skills").glob(".project-living-docs.*")))

    def test_setup_json_reports_custom_codex_home_and_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "custom-codex"

            result = run_setup(codex_home, "--json")
            payload = json.loads(result.stdout)

            self.assertEqual(str(codex_home.resolve()), payload["codex_home"])
            self.assertEqual(noc.cli_version(), payload["cli_version"])
            self.assertEqual(noc.cli_version(), payload["skill_version"])
            self.assertEqual("ready", payload["status"])
            self.assertEqual("noc init .", payload["next_action"])
            self.assertIsNone(payload["error_code"])

    def test_setup_handles_unicode_and_spaces_in_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "中文 Codex Home"

            result = run_setup(codex_home, "--json")
            payload = json.loads(result.stdout)

            self.assertEqual(str(codex_home.resolve()), payload["codex_home"])
            self.assertTrue((codex_home / "skills/project-living-docs/SKILL.md").is_file())

    def test_default_codex_home_handles_windows_and_posix_home_paths(self) -> None:
        self.assertEqual(
            PureWindowsPath("C:/Users/Alice/.codex"),
            noc.default_codex_home(PureWindowsPath("C:/Users/Alice")),
        )
        self.assertEqual(
            PurePosixPath("/Users/alice/.codex"),
            noc.default_codex_home(PurePosixPath("/Users/alice")),
        )

    def test_formal_skill_and_user_entry_use_installed_noc_command(self) -> None:
        paths = [
            ROOT / ".agents/skills/project-living-docs/SKILL.md",
            ROOT / ".agents/skills/project-living-docs/references/workflow.md",
            ROOT / "skills/codex/project-living-docs/SKILL.md",
            ROOT / "skills/codex/project-living-docs/references/workflow.md",
            ROOT / "templates/AGENTS.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn("python scripts/noc.py", path.read_text(encoding="utf-8"))

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("pipx install noc-living-docs\nnoc setup", readme)
        self.assertIn("python -m pip install noc-living-docs\nnoc setup", readme)
        self.assertIn("`noc setup` installs the bundled", readme)
        self.assertIn("`noc setup`, available since 1.1.0", readme)

    def test_standard_and_legacy_skill_runtime_content_stays_in_sync(self) -> None:
        standard = ROOT / ".agents/skills/project-living-docs"
        legacy = ROOT / "skills/codex/project-living-docs"
        runtime_files = ["SKILL.md", *[p.relative_to(standard).as_posix() for p in (standard / "references").rglob("*") if p.is_file()], *[p.relative_to(standard).as_posix() for p in (standard / "evals").rglob("*") if p.is_file()]]

        for relative in runtime_files:
            with self.subTest(relative=relative):
                self.assertEqual(
                    (standard / relative).read_text(encoding="utf-8").replace("\r\n", "\n"),
                    (legacy / relative).read_text(encoding="utf-8").replace("\r\n", "\n"),
                )

    def test_built_wheel_contains_skill_manifest_and_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(out_dir)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            wheel = next(out_dir.glob("*.whl"))
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())

            expected = {
                "noc_assets/project_living_docs/SKILL.md",
                "noc_assets/project_living_docs/noc-skill.json",
                "noc_assets/project_living_docs/references/workflow.md",
                "noc_assets/project_living_docs/references/feature-doc-template.md",
                "noc_assets/project_living_docs/references/domain-mode-guide.md",
                "noc_assets/project_living_docs/references/codex-prompts.md",
            }
            self.assertTrue(expected.issubset(names), expected - names)

            venv_dir = out_dir / "isolated-venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            venv_noc = venv_dir / ("Scripts/noc.exe" if os.name == "nt" else "bin/noc")
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
                cwd=out_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            codex_home = out_dir / "中文 Codex Home"
            env = {**os.environ, "CODEX_HOME": str(codex_home)}
            env.pop("PYTHONPATH", None)

            version = subprocess.run(
                [str(venv_noc), "--version"],
                cwd=out_dir,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("noc-living-docs 1.2.1\n", version.stdout)

            installed = subprocess.run(
                [str(venv_noc), "setup", "--json"],
                cwd=out_dir,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("ready", json.loads(installed.stdout)["status"])

            checked = subprocess.run(
                [str(venv_noc), "setup", "--check", "--json"],
                cwd=out_dir,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("none", json.loads(checked.stdout)["action"])

            skill_file = codex_home / "skills/project-living-docs/SKILL.md"
            skill_file.write_text("damaged\n", encoding="utf-8")
            repaired = subprocess.run(
                [str(venv_noc), "setup", "--repair", "--json"],
                cwd=out_dir,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("repaired", json.loads(repaired.stdout)["action"])
            self.assertNotEqual("damaged\n", skill_file.read_text(encoding="utf-8"))

            project = out_dir / "中文 Project with spaces"
            project.mkdir()
            initialized = subprocess.run(
                [str(venv_noc), "init", "."],
                cwd=project,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            repeated = subprocess.run(
                [str(venv_noc), "init", "."],
                cwd=project,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            ready_message = "Project memory is ready. Continue using Codex normally.\n"
            self.assertEqual(ready_message, initialized.stdout)
            self.assertEqual(ready_message, repeated.stdout)
            generated = {
                path.relative_to(project).as_posix()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(
                generated,
                {
                    "AGENTS.md",
                    "noc_docs/project.md",
                    "noc_docs/guardrails.md",
                    "noc_docs/verification.md",
                    "noc_docs/.living-docs/config.json",
                    "noc_docs/.living-docs/routing.json",
                    "noc_docs/.living-docs/manifest.json",
                    "noc_docs/.living-docs/feature-index.json",
                    "noc_docs/.living-docs/evidence-index.json",
                },
            )

            subprocess.run(["git", "-C", str(project), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(project), "-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-m", "init"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (project / "app.py").write_text("bug_fixed = True\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "app.py"], check=True)
            no_impact = subprocess.run(
                [str(venv_noc), "check", ".", "--staged", "--memory-impact", "none", "--json"],
                cwd=project,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("ok", json.loads(no_impact.stdout)["status"])

            project_doc = project / "noc_docs/project.md"
            project_doc.write_text(project_doc.read_text(encoding="utf-8") + "\n- Durable capability.\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "noc_docs/project.md"], check=True)
            durable = subprocess.run(
                [str(venv_noc), "check", ".", "--staged", "--memory-impact", "project", "--json"],
                cwd=project,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("ok", json.loads(durable.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
