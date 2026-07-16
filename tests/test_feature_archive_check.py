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
    run(["feature", "ensure", str(project), "--id", "user-login", "--name", "用户登录", "--alias", "登录", "--json"], env=env)
    run(["feature", "ensure", str(project), "--id", "account-security", "--name", "账号安全", "--alias", "安全", "--json"], env=env)
    subprocess.run(["git", "-C", str(project), "init"], check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "-C", str(project), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(project), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(["git", "-C", str(project), "commit", "-m", "init"], check=True, stdout=subprocess.PIPE)
    return project, env


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def file_hashes(project: Path) -> dict[str, str]:
    return {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(project.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(project).parts
    }


def update_overview(project: Path, env: dict[str, str], feature_id: str = "user-login") -> dict:
    patch = {
        "schema_version": "1.0",
        "feature_id": feature_id,
        "source": {"actor": "codex-skill"},
        "patch": {
            "confirmed_requirements_add": [{"id": "req-lockout", "text": "连续登录失败 5 次后锁定账号。", "source": "user"}],
            "implementation_upsert": [{"id": "impl-lockout", "text": "登录失败次数会在认证失败后累计。", "source": "code"}],
            "verification_methods_upsert": [{"id": "verify-lockout", "command": "python -m pytest tests/auth/test_login.py", "scope": "登录锁定"}],
            "verification_result": {
                "command": "python -m pytest tests/auth/test_login.py",
                "cwd": ".",
                "started_at": "2026-07-16T10:00:00+08:00",
                "finished_at": "2026-07-16T10:00:12+08:00",
                "exit_code": 0,
                "result": "passed",
                "scope": "登录锁定",
                "output_summary": "3 passed",
            },
            "major_change_append": [{"id": "change-lockout", "date": "2026-07-16", "summary": "新增锁定策略。", "details": [], "source": "user"}],
            "code_paths_add": ["src/auth/login.py"],
        },
    }
    patch_file = write_json(project / f"{feature_id}-patch.json", patch)
    return json.loads(run(["feature", "update", str(project), "--id", feature_id, "--patch-file", str(patch_file), "--json"], env=env).stdout)


def record_evidence(project: Path, env: dict[str, str], result: str = "passed", feature_id: str = "user-login") -> str:
    payload = {
        "schema_version": "1.0",
        "feature_id": feature_id,
        "command": "python -m pytest tests/auth/test_login.py",
        "cwd": ".",
        "started_at": "2026-07-16T10:00:00+08:00",
        "finished_at": "2026-07-16T10:00:12+08:00",
        "exit_code": 0 if result == "passed" else 1,
        "result": result,
        "scope": "登录锁定",
        "output_summary": "3 passed" if result == "passed" else "1 failed",
        "source": {"actor": "codex-skill"},
    }
    evidence_file = write_json(project / f"{feature_id}-{result}-evidence.json", payload)
    response = json.loads(run(["evidence", "record", str(project), "--feature-id", feature_id, "--file", str(evidence_file), "--json"], env=env).stdout)
    return response["evidence_id"]


def impact(**overrides: object) -> dict:
    payload = {
        "schema_version": "1.0",
        "feature_ids": ["user-login"],
        "change_class": "requirement",
        "code_evidence": {"mode": "staged"},
        "verification_evidence_ids": [],
        "documentation_updates": [
            {
                "feature_id": "user-login",
                "status": "updated",
                "updated_sections": ["已确认需求", "当前实现", "验证方式", "最近验证结果"],
                "reason": None,
            }
        ],
        "major_change_ids": [],
    }
    payload.update(overrides)
    return payload


class FeatureArchiveCheckTests(unittest.TestCase):
    def test_requirement_impact_passes_with_docs_and_passed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            update_overview(project, env)
            evidence_id = record_evidence(project, env)
            (project / "src/auth").mkdir(parents=True)
            (project / "src/auth/login.py").write_text("print('login')\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            impact_file = write_json(project / "impact.json", impact(verification_evidence_ids=[evidence_id]))
            before = file_hashes(project)

            payload = json.loads(run(["check", str(project), "--feature-impact-file", str(impact_file), "--json"], env=env).stdout)

            self.assertEqual("passed", payload["status"])
            self.assertEqual([], payload["errors"])
            self.assertIn({"id": "feature_exists", "status": "passed"}, payload["checks"])
            self.assertEqual(before, file_hashes(project))

    def test_requirement_missing_or_failed_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            update_overview(project, env)
            missing = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "missing.json", impact())), "--json"], env=env, check=False).stdout)
            self.assertEqual("failed", missing["status"])
            self.assertEqual("missing_verification_evidence", missing["errors"][0]["code"])

            failed_id = record_evidence(project, env, "failed")
            failed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "failed.json", impact(verification_evidence_ids=[failed_id]))), "--json"], env=env, check=False).stdout)
            self.assertEqual("failed", failed["status"])
            self.assertEqual("verification_not_passed", failed["errors"][0]["code"])

    def test_major_requires_major_change_id_and_document_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            update_overview(project, env)
            evidence_id = record_evidence(project, env)
            major_payload = impact(
                change_class="major",
                verification_evidence_ids=[evidence_id],
                documentation_updates=[
                    {
                        "feature_id": "user-login",
                        "status": "updated",
                        "updated_sections": ["已确认需求", "当前实现", "验证方式", "最近验证结果", "最近重大变更"],
                        "reason": None,
                    }
                ],
                major_change_ids=["change-lockout"],
            )
            passed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "major.json", major_payload)), "--json"], env=env).stdout)
            self.assertEqual("passed", passed["status"])

            no_id = dict(major_payload)
            no_id["major_change_ids"] = []
            failed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "major-missing.json", no_id)), "--json"], env=env, check=False).stdout)
            self.assertEqual("missing_major_change", failed["errors"][0]["code"])

    def test_implementation_and_none_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            implementation = impact(
                change_class="implementation",
                documentation_updates=[{"feature_id": "user-login", "status": "not_required", "updated_sections": [], "reason": "纯内部重构"}],
            )
            ok = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "impl.json", implementation)), "--json"], env=env).stdout)
            self.assertEqual("passed", ok["status"])
            self.assertTrue(ok["warnings"])

            no_reason = impact(
                change_class="implementation",
                documentation_updates=[{"feature_id": "user-login", "status": "not_required", "updated_sections": [], "reason": None}],
            )
            failed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "impl-bad.json", no_reason)), "--json"], env=env, check=False).stdout)
            self.assertEqual("missing_documentation_reason", failed["errors"][0]["code"])

            none_payload = impact(change_class="none", feature_ids=[], documentation_updates=[], code_evidence={"mode": "staged"})
            none = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "none.json", none_payload)), "--json"], env=env).stdout)
            self.assertEqual("passed", none["status"])

    def test_multi_feature_and_mismatched_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            update_overview(project, env, "user-login")
            update_overview(project, env, "account-security")
            security_evidence = record_evidence(project, env, feature_id="account-security")
            payload = impact(
                feature_ids=["user-login", "account-security"],
                verification_evidence_ids=[security_evidence],
                documentation_updates=[
                    {"feature_id": "user-login", "status": "updated", "updated_sections": ["已确认需求", "当前实现", "验证方式"], "reason": None},
                    {"feature_id": "account-security", "status": "updated", "updated_sections": ["已确认需求", "当前实现", "最近验证结果"], "reason": None},
                ],
            )
            passed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "multi.json", payload)), "--json"], env=env).stdout)
            self.assertEqual("passed", passed["status"])

            mismatch = impact(verification_evidence_ids=[security_evidence])
            failed = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "mismatch.json", mismatch)), "--json"], env=env, check=False).stdout)
            self.assertEqual("evidence_feature_mismatch", failed["errors"][0]["code"])

    def test_declared_sections_must_exist_and_old_memory_impact_contract_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            bad = impact(
                documentation_updates=[
                    {"feature_id": "user-login", "status": "updated", "updated_sections": ["不存在章节"], "reason": None}
                ],
                verification_evidence_ids=["ev-missing"],
            )
            result = json.loads(run(["check", str(project), "--feature-impact-file", str(write_json(project / "bad-section.json", bad)), "--json"], env=env, check=False).stdout)
            self.assertEqual("declared_section_missing", result["errors"][0]["code"])

            legacy = json.loads(run(["check", str(project), "--memory-impact", "none", "--json"], env=env).stdout)
            self.assertEqual("ok", legacy["status"])


if __name__ == "__main__":
    unittest.main()
