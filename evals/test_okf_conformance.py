#!/usr/bin/env python3
"""
Unit and Conformance Test Suite for Open Knowledge Format (OKF v0.2).
Validates that all knowledge bundles, playbooks, references, attested computations,
indexes, update logs, and design documents adhere strictly to OKF v0.2:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.skills_registry import (
    LookerSkillRegistry,
    compute_trust_tier,
    check_is_stale,
    parse_yaml_frontmatter,
    get_skill_content,
    list_registered_skills,
    get_okf_index,
    get_okf_attested_computation,
    validate_okf_knowledge_catalog
)
from agent.tools.storage import save_technical_design_document


class TestOKFConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = LookerSkillRegistry()

    def test_01_normative_conformance_skills_bundle(self):
        """OKF §11: Entire skills/ directory tree must pass 100% OKF v0.2 validation."""
        report = self.registry.validate_okf_conformance("skills")
        self.assertTrue(report["conformant"], f"OKF validation failed with issues: {report.get('issues')}")
        self.assertEqual(report["issues_count"], 0)
        self.assertGreater(report["total_files_audited"], 50)
        self.assertGreater(report["concepts_audited"], 40)
        self.assertGreater(report["index_files_audited"], 5)
        self.assertGreater(report["log_files_audited"], 3)

    def test_02_normative_conformance_custom_bundle(self):
        """OKF §11: Custom healthcheck & refactoring bundles must be 100% compliant."""
        report = self.registry.validate_okf_conformance("skills/custom")
        self.assertTrue(report["conformant"], f"Custom OKF validation failed: {report.get('issues')}")
        self.assertEqual(report["issues_count"], 0)

    def test_03_root_index_and_version(self):
        """OKF §12 & §8: Root index.md must declare okf_version: '0.2'."""
        root_index_path = ROOT_DIR / "skills" / "index.md"
        self.assertTrue(root_index_path.exists())
        content = root_index_path.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("okf_version"), "0.2")
        self.assertIn("# Looker & BigQuery Knowledge Catalog", body)
        self.assertIn("* [Healthcheck Master Skill]", body)

    def test_04_sub_indexes_no_frontmatter(self):
        """OKF §8: Non-root index.md files MUST NOT contain frontmatter and must follow list format."""
        custom_idx = ROOT_DIR / "skills" / "custom" / "index.md"
        self.assertTrue(custom_idx.exists())
        content = custom_idx.read_text(encoding="utf-8")
        self.assertFalse(content.strip().startswith("---"))
        self.assertIn("* [Healthcheck & Optimization]", content)

        pb_idx = ROOT_DIR / "skills" / "custom" / "healthcheck" / "playbooks" / "index.md"
        self.assertTrue(pb_idx.exists())
        pb_content = pb_idx.read_text(encoding="utf-8")
        self.assertFalse(pb_content.strip().startswith("---"))
        self.assertIn("* [Healthcheck Delivery]", pb_content)

    def test_05_directory_update_logs(self):
        """OKF §9: log.md files must follow YYYY-MM-DD chronological structure."""
        root_log = ROOT_DIR / "skills" / "log.md"
        self.assertTrue(root_log.exists())
        content = root_log.read_text(encoding="utf-8")
        self.assertIn("# Knowledge Catalog Update Log", content)
        self.assertIn("## 2026-08-21", content)
        self.assertIn("* **Update**:", content)

    def test_06_trust_tier_computation(self):
        """OKF §5.3: Trust tier classification logic."""
        # Unverified
        self.assertEqual(compute_trust_tier(None), "unverified")
        self.assertEqual(compute_trust_tier([]), "unverified")
        
        # Machine confirmed
        self.assertEqual(compute_trust_tier({"by": "process:looker-system-activity", "at": "2026-08-20T12:00:00Z"}), "machine-confirmed")
        self.assertEqual(compute_trust_tier([{"by": "vendor_sync/v1.0", "at": "2026-08-20T12:00:00Z"}]), "machine-confirmed")
        
        # Human reviewed
        self.assertEqual(compute_trust_tier({"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"}), "human-reviewed")
        self.assertEqual(compute_trust_tier([
            {"by": "process:ci-validator", "at": "2026-08-20T12:00:00Z"},
            {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"}
        ]), "human-reviewed")

    def test_07_staleness_computation(self):
        """OKF §5.5: Staleness check logic."""
        self.assertFalse(check_is_stale(None))
        self.assertFalse(check_is_stale("2099-01-01T00:00:00Z"))
        self.assertTrue(check_is_stale("2020-01-01T00:00:00Z"))

    def test_08_attested_computations(self):
        """OKF §10: Attested Computations must define runtime, parameters, executor, and computation."""
        # 1. Query Latency Breakdown
        ql = self.registry.get_attested_computation("query_latency_breakdown")
        self.assertIsNotNone(ql)
        self.assertEqual(ql["type"], "Attested Computation")
        self.assertEqual(ql["runtime"], "Looker")
        self.assertGreaterEqual(len(ql["parameters"]), 1)
        self.assertIn("query_metrics", ql["body"])
        self.assertEqual(ql["trust_tier"], "human-reviewed")

        # 2. Slot Consumption Timeline
        slots = self.registry.get_attested_computation("slot_consumption_timeline")
        self.assertIsNotNone(slots)
        self.assertEqual(slots["type"], "Attested Computation")
        self.assertEqual(slots["runtime"], "bigquery")
        self.assertIn("INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT", slots["body"])

        # 3. Bytes Billed
        costs = self.registry.get_attested_computation("bytes_billed_by_model")
        self.assertIsNotNone(costs)
        self.assertEqual(costs["runtime"], "bigquery")
        self.assertIn("total_bytes_billed", costs["body"])

        # 4. Table Partitioning DDL
        ddl = self.registry.get_attested_computation("table_partition_ddl")
        self.assertIsNotNone(ddl)
        self.assertEqual(ddl["runtime"], "bigquery")
        self.assertIn("PARTITION BY DATE", ddl["body"])

    def test_09_concept_metadata_and_provenance(self):
        """OKF §5.1: Concept documents must feature sources and rich metadata."""
        perf_pb = self.registry.get_concept("playbook_looker_performance")
        self.assertIsNotNone(perf_pb)
        self.assertEqual(perf_pb["type"], "Playbook")
        self.assertEqual(perf_pb["status"], "stable")
        self.assertEqual(perf_pb["trust_tier"], "human-reviewed")
        self.assertGreaterEqual(len(perf_pb["sources"]), 2)
        self.assertIn("looker", perf_pb["tags"])

    def test_10_technical_design_document_adherence(self):
        """OKF §4: TECHNICAL_DESIGN_DOCUMENT.md must have valid OKF frontmatter and footnotes."""
        tdd_path = ROOT_DIR / "TECHNICAL_DESIGN_DOCUMENT.md"
        self.assertTrue(tdd_path.exists())
        content = tdd_path.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("type"), "Technical Design Document")
        self.assertEqual(fm.get("status"), "stable")
        self.assertEqual(fm.get("verified", {}).get("by"), "human:sampitcher")
        self.assertIn("Pillar 1: Looker Performance", body)
        self.assertIn("[^system-activity-query-metrics]", body)

    def test_11_save_technical_design_document_storage_tool(self):
        """Tests that save_technical_design_document preserves/adds OKF frontmatter."""
        test_tdd = "# Test TDD Body\n\nRemediation content."
        temp_file = "TEST_TDD_OKF.md"
        res = save_technical_design_document(
            tdd_markdown=test_tdd,
            model_name="test-model",
            output_filename=temp_file
        )
        self.assertIn("OKF v0.2", res)
        
        # Verify file written
        p = ROOT_DIR / temp_file
        self.assertTrue(p.exists())
        content = p.read_text(encoding="utf-8")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm)
        self.assertEqual(fm.get("type"), "Technical Design Document")
        self.assertIn("test-model", fm.get("title", ""))
        p.unlink()  # cleanup

    def test_12_progressive_disclosure_tools(self):
        """OKF §8: Tool functions for progressive disclosure."""
        # Root index
        root_idx = get_okf_index()
        self.assertIn("OKF Progressive Disclosure Index", root_idx)
        self.assertIn("Looker & BigQuery Knowledge Catalog", root_idx)

        # Healthcheck index
        hc_idx = get_okf_index("skills/custom/healthcheck")
        self.assertIn("Looker Healthcheck & Performance Knowledge Bundle", hc_idx)

        # Attested computation tool
        comp_output = get_okf_attested_computation("query_latency_breakdown")
        self.assertIn("Attested Computation Contract", comp_output)
        self.assertIn("query_metrics", comp_output)

        # Full catalog validation tool
        report_output = validate_okf_knowledge_catalog("skills")
        self.assertIn("🟢 CONFORMANT (OKF v0.2)", report_output)

    def test_13_concept_graph_engine_and_tools(self):
        """OKF §6, §10, §11: Concept Graph construction, multi-hop traversal, and path finding."""
        from agent.skills_registry import get_okf_concept_graph, find_diagnostic_graph_path

        # 1. Graph construction
        graph = self.registry.build_concept_graph()
        self.assertGreater(graph["total_nodes"], 20)
        self.assertGreater(graph["total_edges"], 50)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)

        # 2. Related concepts traversal
        related = self.registry.get_related_concepts("playbook_looker_performance")
        self.assertGreaterEqual(len(related), 2)
        titles = [r["title"] for r in related]
        self.assertTrue(any("Pipeline Architecture" in t or "Query Outliers" in t or "Delivery Playbook" in t for t in titles))

        # 3. Path finding
        path = self.registry.find_graph_path("playbook_looker_performance", "benchmarks")
        self.assertGreaterEqual(len(path), 2)
        self.assertEqual(path[0], "skills/custom/healthcheck/playbooks/playbook_looker_performance")

        # 4. Agent tools
        global_graph = get_okf_concept_graph()
        self.assertIn("OKF Global Concept Graph Topology", global_graph)
        self.assertIn("graph TD", global_graph)

        sub_graph = get_okf_concept_graph("playbook_looker_performance")
        self.assertIn("OKF Concept Subgraph", sub_graph)

        path_tool = find_diagnostic_graph_path("playbook_looker_performance", "benchmarks")
        self.assertIn("Diagnostic Graph Path", path_tool)

    def test_14_concept_graph_health_audit(self):
        """OKF §6 & §11: Automated Concept Graph Quality and Integrity Audit."""
        from agent.skills_registry import audit_okf_concept_graph

        audit_res = self.registry.audit_concept_graph_health()
        self.assertEqual(audit_res["graph_health_score"], 100)
        self.assertEqual(audit_res["status"], "HEALTHY")
        self.assertEqual(audit_res["broken_links_count"], 0)
        self.assertEqual(audit_res["orphan_nodes_count"], 0)
        self.assertEqual(len(audit_res["attested_computation_issues"]), 0)

        # Critical path tests
        for p in audit_res["critical_path_reachability"]:
            self.assertTrue(p["reachable"], f"Critical path from {p['from']} to {p['to']} is unreachable!")

        # Tool output check
        tool_output = audit_okf_concept_graph()
        self.assertIn("OKF Concept Graph Health Audit: **HEALTHY** (100/100)", tool_output)


if __name__ == "__main__":
    unittest.main(verbosity=2)


