#!/usr/bin/env python3
"""Dependency-free structural validation for Lean Orchestrator.

This intentionally checks the restricted frontmatter shape used in this repo,
not the entire YAML language or model/runtime behavior.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "skills/lean-orchestrator/SKILL.md",
    "README.md",
    "LICENSE",
    "skills/lean-orchestrator/references/feedback-loop.md",
    "skills/lean-orchestrator/references/worker-packet.md",
    "skills/lean-orchestrator/references/setup-preflight.md",
    ".github/workflows/ci.yml",
)
TASK_KEYS = (
    "TASK ID:",
    "ROUND:",
    "GOAL:",
    "EXECUTOR ROUTE:",
    "DEPENDS ON:",
    "INPUTS:",
    "PROJECT GUIDANCE:",
    "REQUIRED SKILLS:",
    "OPTIONAL SKILLS:",
    "WRITE SCOPE:",
    "PROCEDURE:",
    "CONSTRAINTS:",
    "VERIFY:",
    "DELIVER:",
    "STOP IF:",
    "ROLE:",
)
REPORT_KEYS = ("TASK ID:", "ROUND:", "STATUS:", "CHANGED:", "CHECKS:", "SKILLS USED:", "ISSUES:")


def parse_frontmatter(content: str) -> dict[str, str]:
    """Read simple top-level scalar YAML keys; fails closed for missing delimiters."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing opening YAML delimiter")
    try:
        stop = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing closing YAML delimiter") from exc
    fields: dict[str, str] = {}
    for line in lines[1:stop]:
        if not line.strip() or line.lstrip().startswith("#") or line[0].isspace():
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*", line)
        if not match:
            raise ValueError(f"Invalid top-level frontmatter: {line!r}")
        key, raw = match.groups()
        if key in fields:
            raise ValueError(f"Duplicate frontmatter key: {key}")
        fields[key] = raw.strip('"\'')
    return fields


def validate(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    if (root / "platforms").exists():
        issues.append("Vendor-specific configuration directory is not part of the generic repository")
    for relative in REQUIRED:
        if not (root / relative).is_file():
            issues.append(f"Missing file: {relative}")
    skill_file = root / "skills/lean-orchestrator/SKILL.md"
    if not skill_file.is_file():
        return issues
    skill = skill_file.read_text(encoding="utf-8")
    try:
        meta = parse_frontmatter(skill)
    except ValueError as exc:
        issues.append(f"Frontmatter: {exc}")
        return issues
    name = meta.get("name", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        issues.append("Invalid skill name: must use lowercase letters, digits, and single hyphens (max 64)")
    if name != skill_file.parent.name:
        issues.append("Skill name must match the containing folder")
    description = meta.get("description", "")
    if not (1 <= len(description) <= 1024):
        issues.append("Skill description must be between 1 and 1024 characters")
    if len(meta.get("compatibility", "")) > 500:
        issues.append("Skill compatibility must be at most 500 characters")
    if meta.get("license") != "MIT":
        issues.append("Skill license metadata must match repository MIT license")
    license_file = root / "LICENSE"
    if license_file.is_file() and "MIT License" not in license_file.read_text(encoding="utf-8"):
        issues.append("LICENSE file does not appear to contain the MIT license")
    packet = (root / "skills/lean-orchestrator/references/worker-packet.md")
    if packet.is_file():
        packet_text = packet.read_text(encoding="utf-8")
        for key in TASK_KEYS:
            if key not in packet_text:
                issues.append(f"Packet template missing required field: {key}")
        for key in REPORT_KEYS:
            if key not in skill:
                issues.append(f"Skill lacks report field: {key}")
    for word in ("ACCEPT", "REWORK", "REPLAN", "BLOCK", "D0", "L1", "L2", "L3"):
        if word not in skill:
            issues.append(f"Skill missing protocol marker: {word}")
    for marker in ("VERIFIED_CHEAPER", "PROVISIONAL_CHEAPER", "SAME_TIER", "UNVERIFIED", "UNAVAILABLE", "Automatic capability and routing setup"):
        if marker not in skill:
            issues.append(f"Skill missing worker-routing preflight marker: {marker}")
    # Core behavioral contracts: cheap workers must be configured when allowed,
    # not merely discovered. This is static checking, not runtime enforcement.
    for marker in (
        "Per-dispatch route", "Session-scoped route", "Project/user configuration",
        "Verify the effective route", "Do not merely check", "head model",
        "No recursive orchestration", "No worker spawn", "project skills",
        "head checkpoint", "total expected", "REWORK", "STOP IF:",
    ):
        if marker.lower() not in skill.lower():
            issues.append(f"Skill missing orchestration contract: {marker}")
    for phrase in ("explicitly authorized", "restart", "permissions"):
        if phrase.lower() not in skill.lower():
            issues.append(f"Skill missing safe auto-configuration condition: {phrase}")
    for filename in (
        "skills/lean-orchestrator/SKILL.md",
        "skills/lean-orchestrator/references/setup-preflight.md",
        "skills/lean-orchestrator/references/worker-packet.md",
        "skills/lean-orchestrator/references/feedback-loop.md",
    ):
        content = (root / filename).read_text(encoding="utf-8") if (root / filename).is_file() else ""
        # Vendor-neutral core behavior; optional installer tooling in README is different.
        for vendor in ("codex", "claude", "kimi", "anthropic", "openai", "gemini"):
            if re.search(r"\b" + re.escape(vendor) + r"\b", content, re.IGNORECASE):
                issues.append(f"Vendor-specific reference in {filename}: {vendor}")
    # These references must work after a skill-only installation.
    for relative in ("references/worker-packet.md", "references/feedback-loop.md", "references/setup-preflight.md"):
        if not (skill_file.parent / relative).is_file():
            issues.append(f"Broken portable skill reference: {relative}")
        if f"`{relative}`" not in skill:
            issues.append(f"Skill does not link to portable reference: {relative}")
    readme = root / "README.md"
    if readme.is_file():
        contents = readme.read_text(encoding="utf-8")
        if "Tsinwntas/lean-orchestrator" not in contents:
            issues.append("README missing canonical public installation path")
        forbidden = (
            "YOUR_GITHUB_USERNAME", "Once this repository is public", "Upgrading from",
            "Replace the username", "Before publishing", "When you publish",
        )
        for phrase in forbidden:
            if phrase.lower() in contents.lower():
                issues.append(f"README contains draft/publishing-only instruction: {phrase}")
        for path in ("CHANGELOG.md", "CONTRIBUTING.md", "docs/architecture.md"):
            if f"]({path})" in contents:
                issues.append(f"README links to a removed file: {path}")
    return issues


def main() -> int:
    issues = validate()
    if issues:
        print("Lean Orchestrator validation FAILED:")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("Lean Orchestrator validation PASSED: metadata, layout, and task/report contract")
    print("Note: this is static validation; it does not execute real agent orchestration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
