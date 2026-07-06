from __future__ import annotations

import json
import csv
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
    def test_cli_help_lists_required_subcommands(self) -> None:
        result = run(["--help"])

        for command in ["init", "index", "validate", "hook", "check", "suggest-map", "work"]:
            self.assertIn(command, result.stdout)

    def test_each_required_subcommand_has_help(self) -> None:
        for command in ["init", "index", "validate", "hook", "check", "suggest-map", "work"]:
            with self.subTest(command=command):
                result = run([command, "--help"])
                self.assertIn("usage:", result.stdout)

    def test_codex_skill_frontmatter_contains_name_and_description(self) -> None:
        skill = (ROOT / "skills/codex/project-living-docs/SKILL.md").read_text(encoding="utf-8")

        self.assertTrue(skill.startswith("---\n"))
        self.assertIn("name: project-living-docs", skill)
        self.assertIn("description: Use when", skill)

    def test_codex_skill_references_and_evals_exist(self) -> None:
        skill_root = ROOT / "skills/codex/project-living-docs"
        for path in [
            "references/workflow.md",
            "references/feature-doc-template.md",
            "references/domain-mode-guide.md",
            "references/codex-prompts.md",
            "evals/project-living-docs.prompts.csv",
        ]:
            self.assertTrue((skill_root / path).exists(), path)

        evals = list(csv.DictReader((skill_root / "evals/project-living-docs.prompts.csv").read_text(encoding="utf-8").splitlines()))
        self.assertGreaterEqual(len(evals), 15)
        self.assertIn("true", {row["should_trigger"] for row in evals})
        self.assertIn("false", {row["should_trigger"] for row in evals})

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

    def test_check_treats_java_go_as_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "src").mkdir()
            (project / "src/Main.java").write_text("class Main {}\n", encoding="utf-8")
            (project / "src/main.go").write_text("package main\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("code changed but no noc_docs files changed", result.stdout)

    def test_check_treats_python_js_and_ts_as_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "src").mkdir()
            (project / "src/app.py").write_text("print('hello')\n", encoding="utf-8")
            (project / "src/app.js").write_text("console.log('hello')\n", encoding="utf-8")
            (project / "src/app.ts").write_text("console.log('hello')\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("code changed but no noc_docs files changed", result.stdout)

    def test_check_treats_tcl_and_skill_as_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "src").mkdir()
            (project / "src/flow.tcl").write_text("puts hello\n", encoding="utf-8")
            (project / "src/layout.skill").write_text("; SKILL script\n", encoding="utf-8")
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

    def test_migration_preserves_existing_agent_rules_and_existing_docs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "AGENTS.md").write_text("# Existing Rules\n\n- Keep this rule.\n", encoding="utf-8")
            (project / "docs").mkdir()
            (project / "docs/README.md").write_text("# Existing Docs\n", encoding="utf-8")

            run(["init", str(project), "--mode", "small"])
            run(["validate", "--target", str(project)])

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("- Keep this rule.", agents)
            self.assertIn("<!-- noc-living-docs:start -->", agents)
            self.assertTrue((project / "docs/README.md").exists())
            self.assertTrue((project / "noc_docs/features").exists())

    def test_migration_auto_selects_domain_mode_for_monorepo_services(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "pnpm-workspace.yaml").write_text("packages:\n  - services/*\n", encoding="utf-8")
            for name in ["auth", "billing", "reporting"]:
                (project / "services" / name).mkdir(parents=True)

            run(["init", str(project), "--mode", "auto"])
            run(["validate", "--target", str(project)])

            config = json.loads((project / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["mode"], "domain")
            self.assertTrue((project / "noc_docs/domains").exists())
            self.assertFalse((project / "noc_docs/features").exists())

    def test_migration_auto_selects_domain_mode_for_top_level_project_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for name in ["edm-console", "edm-server", "edm-ui"]:
                child = project / name
                child.mkdir()
                if name == "edm-ui":
                    (child / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
                else:
                    (child / "pom.xml").write_text("<project></project>\n", encoding="utf-8")

            run(["init", str(project), "--mode", "auto"])
            run(["validate", "--target", str(project)])

            config = json.loads((project / "noc_docs/.living-docs/config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["mode"], "domain")
            self.assertTrue((project / "noc_docs/domains").exists())
            self.assertFalse((project / "noc_docs/features").exists())

    def test_migration_config_heavy_project_triggers_docs_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            (project / "migrations").mkdir()
            (project / "migrations/001.sql").write_text("select 1;\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("code changed but no noc_docs files changed", result.stdout)

    def test_check_outputs_lightweight_change_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            git(project, ["init"])
            run(["init", str(project), "--mode", "small"])
            git(project, ["add", "."])
            git(project, ["commit", "-m", "init"], check=False)

            (project / "migrations").mkdir()
            (project / "migrations/001.sql").write_text("alter table users add column name text;\n", encoding="utf-8")
            (project / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
            git(project, ["add", "."])

            result = run(["check", str(project), "--staged"], check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Detected change type(s): deployment, schema", result.stdout)
            self.assertIn("Suggested docs: status.md, test-record.md, development/testing.md", result.stdout)

    def test_suggest_map_outputs_candidate_feature_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])
            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")
            (project / "services/billing").mkdir(parents=True)
            (project / "services/billing/app.go").write_text("package billing\n", encoding="utf-8")

            result = run(["suggest-map", str(project)])

            self.assertIn("auth", result.stdout)
            self.assertIn("src/auth/", result.stdout)
            self.assertIn("billing", result.stdout)
            self.assertIn("services/billing/", result.stdout)

    def test_suggest_map_uses_java_package_branches_for_maven_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])
            for name in ["api", "application", "domain", "infrastructure"]:
                package_dir = project / "src/main/java/com/noc/code" / name
                package_dir.mkdir(parents=True)
                (package_dir / "Marker.java").write_text(f"package com.noc.code.{name};\n", encoding="utf-8")
            test_dir = project / "src/test/java/com/noc/code"
            test_dir.mkdir(parents=True)
            (test_dir / "MarkerTests.java").write_text("package com.noc.code;\n", encoding="utf-8")

            result = run(["suggest-map", str(project)])
            suggestions = json.loads(result.stdout)["suggestions"]
            features = {suggestion["feature"] for suggestion in suggestions}
            paths = {suggestion["path"] for suggestion in suggestions}

            self.assertIn("api", features)
            self.assertIn("domain", features)
            self.assertIn("src/main/java/com/noc/code/api/", paths)
            self.assertNotIn("main", features)
            self.assertNotIn("test", features)
            self.assertNotIn("src/test/", paths)

    def test_suggest_map_outputs_top_level_project_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "domain"])
            for name in ["edm-console", "edm-server", "edm-ui"]:
                child = project / name
                child.mkdir()
                marker = "package.json" if name == "edm-ui" else "pom.xml"
                (child / marker).write_text("{}\n", encoding="utf-8")

            result = run(["suggest-map", str(project)])
            suggestions = json.loads(result.stdout)["suggestions"]
            paths = {suggestion["path"] for suggestion in suggestions}

            self.assertIn("edm-console/", paths)
            self.assertIn("edm-server/", paths)
            self.assertIn("edm-ui/", paths)

    def test_suggest_map_write_merges_without_overwriting_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])
            feature_map_path = project / "noc_docs/.living-docs/feature-map.json"
            feature_map_path.write_text(
                json.dumps(
                    {
                        "mode": "small",
                        "features": {
                            "auth": {
                                "paths": ["legacy/auth/"],
                                "owner": "auth-team",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")

            result = run(["suggest-map", str(project), "--write"])

            self.assertIn("Updated feature-map.json with 1 suggestion(s).", result.stdout)
            feature_map = json.loads(feature_map_path.read_text(encoding="utf-8"))
            entry = feature_map["features"]["auth"]
            self.assertEqual(entry["owner"], "auth-team")
            self.assertEqual(entry["paths"], ["legacy/auth/", "src/auth/"])

    def test_work_outputs_docs_plan_for_named_feature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])

            feature = project / "noc_docs/features/user-login"
            template = project / "noc_docs/features/_feature"
            feature.mkdir(parents=True)
            for file in template.iterdir():
                if file.is_file():
                    (feature / file.name).write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
            run(["index", str(project)])

            result = run(["work", str(project), "--feature", "user-login", "--intent", "lock account after failed login"])

            self.assertIn("NOC work plan", result.stdout)
            self.assertIn("Intent: lock account after failed login", result.stdout)
            self.assertIn("Feature: user-login", result.stdout)
            self.assertIn("noc_docs/features/user-login/requirements.md", result.stdout)
            self.assertIn("Put the agreed requirement", result.stdout)
            self.assertIn("noc_docs/features/user-login/change-record.md", result.stdout)
            self.assertIn("python scripts/noc.py check <project> --staged", result.stdout)

    def test_work_resolves_feature_from_path_mapping(self) -> None:
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
            feature_map_path.write_text(
                json.dumps(
                    {
                        "mode": "small",
                        "features": {
                            "user-login": {
                                "paths": ["src/auth/"],
                                "entry": "noc_docs/features/user-login/agent-guide.md",
                                "requirements": "noc_docs/features/user-login/requirements.md",
                                "status": "noc_docs/features/user-login/status.md",
                                "guardrails": "noc_docs/features/user-login/guardrails.md",
                                "tests": "noc_docs/features/user-login/test-record.md",
                                "change_record": "noc_docs/features/user-login/change-record.md",
                                "notes": "noc_docs/features/user-login/notes.md",
                            }
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = run(["work", str(project), "--path", "src/auth/login.py"])

            self.assertIn("Changed or planned path(s): src/auth/login.py", result.stdout)
            self.assertIn("Feature: user-login", result.stdout)
            self.assertIn("noc_docs/features/user-login/status.md when actual behavior changes", result.stdout)

    def test_work_does_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run(["init", str(project), "--mode", "small"])
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }

            run(["work", str(project), "--feature", "new-feature", "--intent", "new behavior"])

            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
