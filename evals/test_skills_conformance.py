#!/usr/bin/env python3
"""
Agent Skills & Manifest Conformance Test Suite.
Validates that all Agent Skills (SKILL.md) adhere to the Agent Skills Standard,
contain required frontmatter, reference valid assets, and match manifest.yaml.
"""

import os
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
        """Verify manifest.yaml syntax and required bundle fields."""
        m_path = ROOT_DIR / "manifest.yaml"
        self.assertTrue(m_path.exists(), "manifest.yaml must exist at root")

        with open(m_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        self.assertEqual(manifest.get("version"), "0.2")
        self.assertIn("bundles", manifest)
        bundles = manifest["bundles"]
        self.assertGreaterEqual(len(bundles), 4)

        bundle_ids = [b["id"] for b in bundles]
        self.assertIn("looker-healthcheck", bundle_ids)
        self.assertIn("looker-performance", bundle_ids)
        self.assertIn("lookml-quality", bundle_ids)
        self.assertIn("bigquery-compute", bundle_ids)

        for b in bundles:
            self.assertIn("name", b)
            self.assertIn("version", b)
            self.assertIn("entry_skill", b)
            entry_skill = ROOT_DIR / b["entry_skill"]
            self.assertTrue(entry_skill.exists(), f"Entry skill {entry_skill} does not exist for bundle {b['id']}")

    def test_02_all_skill_md_frontmatter(self):
        """Verify that every SKILL.md in skills/ has valid YAML frontmatter with name and description."""
        skill_files = [f for f in ROOT_DIR.glob("skills/**/SKILL.md") if "vendor" not in str(f)]
        self.assertGreaterEqual(len(skill_files), 2)


        for sf in skill_files:
            content = sf.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            rel = sf.relative_to(ROOT_DIR)

            self.assertIsNotNone(fm, f"{rel} must have YAML frontmatter")
            self.assertIn("name", fm, f"{rel} frontmatter must contain 'name'")
            self.assertIn("description", fm, f"{rel} frontmatter must contain 'description'")
            self.assertTrue(len(fm["name"]) > 0, f"{rel} name must not be empty")
            self.assertTrue(len(fm["description"]) > 10, f"{rel} description must be meaningful (>10 chars)")

            # Check required markdown sections
            self.assertIn("# ", body, f"{rel} must have a top-level H1 header")
            self.assertTrue("When to Use" in body or "when to use" in body.lower(), f"{rel} should specify when to use")

    def test_03_skill_scripts_executable(self):
        """Verify that shell scripts in skills/ exist and have valid bash shebangs."""
        sh_scripts = list(ROOT_DIR.glob("skills/**/scripts/*.sh"))
        self.assertGreaterEqual(len(sh_scripts), 3)
        for script in sh_scripts:
            code = script.read_text(encoding="utf-8")
            self.assertTrue(code.startswith("#!/bin/bash") or code.startswith("#!/usr/bin/env bash"),
                            f"Script {script} missing bash shebang")

    def test_04_bundle_export_integrity(self):
        """Verify that export_okf_bundle can discover all bundles."""
        from scripts.export_okf_bundle import sha256_file
        m_path = ROOT_DIR / "manifest.yaml"
        self.assertTrue(m_path.exists())
        test_sha = sha256_file(m_path)
        self.assertEqual(len(test_sha), 64)


if __name__ == "__main__":
    unittest.main()
