#!/usr/bin/env python3
"""Offline repository validation, not an agent runtime or behavior evaluator.

Uses the standard library. Frontmatter deliberately supports the single-line
string scalars and two-space-indented metadata mapping used by this package,
not all YAML. Unsupported syntax is rejected rather than silently misparsed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_VERSION = "4"
POLICY_METADATA = {
    "mode": "orchestrate-only",
    "head-implementation": "forbidden",
    "worker-routing": "explicit",
    "worker-selection": "cheapest-capable-first",
    "head-tier-workers": "approval-required",
}
SKILL_PATH = Path("skills/lean-orchestrator")
REFERENCES = ("setup-preflight.md", "worker-packet.md", "feedback-loop.md")
REQUIRED = (
    "README.md", "LICENSE", ".gitignore", ".gitattributes",
    ".github/workflows/ci.yml", "scripts/validate.py", "tests/test_contract.py",
)
TOP_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SEMVER = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
TASK_KEYS = (
    "ROLE", "TASK ID", "ROUND", "GOAL", "DEPENDS ON", "BASE", "WORKSPACE",
    "READ SCOPE", "WRITE SCOPE", "GUIDANCE", "SKILLS", "PROCEDURE",
    "CONSTRAINTS", "LIMITS", "VERIFY", "DELIVER", "STOP IF",
)
CORRECTION_KEYS = (
    "ROLE", "TASK ID", "ROUND", "RETAINS", "BASE", "DEFECT", "PROCEDURE",
    "VERIFY", "STOP IF",
)
DISPATCH_KEYS = (
    "TASK ID", "ROUND", "MODEL", "EFFORT", "CANDIDATES", "CONTROL", "ELIGIBILITY",
    "EVIDENCE", "APPROVAL", "LIMITS", "DECISION",
)
REPORT_KEYS = (
    "TASK ID", "ROUND", "STATUS", "BASE", "ARTIFACTS", "CHECKS", "SKILLS USED", "ISSUES",
)
ANCHORS = {
    "SKILL.md": ("role-gate", "economy", "routing", "plan", "budget", "dispatch", "review", "finish"),
    "references/setup-preflight.md": ("discover", "rank", "configure", "dispatch-gate", "evidence", "fallback"),
    "references/worker-packet.md": ("task", "correction", "report"),
    "references/feedback-loop.md": ("states", "example", "edge-cases"),
}


def _scalar(raw: str) -> str:
    """Parse a deliberately restricted YAML string scalar, rejecting other types."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty scalar; use an explicit quoted string if intended")
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid double-quoted string") from exc
        if not isinstance(value, str):
            raise ValueError("Expected a string scalar")
        return value
    if raw.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", raw):
            raise ValueError("Invalid single-quoted string")
        return raw[1:-1].replace("''", "'")
    if raw.endswith(('"', "'")):
        raise ValueError("Unbalanced quotation")
    if (raw[0] in "|>!&*{[?%@`" or re.match(r"^(?:-|:)\s", raw)
            or ": " in raw or re.search(r"\s#", raw)):
        raise ValueError("Unsupported YAML syntax; use a single-line quoted string")
    if raw.lower() in {"true", "false", "null", "~", "yes", "no", "on", "off"}:
        raise ValueError("Non-string YAML scalar must be quoted")
    if re.match(r"^(?:[-+]?\d|[-+]?\.[0-9])", raw):
        raise ValueError("Numeric-looking YAML scalar must be quoted")
    return raw


def parse_frontmatter(content: str) -> dict[str, str | dict[str, str]]:
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Missing opening YAML delimiter (or unexpected BOM)")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing closing YAML delimiter") from exc
    result: dict[str, str | dict[str, str]] = {}
    in_metadata = False
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ValueError("Tabs are unsupported in frontmatter")
        nested = line.startswith(" ")
        if nested:
            if not in_metadata or not line.startswith("  ") or line.startswith("   "):
                raise ValueError("Invalid indentation or nested key outside metadata")
            target = result["metadata"]
            assert isinstance(target, dict)
            line = line[2:]
        else:
            target = result
            in_metadata = False
        match = re.fullmatch(r"([a-zA-Z][a-zA-Z0-9_-]*):(?:\s+(.*))?", line)
        if not match:
            raise ValueError(f"Invalid frontmatter entry: {line!r}")
        key, raw = match.groups()
        if key in target:
            raise ValueError(f"Duplicate frontmatter key: {key}")
        if not nested and key not in TOP_KEYS:
            raise ValueError(f"Unknown top-level field: {key}")
        if not nested and key == "metadata":
            if raw is not None and raw.strip():
                raise ValueError("metadata must be an indented mapping")
            target[key] = {}
            in_metadata = True
        else:
            target[key] = _scalar(raw or "")
    return result


def read_text(path: Path, issues: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(f"Cannot read {path.name}: {exc}")
        return ""


def without_fences(text: str) -> str:
    return re.sub(r"^```[^\n]*\n.*?^```\s*$", "", text, flags=re.M | re.S)


def document_anchors(text: str) -> set[str]:
    text = without_fences(text)
    anchors = set(re.findall(r'<a id="([a-z0-9-]+)"></a>', text))
    # Headings used by ordinary Markdown fragments, including repeated headings.
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.M):
        heading = re.sub(r"[*_`]", "", heading).lower().strip()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        number = counts.get(slug, 0)
        anchors.add(slug if not number else f"{slug}-{number}")
        counts[slug] = number + 1
    return anchors


def check_document(path: Path, boundary: Path, issues: list[str]) -> None:
    text = read_text(path, issues)
    fences = re.findall(r"^```.*$", text, re.M)
    if len(fences) % 2:
        issues.append(f"Unclosed code fence: {path.name}")
    clean = without_fences(text)
    explicit = re.findall(r'<a id="([a-z0-9-]+)"></a>', clean)
    if len(explicit) != len(set(explicit)):
        issues.append(f"Duplicate explicit anchor: {path.name}")
    for href in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", clean):
        try:
            url = urlsplit(href)
        except ValueError:
            issues.append(f"Invalid link in {path.name}: {href}")
            continue
        if url.scheme in {"https", "http", "mailto"}:
            continue  # Offline validation does not claim remote link availability.
        if url.scheme or url.netloc or unquote(url.path).startswith(("/", "\\")):
            issues.append(f"Nonportable link in {path.name}: {href}")
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
        if not target.is_relative_to(boundary.resolve()):
            issues.append(f"Link escapes installation boundary in {path.name}: {href}")
        elif not target.exists():
            issues.append(f"Broken local link in {path.name}: {href}")
        elif url.fragment and target.is_file():
            if unquote(url.fragment) not in document_anchors(read_text(target, issues)):
                issues.append(f"Broken anchor in {path.name}: {href}")


def marked_packet(text: str, marker: str) -> str:
    token = f"<!-- packet: {marker} -->"
    if text.count(token) != 1:
        raise ValueError(f"Expected exactly one packet marker: {marker}")
    following = text.split(token, 1)[1]
    match = re.match(r"\s*```text\n(.*?)\n```", following, re.S)
    if not match:
        raise ValueError(f"Missing text block after packet marker: {marker}")
    return match.group(1)


def parse_packet(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Z][A-Z /-]*):\s*(.*)", line)
        if match:
            key, value = match.groups()
            if key in result:
                raise ValueError(f"Duplicate packet field: {key}")
            result[key] = value
            current = key
        elif line.startswith("  ") and current is not None:
            result[current] += "\n" + line.strip()
        else:
            raise ValueError(f"Invalid packet line: {line!r}")
    return {key: value.strip() for key, value in result.items()}



# Dispatch candidates are *declared* evidence, not actual provider costs or model capability.
# This schema can reject a skipped declared cheaper-capable route, but cannot verify
# model pricing, availability, routing application, or truthfulness of exclusions.
_CANDIDATE_RE = re.compile(
    r"(?P<model>[A-Za-z0-9][A-Za-z0-9._/+:~-]*)@"
    r"(?P<effort>[A-Za-z0-9][A-Za-z0-9._-]*)="
    r"(?P<fit>FIT|TRIAL|EXCLUDED(?:\((?P<reason>[^();]+)\))?)$"
)


def check_candidate_ladder(fields: dict[str, str]) -> list[str]:
    raw = fields.get("CANDIDATES", "").strip()
    if fields.get("DECISION") != "DISPATCH":
        return []
    if not raw:
        return ["CANDIDATES missing; ranked cheaper-first selection is mandatory"]
    entries = [part.strip() for part in raw.split(";")]
    if not all(entries):
        return ["CANDIDATES contains an empty entry"]
    parsed = []
    for entry in entries:
        match = _CANDIDATE_RE.fullmatch(entry)
        if not match:
            return [f"CANDIDATES invalid entry: {entry!r}; expected model@effort=FIT/TRIAL/EXCLUDED(reason)"]
        model, effort, fit, reason = match.group("model", "effort", "fit", "reason")
        if fit.startswith("EXCLUDED"):
            if not reason or len(reason.strip()) < 8:
                return [f"CANDIDATES excluded route {model!r} needs a concrete task-specific reason"]
            if re.search(r"(?i)^(?:less capable|not smart enough|too dumb|better quality|prefer|just safer|not sure)$", reason.strip()):
                return [f"CANDIDATES excluded route {model!r} has a non-specific reason"]
        parsed.append((model, effort, fit))
    models = [(m, e) for m, e, _ in parsed]
    if len(models) != len(set(models)):
        return ["CANDIDATES must not repeat a model/effort pair"]
    selected = (fields.get("MODEL", ""), fields.get("EFFORT", ""))
    if selected not in models:
        return ["CANDIDATES must include the selected MODEL and EFFORT"]
    first = next(((m, e) for m, e, fit in parsed if fit in {"FIT", "TRIAL"}), None)
    if first is None:
        return ["CANDIDATES has no FIT or TRIAL route for DISPATCH"]
    if selected != first:
        return ["CANDIDATES: selected route is not the first cheapest capable FIT/TRIAL candidate"]
    return []

def validate_packet(text: str, kind: str = "task", *, template: bool = False) -> list[str]:
    schemas = {"task": TASK_KEYS, "correction": CORRECTION_KEYS, "report": REPORT_KEYS, "dispatch": DISPATCH_KEYS}
    if kind not in schemas:
        raise ValueError(f"Unknown packet kind: {kind}")
    try:
        fields = parse_packet(text)
    except ValueError as exc:
        return [str(exc)]
    issues = [f"Missing or empty packet field: {key}" for key in schemas[kind] if not fields.get(key)]
    if "ROLE" in schemas[kind] and fields.get("ROLE") != "WORKER":
        issues.append("Packet ROLE must be WORKER")
    if not template:
        if re.search(r"<[^>\n]+>", text):
            issues.append("Concrete packet contains unfilled placeholders")
        if not re.fullmatch(r"[1-9]\d*", fields.get("ROUND", "")):
            issues.append("Packet ROUND must be a positive integer")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", fields.get("TASK ID", "")):
            issues.append("Invalid TASK ID")
        if kind == "report" and fields.get("STATUS") not in {"DONE", "BLOCKED", "FAILED"}:
            issues.append("Invalid worker report STATUS")
        if kind == "dispatch":
            decision = fields.get("DECISION")
            eligibility = fields.get("ELIGIBILITY")
            if decision not in {"DISPATCH", "BLOCK"}:
                issues.append("Invalid dispatch DECISION")
            if eligibility not in {"ECONOMICAL", "EXCEPTION", "UNRESOLVED"}:
                issues.append("Invalid dispatch ELIGIBILITY")
            if decision == "DISPATCH":
                issues.extend(check_candidate_ladder(fields))
                if eligibility == "UNRESOLVED":
                    issues.append("Unresolved eligibility must BLOCK dispatch")
                if eligibility == "EXCEPTION" and fields.get("APPROVAL", "").strip().upper() in {"", "NONE", "PENDING", "NOT REQUESTED"}:
                    issues.append("Exceptional dispatch requires actual prior APPROVAL")
                inherited = {"", "inherit", "inherited", "default", "auto", "head", "same as head", "unknown", "unavailable"}
                if fields.get("MODEL", "").strip().lower() in inherited:
                    issues.append("Dispatch MODEL must be explicit, not inherited or unknown")
                if fields.get("EFFORT", "").strip().lower() in inherited:
                    issues.append("Dispatch EFFORT must be explicit or UNSUPPORTED")
    return issues


def _release_marker(text: str, version: str, name: str, issues: list[str]) -> None:
    matches = re.findall(r"<!-- lean-orchestrator-release: ([^\s]+) -->", text)
    if matches != [version]:
        issues.append(f"Release mismatch in {name}: expected {version}; replace the complete package")


def validate_skill(skill_dir: Path) -> list[str]:
    skill_dir = skill_dir.resolve()
    issues: list[str] = []
    skill = skill_dir / "SKILL.md"
    if not skill.is_file():
        return ["Missing SKILL.md"]
    text = read_text(skill, issues)
    try:
        meta = parse_frontmatter(text)
    except ValueError as exc:
        return issues + [f"Frontmatter: {exc}"]
    name = meta.get("name", "")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        issues.append("Invalid skill name")
    elif name != skill_dir.name:
        issues.append("Skill name must match its directory name")
    for key, maximum, required in (("description", 1024, True), ("compatibility", 500, False)):
        value = meta.get(key)
        if (required or value is not None) and (not isinstance(value, str) or not 1 <= len(value) <= maximum):
            issues.append(f"Invalid {key}: expected a nonempty string of at most {maximum} characters")
    if meta.get("license") != "MIT":
        issues.append("Expected MIT license metadata")
    metadata = meta.get("metadata", {})
    version = metadata.get("version", "") if isinstance(metadata, dict) else ""
    if not re.fullmatch(SEMVER, version):
        issues.append("Missing or invalid metadata.version")
    if not isinstance(metadata, dict) or metadata.get("protocol") != CONTRACT_VERSION:
        issues.append("Protocol mismatch: install matching skill, references, validator, and tests")
    for key, expected in POLICY_METADATA.items():
        if not isinstance(metadata, dict) or metadata.get(key) != expected:
            issues.append(f"Policy metadata mismatch: {key} must be {expected}")
    if len(text.splitlines()) > 500:
        issues.append("SKILL.md exceeds the 500-line context budget")
    license_path = skill_dir / "LICENSE"
    license_text = read_text(license_path, issues)
    if not license_path.resolve().is_relative_to(skill_dir):
        issues.append("Skill license escapes installation boundary")
    if not license_text.startswith("MIT License\n") or "Copyright (c)" not in license_text:
        issues.append("Missing MIT notice in installable skill")
    for relative, anchors in ANCHORS.items():
        path = skill_dir / relative
        if not path.is_file():
            issues.append(f"Missing skill file: {relative}")
            continue
        if not path.resolve().is_relative_to(skill_dir):
            issues.append(f"Skill file escapes installation boundary: {relative}")
        contents = read_text(path, issues)
        if relative != "SKILL.md":
            _release_marker(contents, version, relative, issues)
            if f"]({relative})" not in text:
                issues.append(f"Missing direct skill reference: {relative}")
        for anchor in anchors:
            token = f'<a id="{anchor}"></a>'
            if contents.count(token) != 1:
                issues.append(f"Missing/duplicate protocol section {anchor} in {relative}")
            else:
                section = contents.split(token, 1)[1].split('<a id="', 1)[0]
                if len(section.strip()) < 100:
                    issues.append(f"Empty protocol section {anchor} in {relative}")
        check_document(path, skill_dir, issues)
    if '<a id="role-gate"></a>' in text and '<a id="routing"></a>' in text:
        if text.index('<a id="role-gate"></a>') > text.index('<a id="routing"></a>'):
            issues.append("Role gate must precede routing instructions")
    for filename, markers in (
        ("setup-preflight.md", (("dispatch-template", "dispatch", True),)),
        ("worker-packet.md", (("task-template", "task", True), ("correction-template", "correction", True), ("report-template", "report", True))),
        ("feedback-loop.md", (("example-task", "task", False),)),
    ):
        path = skill_dir / "references" / filename
        if not path.is_file():
            continue
        contents = read_text(path, issues)
        for marker, kind, template in markers:
            try:
                packet = marked_packet(contents, marker)
            except ValueError as exc:
                issues.append(str(exc))
                continue
            issues.extend(f"{marker}: {issue}" for issue in validate_packet(packet, kind, template=template))
    # Check any additional reference documents too, not just the required three.
    for path in skill_dir.rglob("*.md"):
        if str(path.relative_to(skill_dir)).replace("\\", "/") not in ANCHORS:
            if not path.resolve().is_relative_to(skill_dir):
                issues.append(f"Skill file escapes installation boundary: {path.name}")
            check_document(path, skill_dir, issues)
    return issues


def validate(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    issues = [f"Missing repository file: {name}" for name in REQUIRED if not (root / name).is_file()]
    skill_dir = root / SKILL_PATH
    issues.extend(validate_skill(skill_dir))
    if (root / "SKILL.md").exists():
        issues.append("Unexpected duplicate root SKILL.md; the installable skill is under skills/")
    for path in (root / "platforms", root / "docs/platforms.md"):
        if path.exists():
            issues.append("Unexpected vendor-specific configuration bundle")
    root_license = read_text(root / "LICENSE", issues)
    skill_license = read_text(skill_dir / "LICENSE", issues)
    if root_license != skill_license:
        issues.append("Repository and installable skill licenses differ")
    readme_path = root / "README.md"
    if readme_path.is_file():
        readme = read_text(readme_path, issues)
        check_document(readme_path, root, issues)
        try:
            metadata = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8")).get("metadata", {})
            if isinstance(metadata, dict):
                _release_marker(readme, metadata.get("version", ""), "README.md", issues)
        except (OSError, UnicodeError, ValueError):
            pass  # The underlying metadata/read error is already reported.
        sources = re.findall(r"npx skills add ([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) --skill lean-orchestrator", readme)
        if not sources:
            issues.append("README missing a public installation command")
        elif len(set(sources)) != 1:
            issues.append("README installation commands point to different repositories")
        for phrase in ("YOUR_GITHUB_USERNAME", "Once this repository is public", "Before publishing", "When you publish"):
            if phrase.lower() in readme.lower():
                issues.append(f"README contains draft-only wording: {phrase}")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--root", type=Path, help="Validate a complete repository")
    group.add_argument("--skill-dir", type=Path, help="Validate a standalone installed skill")
    args = parser.parse_args(argv)
    issues = validate_skill(args.skill_dir) if args.skill_dir else validate(args.root or ROOT)
    if issues:
        print("Lean Orchestrator validation FAILED:")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("Lean Orchestrator validation PASSED: metadata, portability, release, policy, and packet structure")
    print("Static checks only: no live agents or model-usage measurement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
