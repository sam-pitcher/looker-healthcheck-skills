#!/usr/bin/env python3
"""
CLI Runner for Looker & BigQuery Healthcheck Skills Evaluation Suite.
Executes:
  1. Transcriber 0-4 scoring rubric benchmarks (evals/fixtures)
  2. LookML quality rules auditor verification
  3. Agent Skills Standard & Manifest conformance tests (skills/)
Outputs structured summary metrics, latency benchmarks, and evaluation status.
"""

import sys
import time
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evals.test_transcriber_scoring import TestTranscriberScoring
from evals.test_skills_conformance import TestSkillsConformance

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_all_evaluations():
    print(f"\n{BOLD}{CYAN}🧪 Looker & BigQuery Healthcheck Skills Evaluation Suite{RESET}\n" + "=" * 70, flush=True)

    suite_classes = [
        ("Layer 1: Transcriber 0–4 Scoring Rubric Benchmarks", TestTranscriberScoring),
        ("Layer 2: Agent Skills Standard & Manifest Conformance", TestSkillsConformance),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    start_time = time.time()

    for suite_name, test_class in suite_classes:
        print(f"\n{BOLD}{suite_name}{RESET}", flush=True)
        print("-" * 70, flush=True)

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)

        for test in suite:
            total_tests += 1
            test_name = test._testMethodName
            t_start = time.time()
            result = unittest.TestResult()
            test.run(result)
            duration = round((time.time() - t_start) * 1000, 2)

            if result.wasSuccessful():
                passed_tests += 1
                print(f"  {GREEN}✔ PASS{RESET}  {test_name:<54} {CYAN}({duration:>6.2f} ms){RESET}", flush=True)
            else:
                failed_tests += 1
                err = result.failures[0][1] if result.failures else (result.errors[0][1] if result.errors else "Unknown error")
                first_line = err.strip().splitlines()[-1]
                print(f"  {RED}✖ FAIL{RESET}  {test_name:<54} {RED}({duration:>6.2f} ms){RESET}", flush=True)
                print(f"        {RED}Error: {first_line}{RESET}", flush=True)

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
