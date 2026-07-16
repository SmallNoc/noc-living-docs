from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/noc.py"


def run(args: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def project_file_hashes(project: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(project).parts:
            hashes[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


class SimplifiedProjectMemoryTests(unittest.TestCase):
    def ready_home(self, root: Path) -> dict[str, str]:
        env = {"CODEX_HOME": str(root / "Codex Home 中文")}
        run(["setup", "--json"], env=env)
        return env

    def initialized_git_project(self, root: Path) -> tuple[Path, dict[str, str]]:
        project = root / "project"
        project.mkdir()
        env = self.ready_home(root)
        run(["init", str(project)], env=env)
        subprocess.run(["git", "-C", str(project), "init"], check=True, stdout=subprocess.PIPE)
        subprocess.run(["git", "-C", str(project), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(project), "-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-m", "init"],
            check=True,
            stdout=subprocess.PIPE,
        )
        return project, env

    def test_default_init_creates_feature_archive_minimal_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "项目 with spaces"
            project.mkdir()
            env = self.ready_home(root)

            result = run(["init", str(project)], env=env)

            self.assertEqual(result.stdout, "Project memory is ready. Continue using Codex normally.\n")
            files = {
                path.relative_to(project).as_posix()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(
                files,
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
            config = json.loads((project / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["protocol_version"], 2)
            self.assertEqual(config["layout"], "feature-archive")
            self.assertEqual(config["layout_version"], "1.0")
            self.assertTrue((project / "noc_docs/features").is_dir())
            self.assertEqual([], list((project / "noc_docs/features").iterdir()))
            self.assertFalse((project / "noc_docs/domains").exists())

    def test_init_detects_project_files_without_inventing_business_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = self.ready_home(root)
            cases = [
                ("python", "pyproject.toml", "src/app.py", "tests/test_app.py"),
                ("node", "package.json", "src/index.js", "test/index.test.js"),
                ("java", "pom.xml", "src/main/java/App.java", "src/test/java/AppTest.java"),
            ]
            for name, marker, source, test in cases:
                with self.subTest(name=name):
                    project = root / name
                    (project / source).parent.mkdir(parents=True)
                    (project / source).write_text("\n", encoding="utf-8")
                    (project / test).parent.mkdir(parents=True)
                    (project / test).write_text("\n", encoding="utf-8")
                    (project / marker).write_text("{}\n" if marker == "package.json" else "\n", encoding="utf-8")
                    (project / "README.md").write_text(f"# {name.title()} Demo\n", encoding="utf-8")

                    run(["init", str(project)], env=env)
                    text = (project / "noc_docs/project.md").read_text(encoding="utf-8")
                    self.assertIn(marker, text)
                    self.assertIn("待补充", text)
                    self.assertNotIn("billing", text.lower())

    def test_init_preserves_readme_and_user_agents_content_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            env = self.ready_home(root)
            readme = "# User README\n\nKeep me.\n"
            agents = "# User Rules\n\n- Keep this rule.\n"
            (project / "README.md").write_text(readme, encoding="utf-8")
            (project / "AGENTS.md").write_text(agents, encoding="utf-8")

            run(["init", str(project)], env=env)
            first = (project / "AGENTS.md").read_text(encoding="utf-8")
            run(["init", str(project)], env=env)

            self.assertEqual((project / "README.md").read_text(encoding="utf-8"), readme)
            self.assertEqual((project / "AGENTS.md").read_text(encoding="utf-8"), first)
            self.assertIn("- Keep this rule.", first)
            self.assertEqual(first.count("<!-- noc-living-docs:start -->"), 1)

    def test_missing_skill_only_points_to_setup_and_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            env = {"CODEX_HOME": str(root / "empty-codex-home")}

            result = run(["init", str(project)], env=env, check=False)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "noc setup\n")
            self.assertFalse(project.exists())

    def test_v2_validate_doctor_index_work_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            env = self.ready_home(root)
            run(["init", str(project)], env=env)
            subprocess.run(["git", "-C", str(project), "init"], check=True, stdout=subprocess.PIPE)

            run(["validate", "--target", str(project)], env=env)
            run(["index", str(project)], env=env)
            doctor = run(["doctor", str(project)], env=env)
            work = json.loads(run(["work", str(project), "--path", "src/app.py", "--json"], env=env).stdout)

            self.assertIn("protocol_version", work)
            self.assertEqual(work["protocol_version"], 2)
            self.assertEqual(work["layout"], "feature-archive")
            self.assertEqual(
                work["features"][0]["read_before_code"],
                ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"],
            )
            self.assertIn("feature-archive", doctor.stdout)

            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(["git", "-C", str(project), "-c", "user.name=Test", "-c", "user.email=t@example.com", "commit", "-m", "init"], check=True, stdout=subprocess.PIPE)
            (project / "app.py").write_text("print('fix')\n", encoding="utf-8")
            check_result = run(["check", str(project)], env=env)
            self.assertNotIn("WARNING: code changed but no noc_docs files changed", check_result.stdout)

    def test_existing_simplified_work_index_doctor_validate_do_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_git_project(Path(tmp))
            shutil.rmtree(project / "noc_docs/features")
            config_path = project / "noc_docs/.living-docs/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["layout"] = "simplified"
            config.pop("layout_version", None)
            config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            routing_path = project / "noc_docs/.living-docs/routing.json"
            routing_path.write_text(
                json.dumps(
                    {
                        "protocol_version": 2,
                        "layout": "simplified",
                        "routes": [{"path": "**", "memory": ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"]}],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "noc_docs/.living-docs/manifest.json").write_text(
                json.dumps(
                    {
                        "protocol_version": 2,
                        "layout": "simplified",
                        "managed_files": [
                            "noc_docs/project.md",
                            "noc_docs/guardrails.md",
                            "noc_docs/verification.md",
                            "noc_docs/.living-docs/config.json",
                            "noc_docs/.living-docs/routing.json",
                            "noc_docs/.living-docs/manifest.json",
                        ],
                        "files": {},
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            for name in ["feature-index.json", "evidence-index.json"]:
                path = project / "noc_docs/.living-docs" / name
                if path.exists():
                    path.unlink()
            run(["index", str(project)], env=env)
            before = project_file_hashes(project)

            run(["work", str(project), "--path", "src/app.py", "--json"], env=env)
            run(["index", str(project)], env=env)
            run(["doctor", str(project)], env=env)
            run(["validate", "--target", str(project)], env=env)

            self.assertEqual(before, project_file_hashes(project))
            self.assertFalse((project / "noc_docs/features").exists())

    def test_existing_v1_project_is_not_migrated_by_default_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "legacy"
            env = self.ready_home(root)
            run(["init", str(project), "--mode", "small"], env=env)
            legacy = project / "noc_docs/features/_feature/requirements.md"
            before = legacy.read_text(encoding="utf-8")

            run(["init", str(project)], env=env)

            config = json.loads((project / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config.get("protocol_version", 1), 1)
            self.assertTrue(legacy.exists())
            self.assertEqual(legacy.read_text(encoding="utf-8"), before)
            self.assertFalse((project / "noc_docs/project.md").exists())

    def test_explicit_v1_init_remains_available_without_installed_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "legacy"
            env = {"CODEX_HOME": str(root / "empty-codex-home")}

            run(["init", str(project), "--mode", "small"], env=env)

            self.assertTrue((project / "noc_docs/features/_feature/requirements.md").is_file())
            config = json.loads((project / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config.get("protocol_version", 1), 1)

    def test_memory_impact_none_passes_without_docs_update_and_returns_stable_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_git_project(Path(tmp))
            (project / "app.py").write_text("renamed_value = 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "app.py"], check=True)

            result = run(["check", str(project), "--staged", "--memory-impact", "none", "--json"], env=env)
            payload = json.loads(result.stdout)

            self.assertEqual(
                set(payload),
                {"memory_impact", "required_docs", "updated_docs", "status"},
            )
            self.assertEqual(payload["memory_impact"], ["none"])
            self.assertEqual(payload["required_docs"], [])
            self.assertEqual(payload["updated_docs"], [])
            self.assertEqual(payload["status"], "ok")

    def test_declared_long_term_impact_fails_when_required_memory_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_git_project(Path(tmp))
            (project / "app.py").write_text("NEW_CAPABILITY = True\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "app.py"], check=True)

            result = run(
                [
                    "check",
                    str(project),
                    "--staged",
                    "--memory-impact",
                    "project",
                    "--json",
                    "--environment",
                    "ci",
                    "--github-annotations",
                ],
                env=env,
                check=False,
            )
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["required_docs"], ["noc_docs/project.md"])
            self.assertEqual(payload["updated_docs"], [])
            self.assertEqual(payload["status"], "missing_required_docs")

    def test_multiple_memory_impacts_require_and_accept_only_matching_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_git_project(Path(tmp))
            (project / "app.py").write_text("PUBLIC_API = True\n", encoding="utf-8")
            project_doc = project / "noc_docs/project.md"
            project_doc.write_text(project_doc.read_text(encoding="utf-8") + "\n- 新增公开能力。\n", encoding="utf-8")
            verification = project / "noc_docs/verification.md"
            verification.write_text(verification.read_text(encoding="utf-8") + "\n- `python -m unittest`\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)

            result = run(
                [
                    "check",
                    str(project),
                    "--staged",
                    "--memory-impact",
                    "project",
                    "--memory-impact",
                    "verification",
                    "--json",
                    "--environment",
                    "ci",
                ],
                env=env,
            )
            payload = json.loads(result.stdout)

            self.assertEqual(payload["memory_impact"], ["project", "verification"])
            self.assertEqual(payload["required_docs"], ["noc_docs/project.md", "noc_docs/verification.md"])
            self.assertEqual(payload["updated_docs"], ["noc_docs/project.md", "noc_docs/verification.md"])
            self.assertEqual(payload["status"], "ok")

    def test_declared_impact_rejects_unrelated_project_memory_churn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_git_project(Path(tmp))
            (project / "app.py").write_text("NEW_CAPABILITY = True\n", encoding="utf-8")
            project_doc = project / "noc_docs/project.md"
            project_doc.write_text(project_doc.read_text(encoding="utf-8") + "\n- 新能力。\n", encoding="utf-8")
            guardrails = project / "noc_docs/guardrails.md"
            guardrails.write_text(guardrails.read_text(encoding="utf-8") + "\n- 临时记录。\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)

            result = run(
                ["check", str(project), "--staged", "--memory-impact", "project", "--json", "--environment", "ci"],
                env=env,
                check=False,
            )
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["required_docs"], ["noc_docs/project.md"])
            self.assertEqual(payload["updated_docs"], ["noc_docs/guardrails.md", "noc_docs/project.md"])
            self.assertEqual(payload["status"], "unexpected_memory_updates")


if __name__ == "__main__":
    unittest.main()
