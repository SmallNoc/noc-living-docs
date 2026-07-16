"""Feature archive Markdown helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


ZH_CN_OVERVIEW_SECTIONS = [
    "功能目标",
    "已确认需求",
    "当前实现",
    "重要约束",
    "代码范围",
    "验证方式",
    "最近验证结果",
    "最近重大变更",
    "待确认事项",
]


def default_overview_sections(language: str) -> list[str]:
    if language == "zh-CN":
        return ZH_CN_OVERVIEW_SECTIONS.copy()
    return [
        "Feature Goal",
        "Confirmed Requirements",
        "Current Implementation",
        "Important Constraints",
        "Code Scope",
        "Verification Method",
        "Recent Verification Results",
        "Recent Major Changes",
        "Pending Questions",
    ]


def parse_frontmatter_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, Any] = {}
    index = 1
    while index < len(lines):
        line = lines[index]
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith(" "):
            index += 1
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        value = raw.strip()
        if value:
            data[key] = int(value) if value.isdigit() else value
            index += 1
            continue
        items: list[str] = []
        probe = index + 1
        while probe < len(lines):
            child = lines[probe]
            if child.startswith("  - "):
                items.append(child[4:].strip())
                probe += 1
                continue
            break
        data[key] = items
        index = probe
    return data


def parse_frontmatter_file(path: Path) -> dict[str, Any]:
    return parse_frontmatter_text(path.read_text(encoding="utf-8"))


def markdown_language_from_existing(paths: list[Path]) -> str:
    chinese = 0
    latin = 0
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        chinese += sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        latin += sum(1 for char in text if "A" <= char <= "z")
    if chinese > latin:
        return "zh-CN"
    return "en-US"
