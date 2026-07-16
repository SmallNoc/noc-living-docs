from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.noclib.migration as migration


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/noc.py"
AGENT_BLOCK = "# Agent Protocol\n\n<!-- noc-living-docs:start -->\n\nUse noc_docs/.\n\n<!-- noc-living-docs:end -->\n"


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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts and ".noc-backups" not in path.relative_to(root).parts
    }


def tree_dirs(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*"))
        if path.is_dir() and ".git" not in path.relative_to(root).parts
    }


def create_simplified_project(root: Path, *, language: str | None = None) -> Path:
    project = root / "旧 simplified 项目"
    living = project / "noc_docs/.living-docs"
    living.mkdir(parents=True)
    (project / "AGENTS.md").write_text(AGENT_BLOCK, encoding="utf-8")
    for name, text in {
        "project.md": "# 项目\n\n这是中文项目正文。\n",
        "guardrails.md": "# 约束\n\n必须保留原文。\n",
        "verification.md": "# 验证\n\n运行 `python -m unittest`。\n",
    }.items():
        (project / "noc_docs" / name).write_text(text, encoding="utf-8")
    config = {
        "protocol": "noc-living-docs",
        "protocol_version": 2,
        "layout": "simplified",
        "documentation_root": "noc_docs",
    }
    if language:
        config["language"] = language
    write_json(living / "config.json", config)
    write_json(
        living / "routing.json",
        {
            "protocol_version": 2,
            "layout": "simplified",
            "project_memory": ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"],
            "routes": [{"path": "**", "read_before_code": ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"]}],
        },
    )
    write_json(
        living / "manifest.json",
        {
            "protocol_version": 2,
            "layout": "simplified",
            "managed_files": ["noc_docs/project.md", "noc_docs/guardrails.md", "noc_docs/verification.md"],
            "files": {
                name: {"sha256": sha256(project / "noc_docs" / name)}
                for name in ["project.md", "guardrails.md", "verification.md"]
            },
        },
    )
    return project


def create_v1_small_project(root: Path) -> Path:
    project = root / "v1 中文 项目"
    feature = project / "noc_docs/features/用户登录"
    feature.mkdir(parents=True)
    (project / "AGENTS.md").write_text(AGENT_BLOCK, encoding="utf-8")
    write_json(project / "noc_docs/.living-docs/config.json", {"protocol": "noc-living-docs", "mode": "small", "documentation_root": "noc_docs"})
    write_json(
        project / "noc_docs/.living-docs/feature-map.json",
        {
            "mode": "small",
            "features": {
                "用户登录": {
                    "paths": ["src/登录/"],
                    "entry": "noc_docs/features/用户登录/agent-guide.md",
                    "requirements": "noc_docs/features/用户登录/requirements.md",
                    "status": "noc_docs/features/用户登录/status.md",
                }
            },
        },
    )
    files = {
        "agent-guide.md": "# Agent Guide: 用户登录\n\n读取登录相关文档。\n",
        "requirements.md": "# Requirements: 用户登录\n\n- 候选需求：支持短信验证码。\n",
        "status.md": "# Current Status: 用户登录\n\n当前实现说明不能被机械认定为最终现状。\n",
        "guardrails.md": "# Guardrails: 用户登录\n\n不得记录明文密码。\n",
        "test-record.md": "# Test Record: 用户登录\n\n2026-07-01: 手工测试失败。\n",
        "change-record.md": "# Change Record: 用户登录\n\n2026-07-01: 初始记录。\n",
        "notes.md": "# Notes: 用户登录\n\n无法分类的中文备注。\n",
    }
    for name, text in files.items():
        (feature / name).write_text(text, encoding="utf-8")
    return project


def create_v1_domain_project(root: Path) -> Path:
    project = root / "domain-project"
    feature = project / "noc_docs/domains/auth/features/login"
    feature.mkdir(parents=True)
    (project / "AGENTS.md").write_text(AGENT_BLOCK, encoding="utf-8")
    write_json(project / "noc_docs/.living-docs/config.json", {"protocol": "noc-living-docs", "mode": "domain", "documentation_root": "noc_docs"})
    write_json(
        project / "noc_docs/.living-docs/feature-map.json",
        {
            "mode": "domain",
            "domains": {"auth": {"name": "认证域"}},
            "features": {"login": {"domain": "auth", "paths": ["src/auth/"]}},
        },
    )
    (feature / "agent-guide.md").write_text("# Agent Guide: Login\n\nDomain feature text.\n", encoding="utf-8")
    (feature / "requirements.md").write_text("# Requirements: Login\n\n- Candidate requirement.\n", encoding="utf-8")
    return project


class FeatureArchiveMigrationTests(unittest.TestCase):
    def test_simplified_dry_run_is_zero_write_and_lists_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            before_hashes = file_hashes(project)
            before_dirs = tree_dirs(project)

            payload = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--dry-run", "--json"]).stdout)

            self.assertEqual("dry_run", payload["status"])
            self.assertEqual("simplified", payload["source_layout"])
            self.assertEqual("feature-archive", payload["target_layout"])
            self.assertTrue(payload["can_apply"])
            self.assertIn({"operation": "create_directory", "path": "noc_docs/features"}, payload["operations"])
            self.assertIn({"operation": "update_config", "path": "noc_docs/.living-docs/config.json"}, payload["operations"])
            self.assertEqual(["noc_docs"], payload["backup_scope"])
            self.assertEqual(before_hashes, file_hashes(project))
            self.assertEqual(before_dirs, tree_dirs(project))
            self.assertFalse((project / ".noc-backups").exists())

    def test_simplified_apply_requires_backup_and_preserves_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            original_docs = {name: (project / "noc_docs" / name).read_bytes() for name in ["project.md", "guardrails.md", "verification.md"]}
            dry_run_operations = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--dry-run", "--json"]).stdout)["operations"]

            rejected = run(["migrate", str(project), "--to", "feature-archive", "--apply", "--json"], check=False)
            self.assertNotEqual(0, rejected.returncode)
            self.assertEqual("backup_required", json.loads(rejected.stdout)["status"])

            payload = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--apply", "--backup", "--json"]).stdout)

            self.assertEqual("applied", payload["status"])
            self.assertEqual(dry_run_operations, payload["operations"])
            self.assertEqual("feature-archive", read_json(project / "noc_docs/.living-docs/config.json")["layout"])
            self.assertEqual("1.0", read_json(project / "noc_docs/.living-docs/config.json")["layout_version"])
            self.assertEqual("zh-CN", read_json(project / "noc_docs/.living-docs/config.json")["language"])
            self.assertEqual([], read_json(project / "noc_docs/.living-docs/feature-index.json")["features"])
            self.assertTrue((project / "noc_docs/features").is_dir())
            self.assertEqual([], list((project / "noc_docs/features").iterdir()))
            for name, data in original_docs.items():
                self.assertEqual(data, (project / "noc_docs" / name).read_bytes())
            backup = project / payload["backup_path"]
            self.assertTrue(backup.is_dir())
            manifest = read_json(backup / "manifest.json")
            self.assertIn("noc_docs/project.md", manifest["files"])
            self.assertIn("rollback_command", payload["rollback"])

    def test_migration_rollback_restores_pre_migration_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            before = file_hashes(project)
            applied = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--apply", "--backup", "--json"]).stdout)

            rolled_back = json.loads(run(["migrate", str(project), "--rollback", applied["backup_id"], "--json"]).stdout)

            self.assertEqual("rolled_back", rolled_back["status"])
            self.assertEqual(before, file_hashes(project))
            self.assertEqual("simplified", read_json(project / "noc_docs/.living-docs/config.json")["layout"])
            self.assertEqual("simplified", rolled_back["final_layout"])
            self.assertTrue((project / rolled_back["pre_rollback_backup_path"]).is_dir())

    def test_v1_dry_run_reports_every_source_file_and_domain_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            small = create_v1_small_project(Path(tmp))
            before = file_hashes(small)

            payload = json.loads(run(["migrate", str(small), "--to", "feature-archive", "--dry-run", "--json"]).stdout)

            self.assertEqual("dry_run", payload["status"])
            self.assertEqual("small", payload["source_layout"])
            self.assertTrue(payload["can_apply"])
            source_paths = {item["path"]: item["operation"] for item in payload["source_files"]}
            for filename in ["agent-guide.md", "requirements.md", "status.md", "guardrails.md", "test-record.md", "change-record.md", "notes.md"]:
                self.assertIn(f"noc_docs/features/用户登录/{filename}", source_paths)
            self.assertEqual("copy_to_legacy", source_paths["noc_docs/features/用户登录/notes.md"])
            self.assertEqual(before, file_hashes(small))

            domain = create_v1_domain_project(Path(tmp))
            domain_payload = json.loads(run(["migrate", str(domain), "--to", "feature-archive", "--dry-run", "--json"]).stdout)
            self.assertEqual("domain", domain_payload["source_layout"])
            self.assertEqual("auth", domain_payload["features"][0]["legacy_domain"])

    def test_v1_apply_preserves_all_original_text_in_legacy_and_can_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_v1_small_project(Path(tmp))
            before = file_hashes(project)
            original_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((project / "noc_docs/features/用户登录").glob("*.md")))

            payload = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--apply", "--backup", "--json"]).stdout)

            self.assertEqual("applied", payload["status"])
            self.assertEqual("feature-archive", read_json(project / "noc_docs/.living-docs/config.json")["layout"])
            feature_dir = project / "noc_docs/features/yong-hu-deng-lu"
            self.assertTrue((feature_dir / "overview.md").is_file())
            legacy_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((feature_dir / "legacy").glob("*.md")))
            for chunk in ["候选需求：支持短信验证码", "当前实现说明不能被机械认定为最终现状", "无法分类的中文备注", "手工测试失败"]:
                self.assertIn(chunk, legacy_text)
            self.assertIn("name: 用户登录", (feature_dir / "overview.md").read_text(encoding="utf-8"))
            self.assertTrue(original_text)
            self.assertEqual(0, run(["validate", str(project)], check=False).returncode)

            rolled_back = json.loads(run(["migrate", str(project), "--rollback", payload["backup_id"], "--json"]).stdout)

            self.assertEqual("rolled_back", rolled_back["status"])
            self.assertEqual(before, file_hashes(project))

    def test_conflicts_unsafe_paths_and_repeated_migration_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            (project / "noc_docs/features").mkdir()
            (project / "noc_docs/features/unexpected.txt").write_text("conflict\n", encoding="utf-8")

            conflict = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--dry-run", "--json"]).stdout)
            self.assertFalse(conflict["can_apply"])
            self.assertEqual("target_conflict", conflict["conflicts"][0]["code"])
            rejected = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--apply", "--backup", "--json"], check=False).stdout)
            self.assertEqual("conflict", rejected["status"])

            unsafe = create_simplified_project(Path(tmp) / "unsafe")
            config = read_json(unsafe / "noc_docs/.living-docs/config.json")
            config["documentation_root"] = "../outside"
            write_json(unsafe / "noc_docs/.living-docs/config.json", config)
            unsafe_result = json.loads(run(["migrate", str(unsafe), "--to", "feature-archive", "--dry-run", "--json"], check=False).stdout)
            self.assertEqual("unsafe_path", unsafe_result["status"])

            clean = create_simplified_project(Path(tmp) / "clean")
            run(["migrate", str(clean), "--to", "feature-archive", "--apply", "--backup", "--json"])
            repeated = json.loads(run(["migrate", str(clean), "--to", "feature-archive", "--dry-run", "--json"]).stdout)
            self.assertIn(repeated["status"], {"already_target", "unchanged"})

    def test_ordinary_commands_do_not_migrate_simplified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            before_config = read_json(project / "noc_docs/.living-docs/config.json")

            run(["work", str(project), "--path", "src/app.py", "--json"])
            run(["index", str(project)])
            run(["doctor", str(project)], check=False)
            run(["validate", str(project)], check=False)
            run(["evidence", str(project), "--staged", "--json"])

            after_config = read_json(project / "noc_docs/.living-docs/config.json")
            self.assertEqual(before_config["layout"], after_config["layout"])
            self.assertNotEqual("feature-archive", after_config["layout"])
            self.assertFalse((project / "noc_docs/features").exists())
            self.assertFalse((project / ".noc-backups").exists())

    def test_apply_failure_restores_original_noc_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            before = file_hashes(project)
            original_writer = migration.write_feature_archive_indexes

            def fail_indexes(target: Path) -> None:
                raise RuntimeError("forced index failure")

            migration.write_feature_archive_indexes = fail_indexes
            try:
                code, payload = migration.migrate_apply(project, backup=True)
            finally:
                migration.write_feature_archive_indexes = original_writer

            self.assertNotEqual(0, code)
            self.assertEqual("migration_failed", payload["status"])
            self.assertEqual(before, file_hashes(project))
            self.assertEqual("simplified", read_json(project / "noc_docs/.living-docs/config.json")["layout"])
            self.assertTrue((project / ".noc-backups").is_dir())

    def test_rollback_rejects_invalid_backup_id_and_damaged_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = create_simplified_project(Path(tmp))
            invalid = json.loads(run(["migrate", str(project), "--rollback", "../bad", "--json"], check=False).stdout)
            self.assertEqual("invalid_backup_id", invalid["status"])

            applied = json.loads(run(["migrate", str(project), "--to", "feature-archive", "--apply", "--backup", "--json"]).stdout)
            manifest = project / applied["backup_path"] / "manifest.json"
            manifest.write_text("{bad json", encoding="utf-8")
            damaged = json.loads(run(["migrate", str(project), "--rollback", applied["backup_id"], "--json"], check=False).stdout)
            self.assertEqual("invalid_backup_manifest", damaged["status"])


if __name__ == "__main__":
    unittest.main()
