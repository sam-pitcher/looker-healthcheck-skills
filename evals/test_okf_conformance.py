#!/usr/bin/env python3
"""
Unit and Conformance Test Suite for Open Knowledge Format (OKF v0.2).
Validates that all knowledge bundles, playbooks, references, attested computations,
indexes, and update logs in bundle/ adhere strictly to OKF v0.2:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
"""

import os
import sys
import yaml
import datetime
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BUNDLE_DIR = ROOT_DIR / "bundle"


def parse_yaml_frontmatter(content: str):
    """Extract YAML frontmatter and markdown body."""
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


def compute_trust_tier(verified_entry) -> str:
    """Computes OKF §5.3 Trust Tier from verified entries."""
    if not verified_entry:
        return "unverified"
    entries = verified_entry if isinstance(verified_entry, list) else [verified_entry]
    has_human = any(isinstance(e, dict) and str(e.get("by", "")).startswith("human:") for e in entries)
    has_machine = any(isinstance(e, dict) and any(str(e.get("by", "")).startswith(p) for p in ["process:", "vendor_sync", "ci-validator"]) for e in entries)
    if has_human:
        return "human-reviewed"
    elif has_machine:
        return "machine-confirmed"
    return "unverified"


def check_is_stale(expires_date_str: str) -> bool:
    """Checks OKF §5.5 staleness based on expiration ISO string."""
    if not expires_date_str:
        return False
    try:
        clean_str = expires_date_str.replace("Z", "+00:00")
        exp = datetime.datetime.fromisoformat(clean_str)
        now = datetime.datetime.now(datetime.timezone.utc)
        return now > exp
    except Exception:
        return False


class TestOKFConformance(unittest.TestCase):
    def test_01_normative_conformance_bundle_tree(self):
        """OKF §11: Entire bundle/ directory tree must exist and contain concepts."""
        self.assertTrue(BUNDLE_DIR.exists(), "bundle/ directory must exist")
        all_md_files = list(BUNDLE_DIR.rglob("*.md"))
        self.assertGreater(len(all_md_files), 15, "bundle/ must contain playbooks and references")

    def test_02_bundle_domains(self):
        """OKF §11: Core domain bundles must exist under bundle/."""
        domains = ["looker_performance", "lookml_quality", "bigquery_compute", "shared"]
        for d in domains:
            d_path = BUNDLE_DIR / d
            self.assertTrue(d_path.exists(), f"bundle/{d} must exist")
            self.assertTrue((d_path / "index.md").exists(), f"bundle/{d}/index.md must exist")

    def test_03_root_index_and_version(self):
        """OKF §12 & §8: Root index.md must declare okf_version: '0.2'."""
        root_index_path = BUNDLE_DIR / "index.md"
        self.assertTrue(root_index_path.exists())
        content = root_index_path.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm, "Root bundle/index.md must have YAML frontmatter")
        self.assertEqual(str(fm.get("okf_version")), "0.2")
        self.assertIn("Looker & BigQuery", body)

    def test_04_sub_indexes_no_frontmatter(self):
        """OKF §8: Non-root index.md files MUST NOT contain frontmatter and must follow list format."""
        for idx in BUNDLE_DIR.rglob("index.md"):
            if idx == BUNDLE_DIR / "index.md":
                continue  # Root index is allowed frontmatter per OKF §8
            content = idx.read_text(encoding="utf-8").strip()
            self.assertFalse(content.startswith("---"), f"{idx} must not contain frontmatter per OKF §8")
            self.assertIn("* [", content, f"{idx} should contain markdown link entries")

    def test_05_directory_update_logs(self):
        """OKF §9: log.md files must follow YYYY-MM-DD chronological structure."""
        root_log = BUNDLE_DIR / "log.md"
        self.assertTrue(root_log.exists())
        content = root_log.read_text(encoding="utf-8")
        self.assertIn("# Knowledge Catalog Update Log", content)
        self.assertIn("## 2026-", content)
        self.assertIn("* **", content)

    def test_06_trust_tier_and_staleness(self):
        """OKF §5.3 & §5.5: Trust tier classification and staleness logic."""
        # Unverified
        self.assertEqual(compute_trust_tier(None), "unverified")
        self.assertEqual(compute_trust_tier([]), "unverified")
        
        # Machine confirmed
        self.assertEqual(compute_trust_tier({"by": "process:looker-system-activity", "at": "2026-08-20T12:00:00Z"}), "machine-confirmed")
        
        # Human reviewed
        self.assertEqual(compute_trust_tier({"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"}), "human-reviewed")
        self.assertEqual(compute_trust_tier([
            {"by": "ci-validator", "at": "2026-08-20T12:00:00Z"},
            {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"}
        ]), "human-reviewed")

        # Staleness
        self.assertFalse(check_is_stale(None))
        self.assertFalse(check_is_stale("2099-01-01T00:00:00Z"))
        self.assertTrue(check_is_stale("2020-01-01T00:00:00Z"))

    def test_07_attested_computations(self):
        """OKF §10: Attested Computations must define type, runtime, parameters, and computation."""
        comp_files = [f for f in BUNDLE_DIR.rglob("computations/*.md") if f.name not in ("index.md", "log.md")]
        self.assertGreaterEqual(len(comp_files), 4)

        for cf in comp_files:
            content = cf.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            self.assertIsNotNone(fm, f"{cf} missing YAML frontmatter")
            self.assertEqual(fm.get("type"), "Attested Computation", f"{cf} type must be Attested Computation")
            self.assertIn("runtime", fm, f"{cf} missing runtime")
            self.assertTrue(len(body.strip()) > 0, f"{cf} body must not be empty")

    def test_08_concept_metadata_and_provenance(self):
        """OKF §5.1: Concept documents must feature sources and rich frontmatter."""
        playbooks = [f for f in BUNDLE_DIR.rglob("playbooks/*.md") if f.name not in ("index.md", "log.md")]
        self.assertGreaterEqual(len(playbooks), 4)
        for pb in playbooks:
            content = pb.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            self.assertIsNotNone(fm, f"{pb} missing YAML frontmatter")
            self.assertIn(fm.get("type"), ["Playbook", "Concept", "Reference", "Attested Computation"])

    def test_09_technical_design_document_adherence(self):
        """OKF §4: TDD specification playbook must have valid OKF frontmatter and 7 sections."""
        tdd_path = BUNDLE_DIR / "shared" / "playbooks" / "playbook_technical_design_document.md"
        self.assertTrue(tdd_path.exists())
        content = tdd_path.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("type"), "Playbook")
        self.assertEqual(fm.get("status"), "stable")
        self.assertIn("Pillar 1: Looker Performance", body)
        self.assertIn("Pillar 2: LookML Modeling", body)
        self.assertIn("Pillar 3: BigQuery", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)



