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
    return project, env


def overview_path(project: Path) -> Path:
    return project / "noc_docs/features/user-login/overview.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_patch(root: Path, payload: dict) -> Path:
    path = root / "patch.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def base_patch(feature_id: str = "user-login") -> dict:
    return {
        "schema_version": "1.0",
        "feature_id": feature_id,
        "source": {"actor": "codex-skill", "intent": "连续失败五次后锁定账号 30 分钟"},
        "patch": {},
    }


def update(project: Path, env: dict[str, str], patch_file: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["feature", "update", str(project), "--id", "user-login", "--patch-file", str(patch_file), "--json"], env=env, check=check)


class FeatureArchiveUpdateTests(unittest.TestCase):
    def test_update_applies_structured_patch_locally_and_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            overview = overview_path(project)
            overview.write_text(
                overview.read_text(encoding="utf-8")
                + "\n## 手工章节\n\n这里是用户手工内容。\n",
                encoding="utf-8",
            )
            before_text = overview.read_text(encoding="utf-8")
            before_sha = sha256(overview)
            patch = base_patch()
            patch["expected_overview_sha256"] = before_sha
            patch["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-lockout-5-failures", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ],
                "implementation_upsert": [
                    {"id": "impl-login-failure-counter", "text": "登录失败次数会在认证失败后累计。", "source": "code_diff"}
                ],
                "constraints_add": [
                    {"id": "constraint-no-plaintext-password", "text": "不得记录明文密码。", "source": "security_review"}
                ],
                "code_paths_add": ["src\\auth\\login.py", "tests/中文登录/test_login.py"],
                "verification_methods_upsert": [
                    {
                        "id": "verify-login-tests",
                        "command": "python -m pytest tests/auth/test_login.py",
                        "scope": "用户登录失败锁定",
                    }
                ],
                "verification_result": {
                    "command": "python -m pytest tests/auth/test_login.py",
                    "cwd": ".",
                    "started_at": "2026-07-16T10:00:00+08:00",
                    "finished_at": "2026-07-16T10:00:12+08:00",
                    "exit_code": 0,
                    "result": "passed",
                    "scope": "用户登录失败锁定",
                    "output_summary": "3 passed",
                },
                "major_change_append": [
                    {
                        "id": "change-login-lockout-policy",
                        "date": "2026-07-16",
                        "summary": "新增连续登录失败锁定策略。",
                        "details": ["连续失败 5 次后锁定 30 分钟。", "修改用户可观察的登录失败行为。"],
                        "source": "user_request+code_diff",
                    }
                ],
                "pending_questions_add": [
                    {"id": "question-lockout-storage", "text": "失败次数应该存储在数据库还是缓存中？", "source": "insufficient_evidence"}
                ],
            }

            payload = json.loads(update(project, env, write_patch(root, patch)).stdout)
            after_text = overview.read_text(encoding="utf-8")

            self.assertEqual("updated", payload["status"])
            self.assertEqual("passed", payload["concurrency_check"])
            self.assertTrue(payload["backup_path"].startswith("noc_docs/.living-docs/backups/"))
            self.assertEqual(before_text, (project / payload["backup_path"]).read_text(encoding="utf-8"))
            self.assertIn("## 已确认需求", after_text)
            self.assertIn("- 连续登录失败 5 次后，账号锁定 30 分钟。 <!-- noc:id=req-lockout-5-failures -->", after_text)
            self.assertIn("## 当前实现", after_text)
            self.assertIn("- 登录失败次数会在认证失败后累计。 <!-- noc:id=impl-login-failure-counter -->", after_text)
            self.assertIn("- `src/auth/login.py`", after_text)
            self.assertIn("- `tests/中文登录/test_login.py`", after_text)
            self.assertIn("## 最近验证结果", after_text)
            self.assertIn("passed", after_text)
            self.assertIn("## 手工章节\n\n这里是用户手工内容。", after_text)
            self.assertNotEqual(before_sha, payload["after_sha256"])
            feature_index = json.loads((project / "noc_docs/.living-docs/feature-index.json").read_text(encoding="utf-8"))
            self.assertEqual("user-login", feature_index["features"][0]["id"])

    def test_repeating_same_patch_is_unchanged_and_creates_no_second_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            patch = base_patch()
            patch["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-lockout-5-failures", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ],
                "code_paths_add": ["src/auth/login.py"],
            }
            patch_file = write_patch(root, patch)

            first = json.loads(update(project, env, patch_file).stdout)
            second = json.loads(update(project, env, patch_file).stdout)

            self.assertEqual("updated", first["status"])
            self.assertEqual("unchanged", second["status"])
            self.assertIsNone(second["backup_path"])
            self.assertTrue(second["ignored_duplicates"])
            self.assertEqual(first["after_sha256"], second["after_sha256"])

    def test_update_and_remove_managed_requirement_and_pending_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            first = base_patch()
            first["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-lockout-5-failures", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ],
                "pending_questions_add": [
                    {"id": "question-lockout-storage", "text": "失败次数应该存储在数据库还是缓存中？", "source": "insufficient_evidence"}
                ],
            }
            update(project, env, write_patch(root, first))
            second = base_patch()
            second["patch"] = {
                "confirmed_requirements_update": [
                    {"id": "req-lockout-5-failures", "text": "连续登录失败 5 次后，账号锁定 60 分钟。", "source": "user_request"}
                ],
                "pending_questions_resolve": [
                    {"id": "question-lockout-storage", "resolution": "使用 Redis 保存失败次数。", "resolved_at": "2026-07-16"}
                ],
            }
            update(project, env, write_patch(root, second))
            third = base_patch()
            third["patch"] = {
                "confirmed_requirements_remove": [
                    {"id": "req-lockout-5-failures", "reason": "用户明确取消该需求"}
                ]
            }

            payload = json.loads(update(project, env, write_patch(root, third)).stdout)
            text = overview_path(project).read_text(encoding="utf-8")

            self.assertEqual("updated", payload["status"])
            self.assertNotIn("req-lockout-5-failures", text)
            self.assertNotIn("question-lockout-storage", text)
            self.assertNotIn("使用 Redis", text)

    def test_duplicate_text_with_different_id_is_conflict_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            first = base_patch()
            first["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-one", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ]
            }
            update(project, env, write_patch(root, first))
            before = sha256(overview_path(project))
            second = base_patch()
            second["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-two", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ]
            }

            result = update(project, env, write_patch(root, second), check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(2, result.returncode)
            self.assertEqual("duplicate_content_conflict", payload["status"])
            self.assertEqual(before, sha256(overview_path(project)))

    def test_sha_conflict_returns_conflict_without_backup_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            before = sha256(overview_path(project))
            patch = base_patch()
            patch["expected_overview_sha256"] = "0" * 64
            patch["patch"] = {
                "confirmed_requirements_add": [
                    {"id": "req-lockout-5-failures", "text": "连续登录失败 5 次后，账号锁定 30 分钟。", "source": "user_request"}
                ]
            }

            result = update(project, env, write_patch(root, patch), check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(2, result.returncode)
            self.assertEqual("conflict", payload["status"])
            self.assertEqual("overview_changed", payload["reason"])
            self.assertEqual(before, sha256(overview_path(project)))
            self.assertFalse((project / "noc_docs/.living-docs/backups").exists())

    def test_invalid_patch_inputs_return_json_errors_and_do_not_write(self) -> None:
        cases = [
            ("missing_schema", {"feature_id": "user-login", "source": {"actor": "codex-skill"}, "patch": {}}),
            ("feature_id_mismatch", base_patch("other-feature")),
            ("invalid_item_id", {**base_patch(), "patch": {"confirmed_requirements_add": [{"id": "Bad_Id", "text": "中文需求", "source": "user"}]}}),
            ("empty_text", {**base_patch(), "patch": {"confirmed_requirements_add": [{"id": "req-empty", "text": "", "source": "user"}]}}),
            ("missing_source", {"schema_version": "1.0", "feature_id": "user-login", "patch": {}}),
            (
                "passed_nonzero",
                {
                    **base_patch(),
                    "patch": {
                        "verification_result": {
                            "command": "python -m pytest",
                            "cwd": ".",
                            "started_at": "2026-07-16T10:00:00+08:00",
                            "finished_at": "2026-07-16T10:00:12+08:00",
                            "exit_code": 1,
                            "result": "passed",
                            "scope": "登录",
                            "output_summary": "failed",
                        }
                    },
                },
            ),
            (
                "invalid_date",
                {
                    **base_patch(),
                    "patch": {
                        "major_change_append": [
                            {"id": "change-login", "date": "2026-99-99", "summary": "变化", "details": [], "source": "user"}
                        ]
                    },
                },
            ),
            ("unsafe_path", {**base_patch(), "patch": {"code_paths_add": ["../secret.txt"]}}),
            ("unknown_field", {**base_patch(), "patch": {"confirmed_requirements_add": [], "surprise": []}}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            before = sha256(overview_path(project))
            for name, patch in cases:
                with self.subTest(name=name):
                    result = update(project, env, write_patch(root, patch), check=False)
                    payload = json.loads(result.stdout)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(payload["status"], {"invalid_patch", "invalid_verification_result", "unsafe_path"})
                    self.assertEqual(before, sha256(overview_path(project)))

    def test_verification_results_are_limited_to_three_and_do_not_infer_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            for index, result in enumerate(["failed", "not_run", "unknown", "passed"], start=1):
                patch = base_patch()
                patch["patch"] = {
                    "verification_result": {
                        "command": f"python -m pytest tests/auth/test_{index}.py",
                        "cwd": ".",
                        "started_at": f"2026-07-16T10:00:0{index}+08:00",
                        "finished_at": f"2026-07-16T10:00:1{index}+08:00",
                        "exit_code": 0 if result == "passed" else (1 if result == "failed" else None),
                        "result": result,
                        "scope": f"范围 {index}",
                        "output_summary": f"summary {index}",
                    }
                }
                update(project, env, write_patch(root, patch))

            text = overview_path(project).read_text(encoding="utf-8")

            self.assertNotIn("test_1.py", text)
            self.assertIn("test_2.py", text)
            self.assertIn("test_3.py", text)
            self.assertIn("test_4.py", text)

    def test_unsupported_layout_and_missing_feature_do_not_create_feature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            patch = base_patch("missing-feature")
            patch["patch"] = {}
            missing_result = run(
                ["feature", "update", str(project), "--id", "missing-feature", "--patch-file", str(write_patch(root, patch)), "--json"],
                env=env,
                check=False,
            )
            self.assertEqual("feature_not_found", json.loads(missing_result.stdout)["status"])
            self.assertFalse((project / "noc_docs/features/missing-feature").exists())

            config = project / "noc_docs/.living-docs/config.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["layout"] = "simplified"
            data.pop("layout_version", None)
            config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            unsupported_result = update(project, env, write_patch(root, base_patch()), check=False)
            self.assertEqual("unsupported_layout", json.loads(unsupported_result.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
