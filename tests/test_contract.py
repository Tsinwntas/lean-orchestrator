"""Offline parser, packaging, and contract regressions; no LLM calls.

Negative tests deliberately damage copies of the package. These establish what
the validator catches, not whether a live agent will obey the instructions.
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lean_validate", ROOT / "scripts/validate.py")
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
SKILL_DIR = ROOT / "skills/lean-orchestrator"
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
PACKET = (SKILL_DIR / "references/worker-packet.md").read_text(encoding="utf-8")
LOOP = (SKILL_DIR / "references/feedback-loop.md").read_text(encoding="utf-8")
EXAMPLE = validator.marked_packet(LOOP, "example-task")
VERSION = validator.parse_frontmatter(SKILL)["metadata"]["version"]
README = (ROOT / "README.md").read_text(encoding="utf-8")
INSTALL_SOURCE = re.search(r"npx skills add ([^ ]+) --skill", README).group(1)
OTHER_SOURCE = "test-fork/lean-orchestrator" if INSTALL_SOURCE != "test-fork/lean-orchestrator" else "another-fork/lean-orchestrator"


class FrontmatterTests(unittest.TestCase):
    def test_actual_metadata_is_parsed_as_strings_and_mapping(self):
        meta = validator.parse_frontmatter(SKILL)
        self.assertEqual(meta["name"], "lean-orchestrator")
        self.assertEqual(meta["metadata"]["protocol"], "4")
        self.assertEqual(meta["metadata"]["worker-selection"], "cheapest-capable-first")
        self.assertRegex(meta["metadata"]["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(validator.CONTRACT_VERSION, "4")

    def test_missing_opening_delimiter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "opening"):
            validator.parse_frontmatter("name: example\n---\n")

    def test_missing_closing_delimiter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "closing"):
            validator.parse_frontmatter("---\nname: example\n")

    def test_duplicate_root_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validator.parse_frontmatter("---\nname: a\nname: b\n---\n")

    def test_duplicate_nested_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validator.parse_frontmatter('---\nmetadata:\n  version: "1.0.0"\n  version: "2.0.0"\n---\n')

    def test_invalid_indentation_is_not_silently_ignored(self):
        for line in (' version: "1"', '   version: "1"', '\tversion: "1"'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                validator.parse_frontmatter(f"---\nmetadata:\n{line}\n---\n")

    def test_nested_key_without_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside metadata"):
            validator.parse_frontmatter('---\nname: a\n  version: "1.0.0"\n---\n')

    def test_unknown_top_level_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            validator.parse_frontmatter("---\nnamme: example\n---\n")

    def test_unbalanced_quotes_are_rejected(self):
        for value in ('"broken', "'broken", 'broken"', "'one' two'"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validator.parse_frontmatter(f"---\nname: {value}\n---\n")

    def test_nonstring_yaml_values_are_rejected(self):
        for value in ('false', 'null', 'yes', '123', '1.2', '0x10', '1e3', '2026-11-12', '[a,b]', '{x: y}', '|'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validator.parse_frontmatter(f"---\nname: {value}\n---\n")

    def test_quoted_strings_preserve_contents(self):
        meta = validator.parse_frontmatter('---\nname: "example"\ndescription: \'It\'\'s a test\'\n---\n')
        self.assertEqual(meta["description"], "It's a test")

    def test_crlf_is_supported(self):
        self.assertEqual(validator.parse_frontmatter(SKILL.replace("\n", "\r\n")), validator.parse_frontmatter(SKILL))

    def test_bom_is_rejected_with_clear_error(self):
        with self.assertRaisesRegex(ValueError, "BOM"):
            validator.parse_frontmatter("\ufeff" + SKILL)

    def test_scalar_metadata_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "mapping"):
            validator.parse_frontmatter('---\nmetadata: "not a map"\n---\n')


class PacketTests(unittest.TestCase):
    def test_templates_are_complete(self):
        for marker, kind in (("task-template", "task"), ("correction-template", "correction"), ("report-template", "report")):
            with self.subTest(marker=marker):
                text = validator.marked_packet(PACKET, marker)
                self.assertEqual(validator.validate_packet(text, kind, template=True), [])

    def test_concrete_example_is_valid(self):
        self.assertEqual(validator.validate_packet(EXAMPLE), [])

    def test_each_required_task_field_is_enforced(self):
        fields = validator.parse_packet(EXAMPLE)
        for key in validator.TASK_KEYS:
            with self.subTest(key=key):
                mutated = "\n".join(f"{k}: {v}" for k, v in fields.items() if k != key)
                # Re-indent multiline values for the text packet format.
                mutated = re.sub(r"\n(?![A-Z][A-Z /-]*:)([^\n]+)", r"\n  \1", mutated)
                issues = validator.validate_packet(mutated)
                self.assertTrue(any(key in issue for issue in issues), issues)

    def test_empty_scope_is_rejected(self):
        bad = re.sub(r"^WRITE SCOPE:.*$", "WRITE SCOPE:", EXAMPLE, flags=re.M)
        self.assertTrue(any("WRITE SCOPE" in issue for issue in validator.validate_packet(bad)))

    def test_duplicate_fields_are_rejected(self):
        self.assertTrue(any("Duplicate" in issue for issue in validator.validate_packet(EXAMPLE + "\nTASK ID: A2")))

    def test_worker_role_cannot_be_head(self):
        self.assertTrue(any("ROLE" in issue for issue in validator.validate_packet(EXAMPLE.replace("ROLE: WORKER", "ROLE: HEAD"))))

    def test_attempt_number_must_be_positive(self):
        for number in ("0", "-1", "one", "1.5", "01"):
            with self.subTest(number=number):
                issues = validator.validate_packet(EXAMPLE.replace("ROUND: 1", f"ROUND: {number}"))
                self.assertTrue(any("ROUND" in issue for issue in issues))

    def test_actual_packet_cannot_contain_unfilled_template(self):
        issues = validator.validate_packet(EXAMPLE.replace("TASK ID: A0", "TASK ID: <assign later>"))
        self.assertTrue(any("placeholders" in issue for issue in issues))

    def test_report_status_is_not_acceptance(self):
        report = 'TASK ID: A0\nROUND: 1\nSTATUS: DONE\nBASE: v1\nARTIFACTS: NONE\nCHECKS: NOT RUN; no tool\nSKILLS USED: NONE\nISSUES: validation pending'
        self.assertEqual(validator.validate_packet(report, "report"), [])
        issues = validator.validate_packet(report.replace("STATUS: DONE", "STATUS: ACCEPTED"), "report")
        self.assertTrue(any("STATUS" in issue for issue in issues))

    def test_text_before_fields_is_rejected(self):
        self.assertTrue(validator.validate_packet("unstructured preface\n" + EXAMPLE))

    def test_missing_and_duplicate_markers_are_rejected(self):
        for text in ("nothing", PACKET + "\n<!-- packet: task-template -->"):
            with self.subTest(text=text[:30]), self.assertRaises(ValueError):
                validator.marked_packet(text, "task-template")


class DispatchRecordTests(unittest.TestCase):
    """Validate declared decisions, not whether host controls are really applied."""

    def record(self, **changes):
        fields = {
            "TASK ID": "A0", "ROUND": "1", "MODEL": "worker-small",
            "EFFORT": "low", "CANDIDATES": "worker-small@low=FIT; worker-mid@medium=FIT",
            "CONTROL": "Explicit host model and effort arguments",
            "ELIGIBILITY": "ECONOMICAL",
            "EVIDENCE": "Supported lower worker tier; execution requested only; quota unknown",
            "APPROVAL": "NONE", "LIMITS": "One active attempt; 8 tool calls",
            "DECISION": "DISPATCH",
        }
        fields.update(changes)
        return "\n".join(f"{k}: {v}" for k, v in fields.items())

    def test_explicit_economical_record_passes(self):
        self.assertEqual(validator.validate_packet(self.record(), "dispatch"), [])

    def test_dispatch_template_has_every_required_field(self):
        text = (SKILL_DIR / "references/setup-preflight.md").read_text(encoding="utf-8")
        self.assertEqual(validator.validate_packet(validator.marked_packet(text, "dispatch-template"), "dispatch", template=True), [])

    def test_every_dispatch_field_is_required(self):
        for key in validator.DISPATCH_KEYS:
            with self.subTest(key=key):
                issues = validator.validate_packet(self.record(**{key: ""}), "dispatch")
                self.assertTrue(any(key in issue for issue in issues), issues)

    def test_model_inheritance_is_rejected(self):
        for model in ("inherit", "default", "head", "same as head", "unknown", "auto"):
            with self.subTest(model=model):
                issues = validator.validate_packet(self.record(MODEL=model), "dispatch")
                self.assertTrue(any("MODEL" in issue for issue in issues), issues)

    def test_effort_inheritance_is_rejected(self):
        for effort in ("inherit", "default", "head", "unknown"):
            with self.subTest(effort=effort):
                issues = validator.validate_packet(self.record(EFFORT=effort), "dispatch")
                self.assertTrue(any("EFFORT" in issue for issue in issues), issues)

    def test_unsupported_effort_control_can_be_disclosed(self):
        self.assertEqual(validator.validate_packet(self.record(EFFORT="UNSUPPORTED", CANDIDATES="worker-small@UNSUPPORTED=FIT", EVIDENCE="Explicit model selected; host exposes no effort control"), "dispatch"), [])

    def test_head_tier_exception_without_approval_fails(self):
        for approval in ("NONE", "PENDING", "NOT REQUESTED"):
            with self.subTest(approval=approval):
                issues = validator.validate_packet(self.record(ELIGIBILITY="EXCEPTION", APPROVAL=approval), "dispatch")
                self.assertTrue(any("APPROVAL" in issue for issue in issues), issues)

    def test_scoped_exception_approval_can_be_recorded(self):
        record = self.record(ELIGIBILITY="EXCEPTION", APPROVAL="User explicitly authorized this model for A0 only")
        self.assertEqual(validator.validate_packet(record, "dispatch"), [])

    def test_unresolved_route_cannot_dispatch(self):
        issues = validator.validate_packet(self.record(ELIGIBILITY="UNRESOLVED"), "dispatch")
        self.assertTrue(any("BLOCK" in issue for issue in issues), issues)

    def test_unavailable_route_can_record_a_block(self):
        record = self.record(MODEL="UNAVAILABLE", EFFORT="UNAVAILABLE", CANDIDATES="NONE (no enabled worker model)", ELIGIBILITY="UNRESOLVED", DECISION="BLOCK")
        self.assertEqual(validator.validate_packet(record, "dispatch"), [])

    def test_unknown_decision_is_rejected(self):
        issues = validator.validate_packet(self.record(DECISION="TRY ANYWAY"), "dispatch")
        self.assertTrue(any("DECISION" in issue for issue in issues), issues)

    def test_unknown_eligibility_is_rejected(self):
        issues = validator.validate_packet(self.record(ELIGIBILITY="PROBABLY FINE"), "dispatch")
        self.assertTrue(any("ELIGIBILITY" in issue for issue in issues), issues)



class CheapestCapableRoutingTests(unittest.TestCase):
    """Validates declared cheaper-first choices without claiming to know real cost."""

    def record(self, *, candidate_list="worker-tiny@low=FIT; worker-mid@medium=FIT", model="worker-tiny", effort="low", **changes):
        fields = {
            "TASK ID": "A0", "ROUND": "1", "MODEL": model, "EFFORT": effort,
            "CANDIDATES": candidate_list, "CONTROL": "Explicit host routing",
            "ELIGIBILITY": "ECONOMICAL", "EVIDENCE": "Documented provisional lower-tier ordering; actual quota unknown",
            "APPROVAL": "NONE", "LIMITS": "1 attempt, 8 calls", "DECISION": "DISPATCH",
        }
        fields.update(changes)
        return "\n".join(f"{key}: {val}" for key, val in fields.items())

    def test_cheapest_fit_is_selected(self):
        self.assertEqual(validator.validate_packet(self.record(), "dispatch"), [])

    def test_skipping_cheaper_fit_for_comfort_is_rejected(self):
        errors = validator.validate_packet(self.record(model="worker-mid", effort="medium"), "dispatch")
        self.assertTrue(any("first cheapest capable" in error for error in errors), errors)

    def test_cheap_eligible_trial_takes_precedence(self):
        self.assertEqual(validator.validate_packet(self.record(candidate_list="worker-tiny@low=TRIAL; worker-mid@medium=FIT"), "dispatch"), [])
        errors = validator.validate_packet(self.record(candidate_list="worker-tiny@low=TRIAL; worker-mid@medium=FIT", model="worker-mid", effort="medium"), "dispatch")
        self.assertTrue(any("first cheapest capable" in error for error in errors), errors)

    def test_concrete_exclusion_allows_next_qualified_worker(self):
        sample = self.record(candidate_list="worker-tiny@low=EXCLUDED(required compiler unavailable); worker-mid@medium=FIT", model="worker-mid", effort="medium")
        self.assertEqual(validator.validate_packet(sample, "dispatch"), [])

    def test_generic_exclusion_is_rejected(self):
        for why in ("not smart enough", "better quality", "prefer", "just safer"):
            with self.subTest(why=why):
                sample = self.record(candidate_list=f"worker-tiny@low=EXCLUDED({why}); worker-mid@medium=FIT", model="worker-mid", effort="medium")
                self.assertTrue(any("CANDIDATES" in error for error in validator.validate_packet(sample, "dispatch")))

    def test_missing_candidate_list_is_rejected(self):
        errors = validator.validate_packet(self.record(CANDIDATES=""), "dispatch")
        self.assertTrue(any("CANDIDATES" in error for error in errors))

    def test_selected_must_appear_in_candidates(self):
        errors = validator.validate_packet(self.record(model="worker-unknown"), "dispatch")
        self.assertTrue(any("selected MODEL" in error for error in errors), errors)

    def test_duplicate_model_effort_is_rejected(self):
        errors = validator.validate_packet(self.record(candidate_list="worker-tiny@low=FIT; worker-tiny@low=FIT"), "dispatch")
        self.assertTrue(any("repeat" in error for error in errors), errors)

    def test_excluded_candidate_requires_reason(self):
        errors = validator.validate_packet(self.record(candidate_list="worker-tiny@low=EXCLUDED; worker-mid@medium=FIT", model="worker-mid", effort="medium"), "dispatch")
        self.assertTrue(any("CANDIDATES" in error for error in errors), errors)

    def test_no_candidate_with_fit_or_trial_blocks_dispatch(self):
        errors = validator.validate_packet(self.record(candidate_list="worker-tiny@low=EXCLUDED(missing required editor)"), "dispatch")
        self.assertTrue(any("no FIT or TRIAL" in error for error in errors), errors)

    def test_unknown_candidate_status_is_rejected(self):
        errors = validator.validate_packet(self.record(candidate_list="worker-tiny@low=MAYBE"), "dispatch")
        self.assertTrue(any("invalid entry" in error for error in errors), errors)

    def test_user_model_syntax_remains_generic(self):
        sample = self.record(candidate_list="host/model-v1@low=FIT; local/model-v2@UNSUPPORTED=FIT", model="host/model-v1", effort="low")
        self.assertEqual(validator.validate_packet(sample, "dispatch"), [])

    def test_selection_policy_required_in_metadata(self):
        self.assertEqual(validator.POLICY_METADATA["worker-selection"], "cheapest-capable-first")

    def test_task_specific_reason_and_tier_policy_in_core(self):
        core = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Mandatory cheapest-first check", core)
        self.assertIn("no cheaper", (SKILL_DIR / "references/setup-preflight.md").read_text(encoding="utf-8"))


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        self.skill = self.root / "skills/lean-orchestrator"

    def mutate(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assertIssue(self, phrase: str) -> None:
        issues = validator.validate(self.root)
        self.assertTrue(any(phrase in issue for issue in issues), issues)

    def test_each_role_policy_metadata_value_is_required(self):
        path = self.skill / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        for key, expected in validator.POLICY_METADATA.items():
            with self.subTest(key=key):
                path.write_text(original.replace(f'  {key}: "{expected}"\n', ""), encoding="utf-8")
                self.assertIssue(f"Policy metadata mismatch: {key}")
        path.write_text(original, encoding="utf-8")

    def test_permissive_head_implementation_metadata_is_rejected(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", '  head-implementation: "forbidden"', '  head-implementation: "allowed-for-small-tasks"')
        self.assertIssue("Policy metadata mismatch: head-implementation")

    def test_missing_dispatch_gate_is_rejected(self):
        self.mutate("skills/lean-orchestrator/references/setup-preflight.md", '<a id="dispatch-gate"></a>', "")
        self.assertIssue("protocol section dispatch-gate")

    def test_missing_dispatch_approval_field_is_rejected(self):
        self.mutate("skills/lean-orchestrator/references/setup-preflight.md", "APPROVAL:", "APPROVL:")
        self.assertIssue("APPROVAL")

    def test_reference_symlink_outside_skill_is_rejected(self):
        path = self.skill / "references/setup-preflight.md"
        external = Path(self.temp.name) / "outside.md"
        external.write_bytes(path.read_bytes())
        path.unlink()
        try:
            path.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not supported in this environment")
        self.assertIssue("Skill file escapes installation boundary")

    def test_fork_can_change_install_source_without_changing_validator(self):
        path = self.root / "README.md"
        path.write_text(path.read_text().replace(INSTALL_SOURCE, OTHER_SOURCE))
        self.assertEqual(validator.validate(self.root), [])

    def test_inconsistent_install_sources_are_rejected(self):
        self.mutate("README.md", INSTALL_SOURCE, OTHER_SOURCE)
        self.assertIssue("different repositories")

    def test_whole_repository_passes(self):
        self.assertEqual(validator.validate(self.root), [])

    def test_skill_only_copy_has_no_repository_dependency(self):
        destination = Path(self.temp.name) / "standalone/lean-orchestrator"
        shutil.copytree(self.skill, destination)
        shutil.rmtree(self.root)
        self.assertEqual(validator.validate_skill(destination), [])
        self.assertFalse((destination / "scripts").exists())
        self.assertFalse((destination / ".github").exists())

    def test_skill_only_without_references_fails(self):
        shutil.rmtree(self.skill / "references")
        self.assertIssue("Missing skill file")

    def test_missing_each_required_repository_file_fails(self):
        for relative in validator.REQUIRED:
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.unlink()
                self.assertIssue("Missing repository file")
                path.write_bytes(original)

    def test_missing_skill_file_fails(self):
        (self.skill / "SKILL.md").unlink()
        self.assertIssue("Missing SKILL.md")

    def test_empty_description_fails(self):
        path = self.skill / "SKILL.md"
        path.write_text(re.sub(r"^description:.*$", 'description: ""', path.read_text(), flags=re.M))
        self.assertIssue("Invalid description")

    def test_oversized_metadata_fails(self):
        for field, maximum in (("description", 1024), ("compatibility", 500)):
            with self.subTest(field=field):
                path = self.skill / "SKILL.md"
                original = path.read_text()
                path.write_text(re.sub(rf"^{field}:.*$", f'{field}: "' + "x" * (maximum + 1) + '"', original, flags=re.M))
                self.assertIssue(f"Invalid {field}")
                path.write_text(original)

    def test_invalid_name_fails(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", "name: lean-orchestrator", "name: invalid--name")
        self.assertIssue("Invalid skill name")

    def test_name_must_match_directory(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", "name: lean-orchestrator", "name: different-name")
        self.assertIssue("directory name")

    def test_missing_version_fails(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", f'  version: "{VERSION}"\n', "")
        self.assertIssue("metadata.version")

    def test_protocol_mismatch_has_actionable_error(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", '  protocol: "4"', '  protocol: "2"')
        self.assertIssue("Protocol mismatch")

    def test_old_reference_release_is_rejected(self):
        self.mutate("skills/lean-orchestrator/references/setup-preflight.md", f"release: {VERSION}", "release: 0.0.0")
        self.assertIssue("Release mismatch")

    def test_legacy_reference_without_marker_is_rejected(self):
        self.mutate("skills/lean-orchestrator/references/setup-preflight.md", f"<!-- lean-orchestrator-release: {VERSION} -->", "")
        self.assertIssue("Release mismatch")

    def test_old_readme_release_is_rejected(self):
        self.mutate("README.md", f"release: {VERSION}", "release: 0.0.0")
        self.assertIssue("Release mismatch")

    def test_broken_local_reference_is_rejected(self):
        self.mutate("README.md", "](LICENSE)", "](MISSING.md)")
        self.assertIssue("Broken local link")

    def test_link_outside_installable_skill_is_rejected(self):
        path = self.skill / "SKILL.md"
        path.write_text(path.read_text() + "\n[not portable](../../README.md)\n")
        self.assertIssue("escapes installation boundary")

    def test_percent_encoded_escape_is_rejected(self):
        path = self.skill / "SKILL.md"
        path.write_text(path.read_text() + "\n[escape](%2e%2e/%2e%2e/README.md)\n")
        self.assertIssue("escapes installation boundary")

    def test_absolute_and_file_links_are_rejected(self):
        path = self.skill / "SKILL.md"
        original = path.read_text()
        for href in ("/tmp/a.md", "file:///tmp/a.md", "C:/temp/a.md", "//host/share"):
            with self.subTest(href=href):
                path.write_text(original + f"\n[bad]({href})\n")
                self.assertIssue("Nonportable link")
        path.write_text(original)

    def test_valid_anchor_and_missing_anchor_are_distinguished(self):
        path = self.skill / "SKILL.md"
        original = path.read_text()
        path.write_text(original + "\n[role](#role-gate)\n")
        self.assertEqual(validator.validate(self.root), [])
        path.write_text(original + "\n[bad](#missing-anchor)\n")
        self.assertIssue("Broken anchor")

    def test_duplicate_anchor_is_rejected(self):
        path = self.skill / "SKILL.md"
        path.write_text(path.read_text() + '\n<a id="role-gate"></a>\n')
        self.assertIssue("Duplicate explicit anchor")

    def test_heading_rewording_does_not_break_validation(self):
        path = self.skill / "SKILL.md"
        original = path.read_text()
        changed, count = re.subn(r'(<a id="routing"></a>\n)##[^\n]+', r'\1## An alternative heading', original)
        self.assertEqual(count, 1)
        path.write_text(changed)
        self.assertEqual(validator.validate(self.root), [])

    def test_missing_role_gate_is_rejected(self):
        self.mutate("skills/lean-orchestrator/SKILL.md", '<a id="role-gate"></a>', "")
        self.assertIssue("protocol section role-gate")

    def test_empty_protocol_section_is_rejected(self):
        path = self.skill / "SKILL.md"
        text = re.sub(r'(<a id="budget"></a>).*?(?=<a id="dispatch">)', r'\1\n## Budget\n', path.read_text(), flags=re.S)
        path.write_text(text)
        self.assertIssue("Empty protocol section budget")

    def test_unclosed_code_fence_is_rejected(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n```text\nunfinished\n")
        self.assertIssue("Unclosed code fence")

    def test_missing_skill_license_is_rejected(self):
        (self.skill / "LICENSE").unlink()
        self.assertIssue("Missing MIT notice")

    def test_divergent_license_is_rejected(self):
        path = self.skill / "LICENSE"
        path.write_text(path.read_text() + "\nA deliberately different notice.\n")
        self.assertIssue("licenses differ")

    def test_invalid_utf8_is_reported_without_crash(self):
        (self.skill / "references/worker-packet.md").write_bytes(b"\xff\xfe")
        self.assertIssue("Cannot read")

    def test_copy_paste_packet_corruption_is_rejected(self):
        self.mutate("skills/lean-orchestrator/references/worker-packet.md", "WRITE SCOPE:", "WRTE SCOPE:")
        self.assertIssue("WRITE SCOPE")

    def test_duplicate_root_skill_is_rejected(self):
        (self.root / "SKILL.md").write_text(SKILL)
        self.assertIssue("duplicate root SKILL.md")

    def test_public_readme_has_no_owner_setup_placeholder(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\nOnce this repository is public\n")
        self.assertIssue("draft-only wording")

    def test_cli_works_from_an_unrelated_working_directory(self):
        result = subprocess.run([sys.executable, str(self.root / "scripts/validate.py")], cwd=self.temp.name, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_has_nonzero_status_for_broken_package(self):
        (self.skill / "references/setup-preflight.md").unlink()
        result = subprocess.run([sys.executable, str(self.root / "scripts/validate.py")], text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_supports_standalone_skill_validation(self):
        result = subprocess.run([sys.executable, str(self.root / "scripts/validate.py"), "--skill-dir", str(self.skill)], text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_workflow_uses_pinned_actions_and_read_only_access(self):
        workflow = (self.root / ".github/workflows/ci.yml").read_text()
        pins = re.findall(r"uses:\s+([^\s#]+)", workflow)
        self.assertEqual(len(pins), 2)
        self.assertTrue(all(re.fullmatch(r"actions/[a-z-]+@[a-f0-9]{40}", pin) for pin in pins))
        self.assertRegex(workflow, r"permissions:\s*\n\s+contents: read")
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("timeout-minutes: 5", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
