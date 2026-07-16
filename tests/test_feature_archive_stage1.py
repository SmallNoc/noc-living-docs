from __future__ import annotations

import unittest

from scripts.noclib import schemas


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


if __name__ == "__main__":
    unittest.main()
