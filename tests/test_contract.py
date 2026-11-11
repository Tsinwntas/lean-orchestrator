"""Offline checks for the static Lean Orchestrator repository contract."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_validate", ROOT / "scripts" / "validate.py")
assert spec and spec.loader
validate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_module)


class SkillContractTests(unittest.TestCase):
    def test_metadata(self):
        metadata = validate_module.parse_frontmatter((ROOT / "skills" / "lean-orchestrator" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(metadata["name"], "lean-orchestrator")
        self.assertEqual(metadata["license"], "MIT")
        self.assertEqual(metadata["metadata"], "")
        self.assertLessEqual(len(metadata["description"]), 1024)

    def test_validation_passes(self):
        self.assertEqual(validate_module.validate(), [])

    def test_duplicate_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_module.parse_frontmatter("---\nname: test\nname: another\n---\nbody")

    def test_missing_yaml_delimiter_rejected(self):
        with self.assertRaisesRegex(ValueError, "closing"):
            validate_module.parse_frontmatter("---\nname: test\n")

    def test_feedback_loop_has_review_before_next_task(self):
        walkthrough = (ROOT / "skills" / "lean-orchestrator" / "references" / "feedback-loop.md").read_text(encoding="utf-8")
        self.assertIn("A0 acceptance", walkthrough)
        self.assertIn("A1 ROUND 2", walkthrough)
        self.assertIn("A2", walkthrough)

    def test_worker_skill_propagation_and_root_only(self):
        skill = (ROOT / "skills" / "lean-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
        packet = (ROOT / "skills" / "lean-orchestrator" / "references" / "worker-packet.md").read_text(encoding="utf-8")
        for item in ("PROJECT GUIDANCE:", "REQUIRED SKILLS:", "OPTIONAL SKILLS:", "SKILLS USED:"):
            self.assertIn(item, skill)
            self.assertIn(item, packet)
        self.assertIn("Root-only orchestration", skill)
        # A portable skill must forbid recursive delegation independently of host configuration.
        self.assertIn("No subdelegation", skill)
    def test_installable_skill_is_self_contained(self):
        skill_dir = ROOT / "skills" / "lean-orchestrator"
        self.assertTrue((skill_dir / "SKILL.md").is_file())
        self.assertFalse((ROOT / "SKILL.md").exists())
        for name in ("worker-packet.md", "feedback-loop.md", "setup-preflight.md"):
            self.assertTrue((skill_dir / "references" / name).is_file())
        self.assertFalse((skill_dir / ".github").exists())

    def test_no_vendor_specific_configuration_bundle(self):
        self.assertFalse((ROOT / "platforms").exists())
        self.assertFalse((ROOT / "docs" / "platforms.md").exists())
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Host | Project-scoped directory", text)
        self.assertNotIn("Platform | Example", text)

    def test_skill_uses_runtime_discovery_not_hardcoded_models(self):
        skill = (ROOT / "skills" / "lean-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Discover available worker types", skill)
        self.assertIn("Root-only orchestration", skill)
        self.assertIn("REQUIRED SKILLS:", skill)

    def test_routing_preflight_statuses(self):
        skill = (ROOT / "skills" / "lean-orchestrator" / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("VERIFIED_CHEAPER", "SAME_TIER", "UNVERIFIED", "UNAVAILABLE"):
            self.assertIn(marker, skill)
        self.assertIn("do not delegate solely to save tokens", skill)

    def test_readme_install_is_publication_ready(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator", readme)
        self.assertIn("skills/lean-orchestrator/", readme)
        self.assertNotIn("Once this repository is public", readme)
        self.assertNotIn("Upgrading from", readme)
        self.assertNotIn("When you publish", readme)

    def test_readme_has_no_owner_placeholder(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("YOUR_GITHUB_USERNAME", readme)
        self.assertIn("npx skills add Tsinwntas/lean-orchestrator --skill lean-orchestrator", readme)



if __name__ == "__main__":
    unittest.main()
