from __future__ import annotations

import hashlib
import json
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


def ready_project(root: Path) -> tuple[Path, dict[str, str]]:
    env = {"CODEX_HOME": str(root / "Codex Home 中文")}
    run(["setup", "--json"], env=env)
    project = root / "project"
    project.mkdir()
    run(["init", str(project)], env=env)
    return project, env


def file_hashes(project: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(project).parts:
            hashes[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def write_overview(
    project: Path,
    feature_id: str,
    name: str,
    *,
    aliases: list[str] | None = None,
    status: str = "active",
    body: str = "",
) -> None:
    feature = project / "noc_docs/features" / feature_id
    feature.mkdir(parents=True, exist_ok=True)
    alias_lines = "".join(f"  - {alias}\n" for alias in aliases or [])
    aliases_block = f"aliases:\n{alias_lines}" if aliases is not None else "aliases: []\n"
    (feature / "overview.md").write_text(
        "---\n"
        f"id: {feature_id}\n"
        f"name: {name}\n"
        f"{aliases_block}"
        f"status: {status}\n"
        "schema_version: 1\n"
        "created_at: 2026-07-16\n"
        "updated_at: 2026-07-16\n"
        "language: zh-CN\n"
        "---\n\n"
        f"# {name}\n\n"
        f"{body}",
        encoding="utf-8",
    )


def work(project: Path, env: dict[str, str], *args: str) -> dict:
    return json.loads(run(["work", str(project), *args, "--json"], env=env).stdout)


class FeatureArchiveCandidateRoutingTests(unittest.TestCase):
    def test_intent_matches_feature_id_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "user-login")

            self.assertEqual("feature-archive", payload["layout"])
            self.assertEqual("use_existing", payload["action"])
            self.assertEqual("user-login", payload["candidates"][0]["id"])
            self.assertEqual("high", payload["candidates"][0]["confidence"])
            self.assertIn({"type": "feature_id_match", "value": "user-login"}, payload["candidates"][0]["evidence"])

    def test_chinese_name_and_alias_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录", "账号登录"])
            run(["index", str(project)], env=env)

            by_name = work(project, env, "--intent", "用户登录")
            by_alias = work(project, env, "--intent", "账号登录")

            self.assertEqual("user-login", by_name["candidates"][0]["id"])
            self.assertIn({"type": "name_match", "value": "用户登录"}, by_name["candidates"][0]["evidence"])
            self.assertEqual("user-login", by_alias["candidates"][0]["id"])
            self.assertIn({"type": "alias_match", "value": "账号登录"}, by_alias["candidates"][0]["evidence"])

    def test_alias_high_confidence_but_weak_common_terms_are_not_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(
                project,
                "user-login",
                "用户登录",
                aliases=["登录"],
                body="## 功能目标\n\n支持用户登录和账号管理查询。\n",
            )
            run(["index", str(project)], env=env)

            alias = work(project, env, "--intent", "登录")
            self.assertEqual("user-login", alias["candidates"][0]["id"])
            self.assertEqual("high", alias["candidates"][0]["confidence"])

            for term in ["用户", "管理", "查询"]:
                with self.subTest(term=term):
                    payload = work(project, env, "--intent", term)
                    if payload["candidates"]:
                        self.assertNotEqual("high", payload["candidates"][0]["confidence"])
                    else:
                        self.assertEqual("no_match", payload["action"])

    def test_english_name_case_normalized_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "User Login", aliases=["login"])
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "user login")

            self.assertEqual("user-login", payload["candidates"][0]["id"])
            self.assertEqual("high", payload["candidates"][0]["confidence"])

    def test_code_path_exact_prefix_windows_and_chinese_path_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(
                project,
                "user-login",
                "用户登录",
                body="## 代码范围\n\n- `src/auth/login.py`\n- `src/auth/`\n- `src/中文登录/`\n",
            )
            run(["index", str(project)], env=env)

            exact = work(project, env, "--path", "src/auth/login.py")
            prefix = work(project, env, "--path", "src\\auth\\controller.py")
            chinese = work(project, env, "--path", "src/中文登录/service.py")

            self.assertEqual("user-login", exact["candidates"][0]["id"])
            self.assertIn({"type": "code_path_exact_match", "value": "src/auth/login.py"}, exact["candidates"][0]["evidence"])
            self.assertEqual("user-login", prefix["candidates"][0]["id"])
            self.assertIn({"type": "code_path_prefix_match", "value": "src/auth/"}, prefix["candidates"][0]["evidence"])
            self.assertEqual("user-login", chinese["candidates"][0]["id"])

    def test_test_path_related_to_feature_code_scope_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", body="## 代码范围\n\n- `src/auth/`\n")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--path", "tests/auth/test_login.py")

            self.assertEqual("user-login", payload["candidates"][0]["id"])
            self.assertIn(
                {"type": "test_path_related_match", "value": "tests/auth/test_login.py -> src/auth/"},
                payload["candidates"][0]["evidence"],
            )

    def test_intent_and_path_combined_raise_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录"], body="## 代码范围\n\n- `src/auth/`\n")
            run(["index", str(project)], env=env)

            intent_only = work(project, env, "--intent", "登录")
            combined = work(project, env, "--intent", "登录", "--path", "src/auth/login.py")

            self.assertGreater(combined["candidates"][0]["score"], intent_only["candidates"][0]["score"])
            self.assertEqual("high", combined["candidates"][0]["confidence"])

    def test_weak_keyword_does_not_create_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", body="## 功能目标\n\n支持用户使用账号登录。\n")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "用户")

            if payload["candidates"]:
                self.assertNotEqual("high", payload["candidates"][0]["confidence"])
            else:
                self.assertEqual("no_match", payload["action"])

    def test_ambiguous_scores_return_ask_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录"])
            write_overview(project, "admin-login", "管理员登录", aliases=["登录"])
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "登录")

            self.assertTrue(payload["ambiguity"]["is_ambiguous"])
            self.assertEqual("ask_user", payload["action"])

    def test_intent_and_path_conflict_returns_ask_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录"], body="## 代码范围\n\n- `src/auth/`\n")
            write_overview(project, "billing", "账单管理", aliases=["账单"], body="## 代码范围\n\n- `src/billing/`\n")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "登录", "--path", "src/billing/invoice.py")

            self.assertEqual("ask_user", payload["action"])
            self.assertTrue(payload["ambiguity"]["is_ambiguous"])

    def test_no_candidate_returns_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "库存盘点")

            self.assertEqual([], payload["candidates"])
            self.assertEqual({"is_ambiguous": False, "top_delta": None}, payload["ambiguity"])
            self.assertEqual("no_match", payload["action"])

    def test_deprecated_feature_is_penalized_and_marked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "old-login", "旧登录", aliases=["登录"], status="deprecated")
            run(["index", str(project)], env=env)

            payload = work(project, env, "--intent", "登录")

            self.assertEqual("deprecated", payload["candidates"][0]["status"])
            self.assertLess(payload["candidates"][0]["score"], 0.78)

    def test_output_order_is_stable_when_scores_tie(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "z-login", "登录功能", aliases=["登录"])
            write_overview(project, "a-login", "登录功能", aliases=["登录"])
            run(["index", str(project)], env=env)

            first = work(project, env, "--intent", "登录")
            second = work(project, env, "--intent", "登录")

            self.assertEqual([c["id"] for c in first["candidates"]], [c["id"] for c in second["candidates"]])
            self.assertEqual(["a-login", "z-login"], [c["id"] for c in first["candidates"]])

    def test_missing_index_falls_back_to_overview_scan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录"])
            run(["index", str(project)], env=env)
            (project / "noc_docs/.living-docs/feature-index.json").unlink()
            before = file_hashes(project)

            payload = work(project, env, "--intent", "登录")

            self.assertEqual("user-login", payload["candidates"][0]["id"])
            self.assertEqual(before, file_hashes(project))
            self.assertFalse((project / "noc_docs/.living-docs/feature-index.json").exists())

    def test_work_is_read_only_for_user_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = ready_project(Path(tmp))
            write_overview(project, "user-login", "用户登录", aliases=["登录"])
            run(["index", str(project)], env=env)
            before = file_hashes(project)

            work(project, env, "--intent", "登录", "--path", "src/auth/login.py")

            self.assertEqual(before, file_hashes(project))

    def test_simplified_and_v1_work_contracts_remain_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, env = ready_project(root)
            shutil.rmtree(project / "noc_docs/features")
            config = project / "noc_docs/.living-docs/config.json"
            data = json.loads(config.read_text(encoding="utf-8"))
            data["layout"] = "simplified"
            data.pop("layout_version", None)
            config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            simplified = work(project, env, "--intent", "登录")

            self.assertEqual("simplified", simplified["layout"])
            self.assertIn("features", simplified)

            legacy = root / "legacy"
            run(["init", str(legacy), "--mode", "small"], env=env)
            legacy_work = json.loads(run(["work", str(legacy), "--path", "unknown/file.py", "--json"], env=env).stdout)
            self.assertEqual(1, legacy_work["protocol_version"])


if __name__ == "__main__":
    unittest.main()
