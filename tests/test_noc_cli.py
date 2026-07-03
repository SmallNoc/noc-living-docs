from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/noc.py"


def run(args: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd,
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


class NocCliTests(unittest.TestCase):
    def test_hook_install_writes_lf_and_warn_only_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            run(["hook", "install", str(project)])

            hook = project / ".git/hooks/pre-commit"
            data = hook.read_bytes()

            expected_shebang = f"#!{Path(sys.executable).resolve().as_posix()}\n".encode()
            self.assertIn(expected_shebang, data)
            self.assertNotIn(b"\r\n", data)
            self.assertIn(b"--warn-only", data)

    def test_warn_only_hook_does_not_block_code_only_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            git(project, ["config", "user.email", "test@example.com"])
            git(project, ["config", "user.name", "Test User"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init noc docs"])
            run(["hook", "install", str(project)])

            (project / "src").mkdir()
            (project / "src/app.py").write_text('print("hello")\n', encoding="utf-8")
            git(project, ["add", "src/app.py"])
            result = git(project, ["commit", "-m", "feat: add app"], check=False)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_index_preserves_feature_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])

            feature = project / "noc_docs/features/user-login"
            template = project / "noc_docs/features/_feature"
            feature.mkdir(parents=True)
            for file in template.iterdir():
                if file.is_file():
                    (feature / file.name).write_text(file.read_text(encoding="utf-8"), encoding="utf-8")

            feature_map_path = project / "noc_docs/.living-docs/feature-map.json"
            existing = {
                "mode": "small",
                "features": {
                    "user-login": {
                        "paths": ["src/auth/", "src/routes/login.py"],
                        "owner": "auth-team",
                    }
                },
            }
            feature_map_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

            run(["index", str(project)])
            indexed = json.loads(feature_map_path.read_text(encoding="utf-8"))

            entry = indexed["features"]["user-login"]
            self.assertEqual(entry["paths"], ["src/auth/", "src/routes/login.py"])
            self.assertEqual(entry["owner"], "auth-team")
            self.assertEqual(entry["entry"], "noc_docs/features/user-login/agent-guide.md")

    def test_check_treats_yaml_sql_shell_and_dockerfile_as_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
            (project / "schema.sql").write_text("select 1;\n", encoding="utf-8")
            (project / "script.sh").write_text("#!/bin/sh\ntrue\n", encoding="utf-8")
            (project / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("code changed but no noc_docs files changed", result.stdout)

    def test_check_rejects_unrelated_docs_for_mapped_feature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])

            feature = project / "noc_docs/features/user-login"
            template = project / "noc_docs/features/_feature"
            feature.mkdir(parents=True)
            for file in template.iterdir():
                if file.is_file():
                    (feature / file.name).write_text(file.read_text(encoding="utf-8"), encoding="utf-8")

            feature_map_path = project / "noc_docs/.living-docs/feature-map.json"
            feature_map_path.write_text(
                json.dumps(
                    {
                        "mode": "small",
                        "features": {
                            "user-login": {
                                "paths": ["src/auth/"],
                                "entry": "noc_docs/features/user-login/agent-guide.md",
                                "status": "noc_docs/features/user-login/status.md",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")
            (project / "noc_docs/project-status.md").write_text("# Project Status\n\nUnrelated.\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("docs changed, but not for affected feature(s)", result.stdout)
            self.assertIn("user-login", result.stdout)

    def test_check_accepts_docs_for_mapped_feature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])

            feature = project / "noc_docs/features/user-login"
            template = project / "noc_docs/features/_feature"
            feature.mkdir(parents=True)
            for file in template.iterdir():
                if file.is_file():
                    (feature / file.name).write_text(file.read_text(encoding="utf-8"), encoding="utf-8")

            feature_map_path = project / "noc_docs/.living-docs/feature-map.json"
            feature_map_path.write_text(
                json.dumps(
                    {
                        "mode": "small",
                        "features": {
                            "user-login": {
                                "paths": ["src/auth/"],
                                "entry": "noc_docs/features/user-login/agent-guide.md",
                                "status": "noc_docs/features/user-login/status.md",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")
            (feature / "status.md").write_text("# Status\n\nUpdated behavior.\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 0)
            self.assertIn("NOC docs changed for affected feature(s): user-login", result.stdout)

    def test_index_adds_freshness_and_completeness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])

            feature = project / "noc_docs/features/user-login"
            feature.mkdir(parents=True)
            (feature / "agent-guide.md").write_text("# Agent Guide\n", encoding="utf-8")
            (feature / "status.md").write_text("# Status\n", encoding="utf-8")

            run(["index", str(project)])
            feature_map = json.loads((project / "noc_docs/.living-docs/feature-map.json").read_text(encoding="utf-8"))
            entry = feature_map["features"]["user-login"]

            self.assertIn("freshness", entry)
            self.assertIn("last_doc_update", entry["freshness"])
            self.assertIn("completeness", entry)
            self.assertIn("missing_docs", entry["completeness"])
            self.assertIn("requirements.md", entry["completeness"]["missing_docs"])


if __name__ == "__main__":
    unittest.main()
