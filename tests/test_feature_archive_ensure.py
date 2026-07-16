from __future__ import annotations

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
    return project, env


def ensure(project: Path, env: dict[str, str], *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["feature", "ensure", str(project), *args, "--json"], env=env, check=check)


class FeatureArchiveEnsureTests(unittest.TestCase):
    def test_ensure_creates_chinese_feature_overview_and_indexes_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))

            result = ensure(
                project,
                env,
                "--id",
                "user-login",
                "--name",
                "用户登录",
                "--alias",
                "登录",
                "--alias",
                "账号登录",
                "--intent",
                "连续登录失败 5 次后，账号锁定 30 分钟。",
            )
            payload = json.loads(result.stdout)

            self.assertEqual("created", payload["status"])
            self.assertEqual(
                {
                    "id": "user-login",
                    "name": "用户登录",
                    "aliases": ["登录", "账号登录"],
                    "overview_path": "noc_docs/features/user-login/overview.md",
                },
                payload["feature"],
            )
            overview = (project / "noc_docs/features/user-login/overview.md").read_text(encoding="utf-8")
            self.assertIn("id: user-login", overview)
            self.assertIn("name: 用户登录", overview)
            self.assertIn("## 已确认需求", overview)
            self.assertIn("- 连续登录失败 5 次后，账号锁定 30 分钟。", overview)
            self.assertNotIn("## 当前实现", overview)
            feature_index = json.loads((project / "noc_docs/.living-docs/feature-index.json").read_text(encoding="utf-8"))
            self.assertEqual("user-login", feature_index["features"][0]["id"])

    def test_ensure_without_intent_does_not_invent_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))

            ensure(project, env, "--id", "user-login", "--name", "用户登录")

            overview = (project / "noc_docs/features/user-login/overview.md").read_text(encoding="utf-8")
            self.assertIn("## 功能目标", overview)
            self.assertIn("待补充", overview)
            self.assertNotIn("## 已确认需求", overview)

    def test_ensure_rejects_invalid_feature_ids(self) -> None:
        invalid_ids = ["", "User-Login", "user_login", "user login", "用户登录", "../login", "features"]
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            for feature_id in invalid_ids:
                with self.subTest(feature_id=feature_id):
                    result = ensure(project, env, "--id", feature_id, "--name", "用户登录", check=False)
                    self.assertNotEqual(0, result.returncode)

    def test_ensure_dedupes_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))

            payload = json.loads(
                ensure(project, env, "--id", "user-login", "--name", "用户登录", "--alias", "登录", "--alias", "登录").stdout
            )

            self.assertEqual(["登录"], payload["feature"]["aliases"])

    def test_ensure_existing_is_idempotent_and_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            ensure(project, env, "--id", "user-login", "--name", "用户登录")
            overview = project / "noc_docs/features/user-login/overview.md"
            overview.write_text(overview.read_text(encoding="utf-8") + "\n用户保留内容。\n", encoding="utf-8")

            payload = json.loads(ensure(project, env, "--id", "user-login", "--name", "用户登录").stdout)

            self.assertEqual("existing", payload["status"])
            self.assertIn("用户保留内容。", overview.read_text(encoding="utf-8"))

    def test_ensure_detects_name_or_alias_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            ensure(project, env, "--id", "user-login", "--name", "用户登录", "--alias", "登录")

            result = ensure(project, env, "--id", "account-login", "--name", "用户登录", check=False)

            self.assertEqual(2, result.returncode)
            self.assertEqual("conflict", json.loads(result.stdout)["status"])

    def test_ensure_rejects_non_feature_archive_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            config = project / "noc_docs/.living-docs/config.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["layout"] = "simplified"
            data.pop("layout_version", None)
            config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            result = ensure(project, env, "--id", "user-login", "--name", "用户登录", check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("feature-archive", result.stdout)

    def test_work_finds_feature_created_by_ensure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            ensure(project, env, "--id", "user-login", "--name", "用户登录", "--alias", "登录")

            payload = json.loads(run(["work", str(project), "--intent", "登录", "--json"], env=env).stdout)

            self.assertEqual("user-login", payload["candidates"][0]["id"])
            self.assertEqual("high", payload["candidates"][0]["confidence"])


if __name__ == "__main__":
    unittest.main()
