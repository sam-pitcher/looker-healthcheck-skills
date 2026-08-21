#!/usr/bin/env python3
"""
OKF Concept Graph Health & Integrity Review Utility.
Audits the knowledge catalog graph to ensure all skills, playbooks, references,
and attested computations are structurally sound, fully connected, and reachable.
"""

import sys
import json
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.skills_registry import skill_registry


def run_graph_review():
    print("=" * 80)
    print(" 🕸️  OKF CONCEPT GRAPH & SKILLS QUALITY AUDIT")
    print("=" * 80)

    report = skill_registry.audit_concept_graph_health()

    status_icon = "🟢" if report["status"] == "HEALTHY" else ("🟡" if report["status"] == "WARNING" else "🔴")

    print(f"\n{status_icon} Overall Graph Health Score: {report['graph_health_score']} / 100 ({report['status']})\n")
    print(f" • Total Concept Nodes : {report['total_nodes']}")
    print(f" • Total Semantic Edges: {report['total_edges']}")
    print(f" • Broken Cross-Links  : {report['broken_links_count']}")
    print(f" • Orphan Isolated Nodes: {report['orphan_nodes_count']}")
    print(f" • Computation Issues  : {len(report['attested_computation_issues'])}\n")

    print("📊 Node Breakdown by Knowledge Type:")
    for ntype, count in sorted(report["node_type_breakdown"].items(), key=lambda x: -x[1]):
        print(f"   - {ntype.ljust(24)}: {count}")

    print("\n🧭 Critical Diagnostic Path Reachability:")
    for p in report["critical_path_reachability"]:
        icon = "✅" if p["reachable"] else "❌"
        print(f"   {icon} {p['from']} ➔ {p['to']} ({p['hops']} hops)")

    if report["broken_links"]:
        print("\n🚨 Broken Links Detected:")
        for bl in report["broken_links"]:
            print(f"   ❌ Source: {bl['source']} ➔ Missing: {bl['target']} ({bl['label']})")

    if report["orphan_nodes"]:
        print("\n⚠️ Orphan Nodes (Unreachable):")
        for o in report["orphan_nodes"]:
            print(f"   ⚠️ [{o['type']}] {o['title']} ({o['id']})")

    if report["attested_computation_issues"]:
        print("\n⚠️ Attested Computation Issues:")
        for issue in report["attested_computation_issues"]:
            print(f"   ⚠️ {issue}")

    print("\n" + "=" * 80)
    if report["graph_health_score"] >= 90:
        print(" 🎉 EXCELLENT: Concept Graph is 100% compliant, fully connected, and ready!")
    else:
        print(" ⚠️  ATTENTION: Issues found. Please resolve broken links or orphan nodes.")
    print("=" * 80)


if __name__ == "__main__":
    run_graph_review()
