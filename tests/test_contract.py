"""Offline structural checks; these do not run or price LLM agents."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_validate", ROOT / "scripts" / "validate.py")
assert spec and spec.loader
validate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_module)

SKILL_DIR = ROOT / "skills" / "lean-orchestrator"
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
PREFLIGHT = (SKILL_DIR / "references" / "setup-preflight.md").read_text(encoding="utf-8")
PACKET = (SKILL_DIR / "references" / "worker-packet.md").read_text(encoding="utf-8")
LOOP = (SKILL_DIR / "references" / "feedback-loop.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_metadata(self):
        metadata = validate_module.parse_frontmatter(SKILL)
        self.assertEqual(metadata["name"], "lean-orchestrator")
        self.assertEqual(metadata["license"], "MIT")
        self.assertEqual(metadata["metadata"], "")
        self.assertLessEqual(len(metadata["description"]), 1024)
        self.assertIn('version: "1.6.0"', SKILL)

    def test_validation_passes(self):
        self.assertEqual(validate_module.validate(), [])

    def test_duplicate_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_module.parse_frontmatter("---\nname: test\nname: another\n---\nbody")

    def test_missing_yaml_delimiter_rejected(self):
        with self.assertRaisesRegex(ValueError, "closing"):
            validate_module.parse_frontmatter("---\nname: test\n")

    def test_self_setup_before_cost_delegation(self):
        self.assertIn("**Self-route before delegating.**", SKILL)
        self.assertIn("Do not merely check whether an existing cheap worker", SKILL)
        self.assertIn("This step is mandatory before cost-driven delegation", SKILL)
        self.assertIn("The user should not have to preconfigure worker models", PREFLIGHT)

    def test_all_setup_modes_explored_in_preferred_order(self):
        routes = ("Per-dispatch route", "Session-scoped route", "Project/user configuration", "No permitted configuration path")
        positions = [SKILL.index(r) for r in routes]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("per-spawn", PREFLIGHT.lower())
        self.assertIn("temporary", PREFLIGHT)

    def test_persistent_config_changes_require_permission(self):
        self.assertIn("only if explicitly authorized", SKILL)
        self.assertIn("minimal reversible changes", SKILL)
        self.assertIn("Never change the head model", PREFLIGHT)
        self.assertIn("reload/restart", PREFLIGHT)

    def test_route_verification_and_honest_cost_accounting(self):
        for status in ("VERIFIED_CHEAPER", "PROVISIONAL_CHEAPER", "SAME_TIER", "UNVERIFIED", "UNAVAILABLE"):
            self.assertIn(status, SKILL)
            self.assertIn(status, PREFLIGHT)
        self.assertIn("Verify the effective route", SKILL)
        self.assertIn("effective worker metadata", PREFLIGHT)
        self.assertIn("Do not invent saved tokens", SKILL)

    def test_worker_skills_and_project_guidance(self):
        for marker in ("PROJECT GUIDANCE:", "REQUIRED SKILLS:", "OPTIONAL SKILLS:", "SKILLS USED:"):
            self.assertIn(marker, SKILL)
            self.assertIn(marker, PACKET)
        self.assertIn("Never assume head-loaded skills are inherited", SKILL)
        self.assertIn("preload", SKILL)

    def test_no_recursive_orchestration(self):
        self.assertIn("No recursive orchestration", SKILL)
        self.assertIn("ROLE: WORKER (never HEAD)", SKILL)
        self.assertIn("No recursive delegation", PACKET)
        self.assertIn("Remove delegation tools", SKILL)

    def test_dependency_review_and_correction(self):
        self.assertIn("ACCEPT", SKILL)
        self.assertIn("REWORK", SKILL)
        self.assertIn("REPLAN", SKILL)
        self.assertIn("BLOCK", SKILL)
        self.assertIn("A1 ROUND 2", LOOP)
        self.assertIn("DISPATCH only after A0 is accepted", LOOP)
        self.assertIn("DEPENDENCIES", SKILL.upper())

    def test_head_usage_optimized_without_bypassing_review(self):
        self.assertIn("head checkpoint", SKILL)
        self.assertIn("never release dependencies until the head approves", SKILL)
        self.assertIn("total expected usage", SKILL)
        self.assertIn("No unnecessary head wake-ups", LOOP)

    def test_workers_are_bounded(self):
        for field in validate_module.TASK_KEYS:
            self.assertIn(field, PACKET)
        for field in validate_module.REPORT_KEYS:
            self.assertIn(field, PACKET)
        self.assertIn("No irreversible external action", PACKET)
        self.assertIn("No redesign", PACKET)

    def test_retry_and_fallback(self):
        self.assertIn("Do not retry an unchanged failing packet", SKILL)
        self.assertIn("No worker spawn or no cheaper routing", SKILL)
        self.assertIn("No worker resume/messaging", SKILL)
        self.assertIn("Model switch needs approval/restart", SKILL)

    def test_installable_skill_is_self_contained(self):
        self.assertTrue((SKILL_DIR / "SKILL.md").is_file())
        self.assertFalse((ROOT / "SKILL.md").exists())
        for name in ("worker-packet.md", "feedback-loop.md", "setup-preflight.md"):
            self.assertTrue((SKILL_DIR / "references" / name).is_file())
            self.assertIn(f"`references/{name}`", SKILL)
        self.assertFalse((SKILL_DIR / ".github").exists())

    def test_no_vendor_config_bundle(self):
        self.assertFalse((ROOT / "platforms").exists())
        self.assertFalse((ROOT / "docs" / "platforms.md").exists())
        self.assertNotIn("Host | Project-scoped directory", README)

    def test_runtime_not_promised_by_skill(self):
        self.assertIn("skill, not a separate model router", README)
        self.assertIn("actual worker spawning", README.lower())
        self.assertIn("host", SKILL)

    def test_publication_ready_readme(self):
        self.assertIn("npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator", README)
        self.assertIn("skills/lean-orchestrator/", README)
        for outdated in ("YOUR_GITHUB_USERNAME", "Once this repository is public", "Upgrading from", "When you publish"):
            self.assertNotIn(outdated, README)
        self.assertIn("Automatic worker routing", README)
        self.assertNotIn("benchmarked savings", README)

    def test_no_external_runtime_requirements(self):
        self.assertFalse((SKILL_DIR / "scripts").exists())
        self.assertTrue((ROOT / "scripts" / "validate.py").is_file())
        self.assertTrue((ROOT / ".github" / "workflows" / "ci.yml").is_file())


if __name__ == "__main__":
    unittest.main()
