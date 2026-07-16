from __future__ import annotations

import unittest
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.noclib import layouts
from scripts.noclib import schemas


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/noc.py"


def run_noc(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def file_hashes(project: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        if path.is_file():
            hashes[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def write_feature_archive_project(project: Path, *, feature_id: str = "user-login") -> None:
    (project / "noc_docs/.living-docs").mkdir(parents=True)
    (project / "noc_docs/features" / feature_id).mkdir(parents=True)
    (project / "AGENTS.md").write_text(
        "# Agent Protocol\n\n<!-- noc-living-docs:start -->\n\n## NOC\n\n<!-- noc-living-docs:end -->\n",
        encoding="utf-8",
    )
    for name in ["project.md", "guardrails.md", "verification.md"]:
        (project / "noc_docs" / name).write_text(f"# {name}\n", encoding="utf-8")
    (project / "noc_docs/.living-docs/config.json").write_text(
        json.dumps(
            {
                "protocol": "noc-living-docs",
                "protocol_version": 2,
                "layout": "feature-archive",
                "layout_version": "1.0",
                "documentation_root": "noc_docs",
                "language": "zh-CN",
                "machine_keys": "en-US",
                "feature_id_style": "ascii-kebab-case",
                "routing": {
                    "high_confidence": 0.78,
                    "medium_confidence": 0.55,
                    "ambiguity_delta": 0.12,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "noc_docs/features" / feature_id / "overview.md").write_text(
        "---\n"
        f"id: {feature_id}\n"
        "name: 用户登录\n"
        "status: active\n"
        "schema_version: 1\n"
        "created_at: 2026-07-16\n"
        "updated_at: 2026-07-16\n"
        "language: zh-CN\n"
        "---\n\n"
        "# 用户登录\n",
        encoding="utf-8",
    )


class FeatureArchiveSchemaTests(unittest.TestCase):
    def test_feature_archive_config_schema_accepts_required_shape(self) -> None:
        payload = {
            "protocol": "noc-living-docs",
            "protocol_version": 2,
            "layout": "feature-archive",
            "layout_version": "1.0",
            "documentation_root": "noc_docs",
            "language": "zh-CN",
            "machine_keys": "en-US",
            "feature_id_style": "ascii-kebab-case",
            "routing": {
                "high_confidence": 0.78,
                "medium_confidence": 0.55,
                "ambiguity_delta": 0.12,
            },
        }

        self.assertEqual([], schemas.validate_config_schema(payload))

    def test_feature_archive_config_schema_rejects_missing_layout_version(self) -> None:
        payload = {
            "protocol": "noc-living-docs",
            "protocol_version": 2,
            "layout": "feature-archive",
            "documentation_root": "noc_docs",
            "language": "zh-CN",
            "machine_keys": "en-US",
        }

        self.assertIn("layout_version is required", schemas.validate_config_schema(payload))

    def test_overview_frontmatter_requires_ascii_kebab_id(self) -> None:
        payload = {
            "id": "用户登录",
            "name": "用户登录",
            "status": "active",
            "schema_version": 1,
            "created_at": "2026-07-16",
            "updated_at": "2026-07-16",
            "language": "zh-CN",
        }

        self.assertIn("id must be ASCII kebab-case", schemas.validate_overview_frontmatter(payload))

    def test_patch_schema_rejects_passed_result_without_zero_exit_code(self) -> None:
        payload = {
            "schema_version": "1.0",
            "feature_id": "user-login",
            "source": {"actor": "codex-skill"},
            "patch": {
                "verification_result": {
                    "command": "python -m unittest",
                    "cwd": ".",
                    "started_at": "2026-07-16T10:00:00+08:00",
                    "finished_at": "2026-07-16T10:00:01+08:00",
                    "exit_code": 1,
                    "result": "passed",
                    "scope": "用户登录",
                    "output_summary": "failed",
                }
            },
        }

        self.assertIn(
            "verification_result passed requires exit_code 0",
            schemas.validate_feature_patch_payload(payload),
        )

    def test_evidence_schema_rejects_passed_result_without_zero_exit_code(self) -> None:
        payload = {
            "schema_version": "1.0",
            "code_evidence": {
                "mode": "staged",
                "changed_paths": ["src/auth/login.py"],
                "diff_summary": {"files_changed": 1, "insertions": 1, "deletions": 0},
                "commit": None,
                "signals": [],
            },
            "verification_evidence": [
                {
                    "command": "python -m unittest",
                    "cwd": ".",
                    "started_at": "2026-07-16T10:00:00+08:00",
                    "finished_at": "2026-07-16T10:00:01+08:00",
                    "exit_code": 2,
                    "result": "passed",
                    "scope": "用户登录",
                    "output_summary": "error",
                }
            ],
        }

        self.assertIn(
            "verification_evidence[0] passed requires exit_code 0",
            schemas.validate_evidence_payload(payload),
        )


class FeatureArchiveLayoutDetectionTests(unittest.TestCase):
    def write_config(self, project: Path, payload: dict) -> None:
        config = project / "noc_docs/.living-docs/config.json"
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def test_detect_layout_recognizes_simplified_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_config(
                project,
                {
                    "protocol": "noc-living-docs",
                    "protocol_version": 2,
                    "layout": "simplified",
                    "documentation_root": "noc_docs",
                },
            )

            info = layouts.detect_layout(project)

            self.assertTrue(layouts.is_simplified_v2(info))
            self.assertEqual(2, info.protocol_version)
            self.assertEqual("simplified", info.layout)
            self.assertEqual("1.0", info.layout_version)

    def test_detect_layout_recognizes_feature_archive_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_config(
                project,
                {
                    "protocol": "noc-living-docs",
                    "protocol_version": 2,
                    "layout": "feature-archive",
                    "layout_version": "1.0",
                    "documentation_root": "noc_docs",
                },
            )

            info = layouts.detect_layout(project)

            self.assertTrue(layouts.is_feature_archive_v2(info))
            self.assertEqual("feature-archive", info.layout)
            self.assertEqual("1.0", info.layout_version)

    def test_detect_layout_recognizes_v1_small(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_config(
                project,
                {
                    "protocol": "noc-living-docs",
                    "version": "0.1.0",
                    "documentation_root": "noc_docs",
                    "mode": "small",
                },
            )

            info = layouts.detect_layout(project)

            self.assertTrue(layouts.is_v1_small(info))
            self.assertEqual(1, info.protocol_version)
            self.assertEqual("small", info.layout)
            self.assertEqual("small", info.mode)

    def test_detect_layout_recognizes_v1_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_config(
                project,
                {
                    "protocol": "noc-living-docs",
                    "version": "0.1.0",
                    "documentation_root": "noc_docs",
                    "mode": "domain",
                },
            )

            info = layouts.detect_layout(project)

            self.assertTrue(layouts.is_v1_domain(info))
            self.assertEqual(1, info.protocol_version)
            self.assertEqual("domain", info.layout)
            self.assertEqual("domain", info.mode)


class FeatureArchiveValidateTests(unittest.TestCase):
    def test_validate_accepts_feature_archive_layout_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_feature_archive_project(project)
            before = file_hashes(project)

            result = run_noc(["validate", "--target", str(project)])

            self.assertEqual("NOC project validation passed.\n", result.stdout)
            self.assertEqual(before, file_hashes(project))

    def test_validate_rejects_invalid_overview_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_feature_archive_project(project, feature_id="用户登录")

            result = run_noc(["validate", "--target", str(project)], check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("id must be ASCII kebab-case", result.stdout)


if __name__ == "__main__":
    unittest.main()
