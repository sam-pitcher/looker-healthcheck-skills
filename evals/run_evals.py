#!/usr/bin/env python3
"""
Comprehensive CLI Runner for Looker Healthcheck Multi-Agent Evaluation Suite.
Executes deterministic tool tests, Transcriber 0-4 scoring rubric, and agent trajectories.
Outputs structured summary metrics, latency benchmarks, and evaluation status.
"""

import sys
import time
import json
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evals.test_tools import (
    test_pillar1_subsystem_and_project_discovery,
    test_pillar2_lookml_modeling_hygiene,
    test_pillar3_bigquery_and_compute,
    test_dynamic_cli_discovery_and_guardrails,
    test_one_click_consolidated_benchmark,
    test_model_scoping_behavior,
    test_dual_layer_storage,
    test_telemetry_tracer
)
from evals.test_transcriber_scoring import (
    test_score_0_antipattern_eval,
    test_score_4_exceptional_eval
)
from evals.eval_agent_trajectories import (
    test_trajectory_complete_30_check_healthcheck,
    test_trajectory_model_scoped_investigation,
    test_trajectory_performance_outlier_triage,
    test_trajectory_lookml_quality_and_henry,
    test_trajectory_dynamic_skill_resolution
)

from evals.test_okf_conformance import TestOKFConformance

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_all_evaluations():
    print(f"\n{BOLD}{CYAN}🧪 Looker & BigQuery Optimization Multi-Agent Evaluation Suite{RESET}\n" + "=" * 70, flush=True)

    okf_test = TestOKFConformance()
    okf_test.setUpClass()

    test_suites = [
        ("Layer 1: Deterministic Tool & Healthcheck Audits", [
            ("Pillar 1: Subsystem & Project Discovery", test_pillar1_subsystem_and_project_discovery),
            ("Pillar 2: LookML Modeling Hygiene", test_pillar2_lookml_modeling_hygiene),
            ("Pillar 3: BigQuery & Compute Layout", test_pillar3_bigquery_and_compute),
            ("Dynamic CLI Discovery & Guardrails", test_dynamic_cli_discovery_and_guardrails),
            ("One-Click Consolidated Benchmark", test_one_click_consolidated_benchmark),
            ("Dynamic Model Scoping Execution", test_model_scoping_behavior),
            ("Dual-Layer Persistence & History", test_dual_layer_storage),
            ("TelemetryTracer Profiling & Spans", test_telemetry_tracer),
        ]),
        ("Layer 2: Transcriber 0–4 Scoring Rubric Benchmarks", [
            ("Score 0 Anti-Pattern Fixture Audit (< 1.5)", test_score_0_antipattern_eval),
            ("Score 4 Exceptional Fixture Audit (>= 3.5)", test_score_4_exceptional_eval),
        ]),
        ("Layer 3: Agent Trajectory & Multi-Step Reasoning Scenarios", [
            ("Scenario 1: 30-Check Full Execution & Report Save", test_trajectory_complete_30_check_healthcheck),
            ("Scenario 2: Model-Scoped Investigation Routing", test_trajectory_model_scoped_investigation),
            ("Scenario 3: Performance Outlier Triage & Benchmark", test_trajectory_performance_outlier_triage),
            ("Scenario 4: LookML Quality & Dead Code Vacuum Routing", test_trajectory_lookml_quality_and_henry),
            ("Scenario 5: Dynamic Skills Registry & Playbook Lookup", test_trajectory_dynamic_skill_resolution),
        ]),
        ("Layer 4: Open Knowledge Format (OKF v0.2) Conformance Suite", [
            ("OKF §11 Normative Conformance (skills/ Tree)", okf_test.test_01_normative_conformance_skills_bundle),
            ("OKF §11 Custom Knowledge Bundles (custom/)", okf_test.test_02_normative_conformance_custom_bundle),
            ("OKF §12 & §8 Bundle Root & Sub-Index Hierarchy", lambda: (okf_test.test_03_root_index_and_version(), okf_test.test_04_sub_indexes_no_frontmatter())),
            ("OKF §9 Directory Update Log Audit", okf_test.test_05_directory_update_logs),
            ("OKF §5.3 & §5.5 Trust Tiers & Staleness Engine", lambda: (okf_test.test_06_trust_tier_computation(), okf_test.test_07_staleness_computation())),
            ("OKF §10 Attested Computations Contract & Runtimes", okf_test.test_08_attested_computations),
            ("OKF §5.1 Concept Metadata & Provenance Sources", okf_test.test_09_concept_metadata_and_provenance),
            ("OKF Technical Design Document (TDD) Adherence", okf_test.test_10_technical_design_document_adherence),
            ("OKF Progressive Disclosure & Tool Integration", lambda: (okf_test.test_11_save_technical_design_document_storage_tool(), okf_test.test_12_progressive_disclosure_tools())),
        ])
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    start_time = time.time()
    results = []

    for suite_name, tests in test_suites:
        print(f"\n{BOLD}{suite_name}{RESET}", flush=True)
        print("-" * 70, flush=True)
        for test_title, test_func in tests:
            total_tests += 1
            t_start = time.time()
            try:
                test_func()
                duration = round((time.time() - t_start) * 1000, 2)
                passed_tests += 1
                results.append({"name": test_title, "status": "PASSED", "duration_ms": duration})
                print(f"  {GREEN}✔ PASS{RESET}  {test_title:<54} {CYAN}({duration:>6.2f} ms){RESET}", flush=True)
            except Exception as e:
                duration = round((time.time() - t_start) * 1000, 2)
                failed_tests += 1
                results.append({"name": test_title, "status": "FAILED", "duration_ms": duration, "error": str(e)})
                print(f"  {RED}✖ FAIL{RESET}  {test_title:<54} {RED}({duration:>6.2f} ms){RESET}", flush=True)
                print(f"        {RED}Error: {e}{RESET}", flush=True)

    total_duration = round((time.time() - start_time), 2)
    pass_rate = round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0

    print("\n" + "=" * 70, flush=True)
    print(f"{BOLD}📊 EVALUATION SUMMARY SCORECARD:{RESET}", flush=True)
    print(f"  • Total Test Cases:   {total_tests}", flush=True)
    print(f"  • Passed:             {GREEN}{passed_tests}{RESET}", flush=True)
    print(f"  • Failed:             {RED if failed_tests > 0 else GREEN}{failed_tests}{RESET}", flush=True)
    print(f"  • Pass Rate:          {GREEN if pass_rate >= 90 else YELLOW}{pass_rate}%{RESET}", flush=True)
    print(f"  • Total Time:         {total_duration}s", flush=True)
    print("=" * 70 + "\n", flush=True)

    if failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_all_evaluations()
