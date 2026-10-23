#!/usr/bin/env python3
"""
Agent Skills & Manifest Conformance Test Suite.
Validates that all Agent Skills (SKILL.md) adhere to the Agent Skills Standard,
contain required frontmatter, reference valid assets, and match manifest.yaml.
"""

import sys
import yaml
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def parse_yaml_frontmatter(content: str):
    if not content.strip().startswith("---"):
        return None, content
    parts = content.strip().split("---", 2)
    if len(parts) >= 3:
        try:
            fm = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return fm, body
        except Exception:
            return None, content
    return None, content


class TestSkillsConformance(unittest.TestCase):
    def test_01_manifest_validity(self):
        """Verify manifest.yaml syntax and skill definitions."""
        m_path = ROOT_DIR / "manifest.yaml"
        self.assertTrue(m_path.exists(), "manifest.yaml must exist at root")

        with open(m_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        self.assertEqual(manifest.get("version"), "1.0.0")
        self.assertIn("skills", manifest)
        skills = manifest["skills"]
        self.assertGreaterEqual(len(skills), 4)

        skill_ids = [s["id"] for s in skills]
        self.assertIn("looker-bq-healthcheck", skill_ids)
        self.assertIn("looker-performance-auditor", skill_ids)
        self.assertIn("lookml-quality-auditor", skill_ids)
        self.assertIn("bq-jobs-diagnostics", skill_ids)

        for s in skills:
            self.assertIn("name", s)
            self.assertIn("path", s)
            self.assertIn("entry_point", s)
            entry = ROOT_DIR / s["entry_point"]
            self.assertTrue(entry.exists(), f"Entry point {entry} does not exist for skill {s['id']}")

    def test_02_all_skill_md_frontmatter(self):
        """Verify that every active SKILL.md has valid YAML frontmatter with name and description."""
        skill_files = [f for f in ROOT_DIR.glob("skills/**/SKILL.md") if "vendor" not in str(f)]
        self.assertGreaterEqual(len(skill_files), 4)

        for sf in skill_files:
            content = sf.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            rel = sf.relative_to(ROOT_DIR)

            self.assertIsNotNone(fm, f"{rel} must have YAML frontmatter")
            self.assertIn("name", fm, f"{rel} frontmatter must contain 'name'")
            self.assertIn("description", fm, f"{rel} frontmatter must contain 'description'")
            self.assertTrue(len(fm["name"]) > 0, f"{rel} name must not be empty")
            self.assertTrue(len(fm["description"]) > 10, f"{rel} description must be meaningful (>10 chars)")

            # Check markdown structure
            self.assertIn("# ", body, f"{rel} must have a top-level H1 header")
            self.assertTrue("When to Use" in body or "when to use" in body.lower(), f"{rel} should specify when to use")

    def test_03_skill_scripts_executable(self):
        """Verify that shell scripts and Python tools in skills/ exist and have valid shebangs."""
        sh_scripts = list(ROOT_DIR.glob("skills/**/scripts/*.sh"))
        py_scripts = [f for f in ROOT_DIR.glob("skills/**/scripts/*.py") if "__" not in str(f)]
        
        self.assertGreaterEqual(len(sh_scripts), 3)
        self.assertGreaterEqual(len(py_scripts), 1)

        for script in sh_scripts:
            code = script.read_text(encoding="utf-8")
            self.assertTrue(code.startswith("#!/bin/bash") or code.startswith("#!/usr/bin/env bash"),
                            f"Script {script} missing bash shebang")

        for script in py_scripts:
            code = script.read_text(encoding="utf-8")
            self.assertTrue(code.startswith("#!/usr/bin/env python3") or code.startswith("#!/usr/bin/python3"),
                            f"Script {script} missing python3 shebang")

    def test_04_skill_references_exist(self):
        """Verify that all skills have curated references directory with relevant playbooks."""
        for skill_dir in ["looker-bq-healthcheck", "lookml-quality-auditor", "looker-performance-auditor", "bq-jobs-diagnostics"]:
            ref_dir = ROOT_DIR / "skills" / skill_dir / "references"
            self.assertTrue(ref_dir.exists(), f"References directory missing for {skill_dir}")
            refs = list(ref_dir.glob("*.md"))
            self.assertGreaterEqual(len(refs), 3, f"Skill {skill_dir} must have at least 3 reference documents")


if __name__ == "__main__":
    unittest.main()
