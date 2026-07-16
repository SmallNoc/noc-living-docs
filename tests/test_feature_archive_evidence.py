from __future__ import annotations

import hashlib
import json
import os
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


def ready_project(root: Path) -> tuple[Path, dict[str, str]]:
    env = {"CODEX_HOME": str(root / "Codex Home 中文")}
    run(["setup", "--json"], env=env)
    project = root / "project"
    project.mkdir()
    run(["init", str(project)], env=env)
    run(["feature", "ensure", str(project), "--id", "user-login", "--name", "用户登录", "--json"], env=env)
    subprocess.run(["git", "-C", str(project), "init"], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(project), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(["git", "-C", str(project), "commit", "-m", "init"], check=True, stdout=subprocess.PIPE)
    return project, env


def file_hashes(project: Path) -> dict[str, str]:
    result = {}
    for path in sorted(project.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(project).parts:
            result[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def evidence_payload(**overrides: object) -> dict:
    payload = {
        "schema_version": "1.0",
        "feature_id": "user-login",
        "command": "python -m pytest tests/auth/test_login.py",
        "cwd": ".",
        "started_at": "2026-07-16T10:00:00+08:00",
        "finished_at": "2026-07-16T10:00:12+08:00",
        "exit_code": 0,
        "result": "passed",
        "scope": "用户登录失败锁定",
        "output_summary": "3 passed",
        "source": {"actor": "codex-skill"},
    }
    payload.update(overrides)
    return payload


class FeatureArchiveEvidenceTests(unittest.TestCase):
    def test_collect_staged_git_evidence_is_read_only_and_reports_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            (project / "src/api").mkdir(parents=True)
            (project / "src/api/routes.py").write_text("def route():\n    return 'old'\n", encoding="utf-8")
            (project / "docs").mkdir()
            (project / "docs/guide.md").write_text("old docs\n", encoding="utf-8")
            (project / "src/old_name.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-m", "baseline files"], check=True, stdout=subprocess.PIPE)

            (project / "src/api/routes.py").write_text("def route():\n    return 'new'\n", encoding="utf-8")
            (project / "docs/guide.md").unlink()
            subprocess.run(["git", "-C", str(project), "mv", "src/old_name.py", "src/new_name.py"], check=True)
            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")
            (project / "tests/auth").mkdir(parents=True)
            (project / "tests/auth/test_login.py").write_text("def test_login(): pass\n", encoding="utf-8")
            (project / "config.yaml").write_text("debug: false\n", encoding="utf-8")
            (project / "数据库迁移.sql").write_text("select 1;\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            before = file_hashes(project)

            payload = json.loads(run(["evidence", str(project), "--staged", "--json"], env=env).stdout)

            self.assertTrue(payload["git_available"])
            self.assertEqual("staged", payload["mode"])
            self.assertEqual("1.0", payload["schema_version"])
            paths = {item["path"]: item["change_type"] for item in payload["changed_paths"]}
            self.assertEqual("added", paths["src/auth/login.py"])
            self.assertEqual("modified", paths["src/api/routes.py"])
            self.assertEqual("deleted", paths["docs/guide.md"])
            self.assertEqual("renamed", paths["src/new_name.py"])
            self.assertEqual("added", paths["tests/auth/test_login.py"])
            self.assertEqual("added", paths["数据库迁移.sql"])
            self.assertGreaterEqual(payload["diff_summary"]["files_changed"], 7)
            signal_types = {signal["type"] for signal in payload["signals"]}
            self.assertTrue({"test_change", "security_change", "config_change", "database_change", "api_change", "documentation_change"} <= signal_types)
            self.assertNotIn("passed", json.dumps(payload))
            self.assertEqual(before, file_hashes(project))

    def test_collect_handles_non_git_and_git_unavailable_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "nogit"
            project.mkdir()
            non_git = json.loads(run(["evidence", str(project), "--staged", "--json"]).stdout)
            self.assertFalse(non_git["git_available"])
            self.assertIn("not_git_repository", non_git["warnings"])

            env = {"PATH": ""}
            unavailable = subprocess.run(
                [sys.executable, str(CLI), "evidence", str(project), "--staged", "--json"],
                cwd=ROOT,
                env={**os.environ, **env},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            payload = json.loads(unavailable.stdout)
            self.assertFalse(payload["git_available"])
            self.assertIn("git_unavailable", payload["warnings"])

    def test_record_verification_evidence_redacts_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            evidence_file = write_json(
                root / "evidence.json",
                evidence_payload(
                    command="TOKEN=abc123 python -m pytest tests/auth/test_login.py",
                    output_summary="Authorization: Bearer very.secret.jwt token=abc123 password=hunter2 " + ("x" * 700),
                ),
            )

            first = json.loads(run(["evidence", "record", str(project), "--feature-id", "user-login", "--file", str(evidence_file), "--json"], env=env).stdout)
            second = json.loads(run(["evidence", "record", str(project), "--feature-id", "user-login", "--file", str(evidence_file), "--json"], env=env).stdout)

            self.assertEqual("created", first["status"])
            self.assertEqual("existing", second["status"])
            stored = (project / first["path"]).read_text(encoding="utf-8")
            combined = stored + json.dumps(first, ensure_ascii=False)
            self.assertIn("[REDACTED]", combined)
            self.assertNotIn("abc123", combined)
            self.assertNotIn("hunter2", combined)
            stored_json = json.loads(stored)
            self.assertLessEqual(len(stored_json["output_summary"]), 500)
            index = json.loads((project / "noc_docs/.living-docs/evidence-index.json").read_text(encoding="utf-8"))
            self.assertEqual(first["evidence_id"], index["evidence"][0]["id"])
            self.assertEqual("passed", index["evidence"][0]["result"])

    def test_record_rejects_invalid_or_unsupported_evidence_without_writing(self) -> None:
        cases = [
            ("passed_nonzero", evidence_payload(exit_code=1), "invalid_verification_evidence"),
            ("time_order", evidence_payload(finished_at="2026-07-16T09:00:00+08:00"), "invalid_verification_evidence"),
            ("missing_feature", evidence_payload(feature_id="missing-feature"), "feature_not_found"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            for name, payload, status in cases:
                with self.subTest(name=name):
                    result = run(
                        [
                            "evidence",
                            "record",
                            str(project),
                            "--feature-id",
                            str(payload["feature_id"]),
                            "--file",
                            str(write_json(root / f"{name}.json", payload)),
                            "--json",
                        ],
                        env=env,
                        check=False,
                    )
                    self.assertEqual(status, json.loads(result.stdout)["status"])

            config = project / "noc_docs/.living-docs/config.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["layout"] = "simplified"
            data.pop("layout_version", None)
            config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = run(
                ["evidence", "record", str(project), "--feature-id", "user-login", "--file", str(write_json(root / "ok.json", evidence_payload())), "--json"],
                env=env,
                check=False,
            )
            self.assertEqual("unsupported_layout", json.loads(result.stdout)["status"])

    def test_index_rebuilds_evidence_index_and_reports_damaged_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            evidence_file = write_json(root / "evidence.json", evidence_payload(result="failed", exit_code=1, output_summary="1 failed"))
            created = json.loads(run(["evidence", "record", str(project), "--feature-id", "user-login", "--file", str(evidence_file), "--json"], env=env).stdout)
            (project / "noc_docs/.living-docs/evidence-index.json").unlink()

            run(["index", str(project)], env=env)
            rebuilt = json.loads((project / "noc_docs/.living-docs/evidence-index.json").read_text(encoding="utf-8"))
            self.assertEqual(created["evidence_id"], rebuilt["evidence"][0]["id"])
            self.assertEqual("failed", rebuilt["evidence"][0]["result"])

            stored = project / created["path"]
            stored.write_text("{bad json", encoding="utf-8")
            result = run(["index", str(project)], env=env, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("invalid evidence", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
