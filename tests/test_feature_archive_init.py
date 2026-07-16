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


def ready_home(root: Path) -> dict[str, str]:
    env = {"CODEX_HOME": str(root / "Codex Home 中文")}
    run(["setup", "--json"], env=env)
    return env


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def derived_files(project: Path) -> list[Path]:
    living = project / "noc_docs/.living-docs"
    return [
        living / "routing.json",
        living / "manifest.json",
        living / "feature-index.json",
        living / "evidence-index.json",
    ]


def write_manual_overview(project: Path) -> None:
    feature = project / "noc_docs/features/user-login"
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "overview.md").write_text(
        "---\n"
        "id: user-login\n"
        "name: 用户登录\n"
        "aliases:\n"
        "  - 登录\n"
        "  - 账号登录\n"
        "status: active\n"
        "schema_version: 1\n"
        "created_at: 2026-07-16\n"
        "updated_at: 2026-07-16\n"
        "language: zh-CN\n"
        "---\n\n"
        "# 用户登录\n\n## 功能目标\n\n支持用户登录。\n",
        encoding="utf-8",
    )


class FeatureArchiveInitTests(unittest.TestCase):
    def test_default_init_creates_feature_archive_structure_without_business_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "中文 Project with spaces"
            project.mkdir()
            env = ready_home(root)

            run(["init", str(project)], env=env)

            files = {path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file()}
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
            self.assertTrue((project / "noc_docs/features").is_dir())
            self.assertEqual([], list((project / "noc_docs/features").iterdir()))

    def test_default_init_writes_feature_archive_config_with_english_machine_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            env = ready_home(root)

            run(["init", str(project)], env=env)

            config = read_json(project / "noc_docs/.living-docs/config.json")
            self.assertEqual(
                {
                    "protocol": "noc-living-docs",
                    "protocol_version": 2,
                    "layout": "feature-archive",
                    "layout_version": "1.0",
                    "documentation_root": "noc_docs",
                    "language": "zh-CN",
                    "machine_keys": "en-US",
                    "feature_id_style": "ascii-kebab-case",
                },
                {key: config[key] for key in [
                    "protocol",
                    "protocol_version",
                    "layout",
                    "layout_version",
                    "documentation_root",
                    "language",
                    "machine_keys",
                    "feature_id_style",
                ]},
            )

    def test_default_init_writes_chinese_project_memory_without_inventing_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            (project / "README.md").write_text("# 示例项目\n", encoding="utf-8")
            env = ready_home(root)

            run(["init", str(project)], env=env)

            project_doc = (project / "noc_docs/project.md").read_text(encoding="utf-8")
            guardrails = (project / "noc_docs/guardrails.md").read_text(encoding="utf-8")
            verification = (project / "noc_docs/verification.md").read_text(encoding="utf-8")
            for heading in ["项目目标", "当前阶段", "主要能力", "架构与模块职责", "项目边界"]:
                self.assertIn(heading, project_doc)
            for heading in ["安全约束", "兼容性约束", "数据约束", "权限约束", "发布与迁移约束"]:
                self.assertIn(heading, guardrails)
            for heading in ["构建方式", "测试方式", "启动方式", "验收要求"]:
                self.assertIn(heading, verification)
            self.assertIn("待补充", project_doc)
            self.assertNotIn("billing", project_doc.lower())

    def test_repeated_init_preserves_existing_feature_archive_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            env = ready_home(root)
            run(["init", str(project)], env=env)
            project_doc = project / "noc_docs/project.md"
            project_doc.write_text(project_doc.read_text(encoding="utf-8") + "\n用户保留内容。\n", encoding="utf-8")
            before = file_hashes(project)

            run(["init", str(project)], env=env)

            self.assertEqual(before, file_hashes(project))

    def test_old_simplified_init_is_not_converted_by_default_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "legacy"
            project.mkdir()
            env = ready_home(root)
            run(["init", str(project)], env=env)
            config = project / "noc_docs/.living-docs/config.json"
            data = read_json(config)
            data["layout"] = "simplified"
            data.pop("layout_version", None)
            config.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            before = file_hashes(project)

            run(["init", str(project)], env=env)

            self.assertEqual(before, file_hashes(project))
            self.assertEqual("simplified", read_json(config)["layout"])


class FeatureArchiveIndexTests(unittest.TestCase):
    def initialized_project(self, root: Path) -> tuple[Path, dict[str, str]]:
        project = root / "project"
        project.mkdir()
        env = ready_home(root)
        run(["init", str(project)], env=env)
        return project, env

    def test_index_rebuilds_deleted_derived_json_without_changing_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))
            markdown_before = {
                path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (project / "noc_docs").rglob("*.md")
            }
            for path in derived_files(project):
                path.unlink()

            run(["index", str(project)], env=env)

            for path in derived_files(project):
                self.assertTrue(path.is_file(), path)
            markdown_after = {
                path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (project / "noc_docs").rglob("*.md")
            }
            self.assertEqual(markdown_before, markdown_after)

    def test_index_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))

            run(["index", str(project)], env=env)
            first = {path.relative_to(project).as_posix(): path.read_text(encoding="utf-8") for path in derived_files(project)}
            run(["index", str(project)], env=env)
            second = {path.relative_to(project).as_posix(): path.read_text(encoding="utf-8") for path in derived_files(project)}

            self.assertEqual(first, second)

    def test_feature_index_represents_empty_feature_collection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))

            run(["index", str(project)], env=env)

            self.assertEqual({"schema_version": "1.0", "features": []}, read_json(project / "noc_docs/.living-docs/feature-index.json"))

    def test_feature_index_reads_existing_overview_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))
            write_manual_overview(project)

            run(["index", str(project)], env=env)

            feature_index = read_json(project / "noc_docs/.living-docs/feature-index.json")
            self.assertEqual(
                [
                    {
                        "id": "user-login",
                        "name": "用户登录",
                        "aliases": ["登录", "账号登录"],
                        "status": "active",
                        "language": "zh-CN",
                        "overview_path": "noc_docs/features/user-login/overview.md",
                        "updated_at": "2026-07-16",
                    }
                ],
                feature_index["features"],
            )

    def test_index_failure_preserves_existing_derived_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))
            write_manual_overview(project)
            run(["index", str(project)], env=env)
            before = {path.relative_to(project).as_posix(): path.read_text(encoding="utf-8") for path in derived_files(project)}
            overview = project / "noc_docs/features/user-login/overview.md"
            overview.write_text(overview.read_text(encoding="utf-8").replace("id: user-login", "id: 用户登录"), encoding="utf-8")

            result = run(["index", str(project)], env=env, check=False)

            self.assertNotEqual(0, result.returncode)
            after = {path.relative_to(project).as_posix(): path.read_text(encoding="utf-8") for path in derived_files(project)}
            self.assertEqual(before, after)

    def test_index_does_not_translate_chinese_markdown_to_english(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project, env = self.initialized_project(Path(tmp))
            before = (project / "noc_docs/project.md").read_text(encoding="utf-8")

            run(["index", str(project)], env=env)

            self.assertEqual(before, (project / "noc_docs/project.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
