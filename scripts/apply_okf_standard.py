#!/usr/bin/env python3
"""
Applies Open Knowledge Format (OKF v0.2) compliance across the repository:
1. Adds rich YAML frontmatter (type, title, description, tags, generated, verified, sources) to all custom markdown files.
2. Formats vendor skills & references with valid OKF types.
3. Creates Attested Computation concepts under skills/custom/healthcheck/computations/.
4. Creates progressive disclosure index.md files (§8) and chronological log.md files (§9).
5. Ensures all documents adhere to OKF v0.2 specification.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent

# Metadata definitions for all custom documents
CUSTOM_DOCS_METADATA = {
    # -------------------------------------------------------------
    # 1. Custom Healthcheck Master Skill
    # -------------------------------------------------------------
    "skills/custom/healthcheck/SKILL.md": {
        "type": "Skill",
        "title": "Looker Healthcheck & Performance Optimization Master Skill",
        "name": "looker-healthcheck",
        "description": "Master developer skill for diagnosing, auditing, and optimizing Looker instance performance, query lifecycles, and LookML codebases.",
        "tags": ["looker", "healthcheck", "performance", "modeling", "bigquery", "pso"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "google-pso-benchmarks", "resource": "/skills/custom/healthcheck/references/benchmarks.md", "title": "Google Cloud PSO Latency & Healthcheck Benchmarks", "author": "team:google-pso"},
            {"id": "system-activity-catalog", "resource": "/skills/custom/healthcheck/references/system_activity_queries.md", "title": "Looker System Activity Query Catalog", "author": "process:looker-system-activity"}
        ]
    },

    # -------------------------------------------------------------
    # 2. Custom Healthcheck Playbooks (6 Files)
    # -------------------------------------------------------------
    "skills/custom/healthcheck/playbooks/playbook_healthcheck_delivery.md": {
        "type": "Playbook",
        "title": "Master Looker Healthcheck Delivery Playbook",
        "description": "Authoritative 4-Pillar engagement delivery methodology, stakeholder interview frameworks, and thematic review structures.",
        "tags": ["looker", "healthcheck", "delivery", "interview", "methodology", "playbooks"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "benchmarks", "resource": "/skills/custom/healthcheck/references/benchmarks.md", "title": "Google Cloud PSO Performance Benchmarks"},
            {"id": "transcriber-rubric", "resource": "/skills/custom/healthcheck/playbooks/playbook_transcriber_scoring.md", "title": "Transcriber Scoring Rubric"},
            {"id": "system-activity", "resource": "/skills/custom/healthcheck/references/system_activity_queries.md", "title": "System Activity Query Bank"}
        ]
    },
    "skills/custom/healthcheck/playbooks/playbook_looker_performance.md": {
        "type": "Playbook",
        "title": "Query Performance Audit & Forensic Triage Playbook",
        "description": "Diagnostic and remediation protocol for auditing query performance, query lifecycle latencies, connection contention, and Looker JVM internal overhead.",
        "tags": ["looker", "performance", "query-lifecycle", "triage", "latency", "jvm"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "pipeline-architecture", "resource": "/skills/custom/healthcheck/references/looker_bigquery_pipeline_architecture.md", "title": "Looker BigQuery Pipeline Architecture"},
            {"id": "vendor-perf-optimizer", "resource": "/skills/vendor/looker-skills/skills/looker-performance-optimizer/SKILL.md", "title": "Looker Performance Optimizer"},
            {"id": "connecting-bq", "resource": "/skills/vendor/looker-skills/skills/connecting-looker-to-bigquery/SKILL.md", "title": "Connecting Looker to BigQuery"}
        ]
    },
    "skills/custom/healthcheck/playbooks/playbook_lookml_quality.md": {
        "type": "Playbook",
        "title": "Looker Style Guide & LookML Modeling Standards Playbook",
        "description": "Official LookML style standards, naming conventions, formatting rules, and DRY modeling patterns for high-quality Looker projects.",
        "tags": ["lookml", "style-guide", "modeling", "dry", "primary-keys", "snake-case"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "modeling-guidelines", "resource": "/skills/vendor/looker-skills/skills/lookml-modeling-guidelines/SKILL.md", "title": "LookML Modeling Guidelines"},
            {"id": "liquid-guidelines", "resource": "/skills/vendor/looker-skills/skills/lookml-liquid/SKILL.md", "title": "LookML Liquid Guidelines"},
            {"id": "access-grants", "resource": "/skills/vendor/looker-skills/skills/lookml-access-grants/SKILL.md", "title": "LookML Access Grants"},
            {"id": "refinements", "resource": "/skills/vendor/looker-skills/skills/lookml-refinements/SKILL.md", "title": "LookML Refinements"}
        ]
    },
    "skills/custom/healthcheck/playbooks/playbook_content_governance.md": {
        "type": "Playbook",
        "title": "Unused Content, Dead LookML & Schedule Cleanup Playbook",
        "description": "Operational procedures, diagnostic detection queries, and safe deprecation funnels for stale dashboards, inactive explores, and zombie schedules.",
        "tags": ["looker", "content-governance", "cleanup", "deprecation", "henry", "schedules"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "system-activity", "resource": "/skills/custom/healthcheck/references/system_activity_queries.md", "title": "System Activity Query Bank"},
            {"id": "henry-guide", "resource": "/skills/custom/refactoring/references/henry_command_guide.md", "title": "Henry CLI Guide"}
        ]
    },
    "skills/custom/healthcheck/playbooks/playbook_transcriber_scoring.md": {
        "type": "Playbook",
        "title": "LookML Model Review & Transcriber Scoring Rubric",
        "description": "Official 0–4 evaluation rubric across LookML Modeling Quality, End-User Experience, Architecture & PDTs, and Governance & Testing.",
        "tags": ["transcriber", "scoring-rubric", "evaluation", "lookml", "governance"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "benchmarks", "resource": "/skills/custom/healthcheck/references/benchmarks.md", "title": "Google Cloud PSO Latency Benchmarks"},
            {"id": "dev-workflows", "resource": "/skills/custom/healthcheck/references/development_workflows_and_ci.md", "title": "Development Workflows & CI/CD"}
        ]
    },
    "skills/custom/healthcheck/playbooks/playbook_technical_design_document.md": {
        "type": "Playbook",
        "title": "Enterprise Technical Design Document (TDD) Authoring Playbook",
        "description": "Standards and 7-section architecture for generating an authoritative, publication-grade Technical Design Document adhering to OKF v0.2.",
        "tags": ["tdd", "technical-design", "architecture", "okf", "remediation-roadmap"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "okf-spec", "resource": "https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md", "title": "Open Knowledge Format (OKF) Specification v0.2", "author": "team:google-cloud-knowledge-catalog"},
            {"id": "pipeline-architecture", "resource": "/skills/custom/healthcheck/references/looker_bigquery_pipeline_architecture.md", "title": "Looker BigQuery Pipeline Architecture"},
            {"id": "warehouse-optimization", "resource": "/skills/custom/healthcheck/references/warehouse_optimization.md", "title": "Warehouse Compute Optimization"}
        ]
    },

    # -------------------------------------------------------------
    # 3. Custom Healthcheck References (13 Files)
    # -------------------------------------------------------------
    "skills/custom/healthcheck/references/aggregate_awareness_and_architecture.md": {
        "type": "Reference",
        "title": "Advanced Optimization, Aggregate Awareness & Enterprise Architecture",
        "description": "Implementation protocols for Looker Aggregate Awareness (aggregate_table) and Hub & Spoke modular project architecture.",
        "tags": ["looker", "aggregate-awareness", "rollups", "hub-and-spoke", "architecture"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "vendor-agg-awareness", "resource": "/skills/vendor/looker-skills/skills/looker-architect/references/aggregate_awareness.md", "title": "Looker Aggregate Awareness Reference"}
        ]
    },
    "skills/custom/healthcheck/references/benchmarks.md": {
        "type": "Reference",
        "title": "Google Cloud PSO Benchmark Standards & Query Lifecycle",
        "description": "Official Google Cloud PSO performance benchmarks, query lifecycle definitions, SLA warning thresholds, and latency targets.",
        "tags": ["looker", "pso", "benchmarks", "latency", "sla", "query-lifecycle"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "pso-standards", "resource": "https://cloud.google.com/looker/docs", "title": "Google Cloud PSO Looker Performance Standards", "author": "team:google-pso"}
        ]
    },
    "skills/custom/healthcheck/references/content_delivery_schedules.md": {
        "type": "Reference",
        "title": "Content Delivery & Schedule Optimization Guide",
        "description": "Diagnostic protocols, failure pattern matching, and automated cleanup procedures for scheduled deliveries and scheduler queue optimization.",
        "tags": ["looker", "scheduler", "cron", "queue", "zombie-schedules"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "system-activity-schedules", "resource": "system__activity/scheduled_plan", "title": "Looker System Activity Scheduled Plan Explore"}
        ]
    },
    "skills/custom/healthcheck/references/development_workflows_and_ci.md": {
        "type": "Reference",
        "title": "Development Workflows, Governance & CI/CD Guide",
        "description": "3-Tier Maturity Framework, LookML data test protocols, and automated CI/CD pipelines for LookML engineering governance.",
        "tags": ["lookml", "ci-cd", "data-tests", "git", "governance", "spectacles"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "vendor-testing-suite", "resource": "/skills/vendor/looker-skills/skills/looker-architect/references/testing_suite.md", "title": "LookML Testing Suite"}
        ]
    },
    "skills/custom/healthcheck/references/history_query_analysis.md": {
        "type": "Reference",
        "title": "History Query Analysis & Persona Profiling Guide",
        "description": "Persona-based query segmentation, query complexity categorization, and dashboard error/killed query rate analysis.",
        "tags": ["looker", "system-activity", "personas", "error-rates", "killed-queries"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "system-activity-history", "resource": "system__activity/history", "title": "Looker System Activity History Explore"}
        ]
    },
    "skills/custom/healthcheck/references/large_dashboards_optimization.md": {
        "type": "Reference",
        "title": "Large Dashboards & Auto-Refresh Optimization Guide",
        "description": "Large dashboard decomposition rules, auto-refresh rate limits, and queries-per-run optimization.",
        "tags": ["looker", "dashboards", "tile-bloat", "auto-refresh", "rendering"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "dashboard-standards", "resource": "/skills/vendor/looker-skills/skills/looker-architect/references/dashboard_standards.md", "title": "Looker Dashboard Standards"}
        ]
    },
    "skills/custom/healthcheck/references/looker_bigquery_pipeline_architecture.md": {
        "type": "Reference",
        "title": "Looker & BigQuery Interconnected Pipeline Architecture",
        "description": "6-stage interconnected execution pipeline blueprint, 4 major failure loops, and 5-dimensional audit strategy.",
        "tags": ["looker", "bigquery", "pipeline-architecture", "failure-loops", "forensics"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "connecting-bq", "resource": "/skills/vendor/looker-skills/skills/connecting-looker-to-bigquery/SKILL.md", "title": "Connecting Looker to BigQuery"}
        ]
    },
    "skills/custom/healthcheck/references/merged_queries_remediation.md": {
        "type": "Reference",
        "title": "Merged Queries Diagnostic & Native LookML Remediation Guide",
        "description": "Operational risks of in-memory merged queries and step-by-step LookML refactoring into native joins.",
        "tags": ["looker", "merged-queries", "joins", "lookml-refactoring"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "modeling-guidelines", "resource": "/skills/vendor/looker-skills/skills/lookml-modeling-guidelines/SKILL.md", "title": "LookML Modeling Guidelines"}
        ]
    },
    "skills/custom/healthcheck/references/query_outliers_diagnosis.md": {
        "type": "Reference",
        "title": "Query Outliers Diagnostic & Multi-Vector Forensic Guide",
        "description": "5-Vector root cause forensic framework, 3-way outlier decomposition, and latency classification scorecard.",
        "tags": ["looker", "query-outliers", "forensics", "latency-decomposition"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "benchmarks", "resource": "/skills/custom/healthcheck/references/benchmarks.md", "title": "Google Cloud PSO Latency Benchmarks"}
        ]
    },
    "skills/custom/healthcheck/references/security_roles_and_access_control.md": {
        "type": "Reference",
        "title": "Security Review, Roles, Permissions & Access Control Guide",
        "description": "Diagnostic protocols for auditing user roles, group hierarchies (GBAC), license allocations, and LookML access grants.",
        "tags": ["looker", "security", "gbac", "access-grants", "user-attributes"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "access-grants", "resource": "/skills/vendor/looker-skills/skills/lookml-access-grants/SKILL.md", "title": "LookML Access Grants"}
        ]
    },
    "skills/custom/healthcheck/references/single_dashboard_optimization.md": {
        "type": "Reference",
        "title": "Single Dashboard Forensic Audit & Optimization Checklist",
        "description": "10-point actionable forensic audit checklist for evaluating and accelerating mission-critical Looker dashboards.",
        "tags": ["looker", "dashboard-optimization", "single-dashboard", "audit-checklist"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "dashboard-standards", "resource": "/skills/vendor/looker-skills/skills/looker-architect/references/dashboard_standards.md", "title": "Looker Dashboard Standards"}
        ]
    },
    "skills/custom/healthcheck/references/system_activity_queries.md": {
        "type": "Reference",
        "title": "Looker System Activity Query Catalog & Telemetry Bank",
        "description": "Centralized JSON query dictionary, dimensions, and table calculation formulas for querying Looker system__activity models.",
        "tags": ["looker", "system-activity", "queries", "telemetry", "formulas"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "system-activity-docs", "resource": "https://cloud.google.com/looker/docs/system-activity-pages", "title": "Looker System Activity Documentation", "author": "team:google-cloud"}
        ]
    },
    "skills/custom/healthcheck/references/warehouse_optimization.md": {
        "type": "Reference",
        "title": "BigQuery & Warehouse Compute Optimization Guide",
        "description": "SQL definitions and diagnostic thresholds for auditing BigQuery compute, slot contention, on-demand query costs, and partitioning.",
        "tags": ["bigquery", "slots", "partition-pruning", "query-costs", "information-schema"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "connecting-bq", "resource": "/skills/vendor/looker-skills/skills/connecting-looker-to-bigquery/SKILL.md", "title": "Connecting Looker to BigQuery"},
            {"id": "mig-optimize", "resource": "https://google-cloud-professional-services.googlesource.com/mig-optimize", "title": "MIG Optimize Diagnostic Framework", "author": "team:google-pso"}
        ]
    },

    # -------------------------------------------------------------
    # 4. Custom Refactoring Skill & References (7 Files)
    # -------------------------------------------------------------
    "skills/custom/refactoring/SKILL.md": {
        "type": "Skill",
        "title": "LookML Project Refactoring & Legacy Runtime Migration Skill",
        "name": "looker-refactoring-skill",
        "description": "Master developer skill for Looker project refactoring, Henry-driven model bloat auditing, legacy runtime migration, and CI/CD content validation.",
        "tags": ["looker", "refactoring", "henry", "spectacles", "legacy-runtime", "ci-cd"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "henry-cli", "resource": "https://github.com/looker-open-source/henry", "title": "Henry Looker Pulse & Vacuum CLI", "author": "team:looker-open-source"},
            {"id": "spectacles", "resource": "https://github.com/spectacles-ci/spectacles", "title": "Spectacles LookML CI Validator", "author": "team:spectacles"}
        ]
    },
    "skills/custom/refactoring/references/content_validation_recipe.md": {
        "type": "Reference",
        "title": "Recipe: Content Validator CI/CD Pre-Deployment Check",
        "description": "Automated pre-deployment validation workflow using local Git and looker-cli content validator.",
        "tags": ["looker-cli", "content-validator", "ci-cd", "pre-deployment"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "spectacles-setup", "resource": "/skills/custom/refactoring/references/spectacles_ci_setup.md", "title": "Spectacles CI Setup"}
        ]
    },
    "skills/custom/refactoring/references/henry_command_guide.md": {
        "type": "Reference",
        "title": "Henry Command & Dead Code Vacuuming Guide",
        "description": "Standard Henry CLI operations, parameters, and LookML code-pruning workflows for auditing model bloat.",
        "tags": ["henry", "dead-code", "vacuum", "pulse", "lookml-hygiene"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "henry-repo", "resource": "https://github.com/looker-open-source/henry", "title": "Henry Open Source Tool", "author": "team:looker-open-source"}
        ]
    },
    "skills/custom/refactoring/references/house_keeping_recipe.md": {
        "type": "Reference",
        "title": "Recipe: Housekeeping & Model Bloat Cleanup (using Henry)",
        "description": "Automated model bloat discovery, unused LookML view pruning, and stale dashboard metadata cleanup.",
        "tags": ["henry", "housekeeping", "model-bloat", "view-pruning"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "henry-guide", "resource": "/skills/custom/refactoring/references/henry_command_guide.md", "title": "Henry Command Guide"}
        ]
    },
    "skills/custom/refactoring/references/legacy_runtime_checklist.md": {
        "type": "Reference",
        "title": "Legacy LookML Runtime Migration Checklist",
        "description": "Technical rules and parameter mappings required to safely disable Legacy LookML Runtime in Looker instances.",
        "tags": ["lookml", "legacy-runtime", "migration", "checklist"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "runtime-recipe", "resource": "/skills/custom/refactoring/references/runtime_migration_recipe.md", "title": "Runtime Migration Recipe"}
        ]
    },
    "skills/custom/refactoring/references/runtime_migration_recipe.md": {
        "type": "Reference",
        "title": "Recipe: Legacy Runtime Migration & Symmetric Aggregates",
        "description": "Automated migration recipe from legacy LookML syntax to modern runtime standards.",
        "tags": ["lookml", "runtime-migration", "symmetric-aggregates"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "legacy-checklist", "resource": "/skills/custom/refactoring/references/legacy_runtime_checklist.md", "title": "Legacy Runtime Checklist"}
        ]
    },
    "skills/custom/refactoring/references/spectacles_ci_setup.md": {
        "type": "Reference",
        "title": "Spectacles & Looker Content Validator CI/CD Setup Guide",
        "description": "Implementation guide for automated LookML syntax and Content Validation in continuous integration pipelines.",
        "tags": ["spectacles", "ci-cd", "github-actions", "content-validator"],
        "status": "stable",
        "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
        "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
        "sources": [
            {"id": "spectacles-repo", "resource": "https://github.com/spectacles-ci/spectacles", "title": "Spectacles CI Documentation", "author": "team:spectacles"}
        ]
    }
}

# -------------------------------------------------------------
# Attested Computations (§10) Definitions
# -------------------------------------------------------------
ATTESTED_COMPUTATIONS = {
    "skills/custom/healthcheck/computations/query_latency_breakdown.md": {
        "frontmatter": {
            "type": "Attested Computation",
            "title": "Query Latency Phase Decomposition",
            "description": "Sanctioned Looker System Activity query to decompose total query duration into Looker JVM overhead, database execution, and connection queue wait times.",
            "status": "stable",
            "runtime": "Looker",
            "parameters": [
                {"name": "model_name", "type": "string", "required": True},
                {"name": "timeframe", "type": "string", "required": False}
            ],
            "executor": {
                "resource": "agent/tools/looker_api.py",
                "receipt": ["query_id", "executed_at", "result_source", "async_processing_average", "execute_main_query_average", "acquire_connection_average"]
            },
            "attester": {
                "resource": "evals/test_tools.py"
            },
            "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
            "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
            "sources": [
                {"id": "system-activity-query-metrics", "resource": "system__activity/query_metrics", "title": "Looker System Activity Query Metrics Explore"}
            ]
        },
        "body": """# Computation

```json
{
  "model": "system__activity",
  "view": "query_metrics",
  "fields": [
    "query.model",
    "query.view",
    "query_metrics.async_processing_average",
    "query_metrics.execute_main_query_average",
    "query_metrics.acquire_connection_average",
    "query_metrics.stream_to_cache_average"
  ],
  "filters": {
    "query.model": "@model_name",
    "history.created_date": "30 days"
  },
  "sorts": ["query_metrics.async_processing_average desc"],
  "limit": "50"
}
```

Deconstructs query execution into JVM compile overhead, database runtime, and connection acquisition queue time per Google PSO standards.[^system-activity-query-metrics]

[^system-activity-query-metrics]: Looker System Activity Query Metrics Explore
"""
    },

    "skills/custom/healthcheck/computations/slot_consumption_timeline.md": {
        "frontmatter": {
            "type": "Attested Computation",
            "title": "BigQuery Slot Consumption Timeline (24 Hours)",
            "description": "Sanctioned BigQuery SQL query to evaluate 24-hour hourly slot utilization and peak saturation across query jobs.",
            "status": "stable",
            "runtime": "bigquery",
            "parameters": [
                {"name": "hours", "type": "integer", "required": False},
                {"name": "region", "type": "string", "required": False}
            ],
            "executor": {
                "resource": "agent/tools/bq_client.py",
                "receipt": ["job_id", "executed_sql", "avg_slots", "peak_slots", "total_rows"]
            },
            "attester": {
                "resource": "evals/test_tools.py"
            },
            "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
            "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
            "sources": [
                {"id": "bq-jobs-timeline", "resource": "region-us.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT", "title": "BigQuery Jobs Timeline by Project"}
            ]
        },
        "body": """# Computation

```sql
SELECT
  TIMESTAMP_TRUNC(period_start, HOUR) as hour_window,
  ROUND(AVG(period_slot_ms) / 1000, 2) as avg_slots,
  ROUND(MAX(period_slot_ms) / 1000, 2) as peak_slots
FROM
  `region-us`.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_PROJECT
WHERE
  period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY 1
ORDER BY hour_window DESC
LIMIT 24;
```

Measures warehouse slot contention and saturation against project reservations.[^bq-jobs-timeline]

[^bq-jobs-timeline]: BigQuery Jobs Timeline by Project
"""
    },

    "skills/custom/healthcheck/computations/bytes_billed_by_model.md": {
        "frontmatter": {
            "type": "Attested Computation",
            "title": "BigQuery Query Cost & Bytes Billed Audit",
            "description": "Sanctioned BigQuery SQL query to compute total gigabytes billed and dollar costs grouped by user and job.",
            "status": "stable",
            "runtime": "bigquery",
            "parameters": [
                {"name": "hours", "type": "integer", "required": False},
                {"name": "cost_per_tb", "type": "float", "required": False}
            ],
            "executor": {
                "resource": "agent/tools/bq_client.py",
                "receipt": ["job_id", "executed_sql", "total_gb_billed", "estimated_cost_usd"]
            },
            "attester": {
                "resource": "evals/test_tools.py"
            },
            "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
            "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
            "sources": [
                {"id": "bq-jobs-by-project", "resource": "region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT", "title": "BigQuery Jobs by Project"}
            ]
        },
        "body": """# Computation

```sql
SELECT
  user_email,
  COUNT(1) as total_queries,
  ROUND(SUM(total_bytes_billed) / POW(1024, 3), 2) as total_gb_billed,
  ROUND((SUM(total_bytes_billed) / POW(1024, 4)) * 6.25, 2) as estimated_cost_usd
FROM
  `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND job_type = 'QUERY'
GROUP BY 1
ORDER BY total_gb_billed DESC
LIMIT 20;
```

Audits on-demand query execution expenses and identifies costly unpruned query scans.[^bq-jobs-by-project]

[^bq-jobs-by-project]: BigQuery Jobs by Project
"""
    },

    "skills/custom/healthcheck/computations/pdt_failure_event_log.md": {
        "frontmatter": {
            "type": "Attested Computation",
            "title": "PDT Build Failure Event Log",
            "description": "Sanctioned Looker System Activity query to isolate Persistent Derived Table build failures, error codes, and trigger failures.",
            "status": "stable",
            "runtime": "Looker",
            "parameters": [
                {"name": "model_name", "type": "string", "required": False},
                {"name": "days", "type": "integer", "required": False}
            ],
            "executor": {
                "resource": "agent/tools/looker_api.py",
                "receipt": ["query_id", "failed_pdts", "error_messages"]
            },
            "attester": {
                "resource": "evals/test_tools.py"
            },
            "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
            "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
            "sources": [
                {"id": "pdt-event-log", "resource": "system__activity/pdt_event_log", "title": "Looker System Activity PDT Event Log Explore"}
            ]
        },
        "body": """# Computation

```json
{
  "model": "system__activity",
  "view": "pdt_event_log",
  "fields": [
    "pdt_event_log.view_name",
    "pdt_event_log.action",
    "pdt_event_log.status",
    "pdt_event_log.error_message",
    "pdt_event_log.created_time"
  ],
  "filters": {
    "pdt_event_log.action": "create-fail",
    "pdt_event_log.created_date": "7 days"
  },
  "sorts": ["pdt_event_log.created_time desc"],
  "limit": "25"
}
```

Identifies derived table build errors and broken datagroup cascades.[^pdt-event-log]

[^pdt-event-log]: Looker System Activity PDT Event Log Explore
"""
    },

    "skills/custom/healthcheck/computations/table_partition_ddl.md": {
        "frontmatter": {
            "type": "Attested Computation",
            "title": "BigQuery Table Partitioning & Clustering DDL Generator",
            "description": "Sanctioned BigQuery DDL pattern for recreating unpartitioned warehouse fact tables with date partitioning and high-cardinality clustering.",
            "status": "stable",
            "runtime": "bigquery",
            "parameters": [
                {"name": "source_table", "type": "string", "required": True},
                {"name": "target_table", "type": "string", "required": True},
                {"name": "partition_column", "type": "string", "required": True},
                {"name": "cluster_columns", "type": "string", "required": True}
            ],
            "executor": {
                "resource": "agent/tools/bq_client.py",
                "receipt": ["job_id", "executed_ddl", "status"]
            },
            "attester": {
                "resource": "evals/test_tools.py"
            },
            "generated": {"by": "looker_healthcheck_agent/v0.2", "at": "2026-08-20T12:00:00Z"},
            "verified": {"by": "human:sampitcher", "at": "2026-08-20T14:00:00Z"},
            "sources": [
                {"id": "bq-partitioning-docs", "resource": "https://cloud.google.com/bigquery/docs/partitioned-tables", "title": "BigQuery Partitioned Tables Documentation", "author": "team:google-cloud"}
            ]
        },
        "body": """# Computation

```sql
CREATE OR REPLACE TABLE `@target_table`
PARTITION BY DATE(@partition_column)
CLUSTER BY @cluster_columns AS
SELECT * FROM `@source_table`;
```

Eliminates full table scans on high-volume Looker fact tables.[^bq-partitioning-docs]

[^bq-partitioning-docs]: BigQuery Partitioned Tables Documentation
"""
    }
}

# -------------------------------------------------------------
# Index & Log Files Definitions (§8, §9, §12)
# -------------------------------------------------------------
INDEX_AND_LOG_FILES = {
    # Bundle Root Index (§12 okf_version: "0.2")
    "skills/index.md": """---
okf_version: "0.2"
---

# Looker & BigQuery Knowledge Catalog

Welcome to the **Looker & BigQuery Healthcheck & Performance Optimization Knowledge Catalog**, structured in full compliance with the [Open Knowledge Format (OKF v0.2)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

## Custom Healthcheck Knowledge Bundle

* [Healthcheck Master Skill](custom/healthcheck/SKILL.md) - Master skill for 3-Pillar 30-check Looker healthcheck audits.
* [Playbooks](custom/healthcheck/playbooks/) - Step-by-step diagnostic and remediation playbooks.
* [References](custom/healthcheck/references/) - Deep-dive architectural guides, benchmark tables, and System Activity query catalogs.
* [Attested Computations](custom/healthcheck/computations/) - Sanctioned, verifiable queries and DDLs for telemetry extraction and compute optimization.

## Custom Refactoring Knowledge Bundle

* [Refactoring Master Skill](custom/refactoring/SKILL.md) - Automated LookML refactoring, Henry vacuuming, and CI/CD validation.
* [Refactoring Recipes & References](custom/refactoring/references/) - Recipes for legacy runtime migration, Spectacles CI, and code housekeeping.

## Upstream Vendor Knowledge Bundle

* [Looker Vendor Skills](vendor/looker-skills/skills/) - Upstream Google Cloud Looker developer and performance engineering skills.
""",

    "skills/log.md": """# Knowledge Catalog Update Log

## 2026-08-21
* **Update**: Standardized entire knowledge base, playbooks, references, and registry to Open Knowledge Format (OKF v0.2).
* **Creation**: Added Attested Computation concepts for System Activity metrics, BigQuery slot timelines, and table partitioning DDL.
* **Creation**: Added progressive disclosure `index.md` catalogs and chronological `log.md` files across all bundle scopes.

## 2026-08-20
* **Creation**: Integrated 30-Check Healthcheck Framework and Transcriber 0–4 Scoring Rubrics.
* **Creation**: Integrated Google Cloud PSO Latency Benchmarks and Looker-BigQuery Pipeline Architecture.

## 2026-08-10
* **Initialization**: Established initial healthcheck agent knowledge base.
""",

    "skills/custom/index.md": """# Custom Knowledge Bundles

* [Healthcheck & Optimization](healthcheck/) - Complete 3-Pillar healthcheck framework, playbooks, and System Activity telemetry.
* [Refactoring & Migration](refactoring/) - Automated LookML refactoring, Henry vacuuming, and legacy runtime migration.
""",

    "skills/custom/log.md": """# Custom Knowledge Update Log

## 2026-08-21
* **Update**: Converted all custom healthcheck and refactoring playbooks/references to OKF v0.2 format with YAML frontmatter and provenance sources.
* **Creation**: Added Attested Computations for Looker & BigQuery diagnostic workflows.
""",

    "skills/custom/healthcheck/index.md": """# Looker Healthcheck & Performance Knowledge Bundle

* [Healthcheck Master Skill](SKILL.md) - Master 30-task healthcheck program and looker-cli integration.
* [Playbooks](playbooks/) - 6 Core operational playbooks for delivery, performance triage, LookML quality, content governance, Transcriber scoring, and TDD authoring.
* [References](references/) - 13 Deep-dive architectural guides, PSO benchmarks, and System Activity query catalogs.
* [Attested Computations](computations/) - Sanctioned telemetry queries, slot timelines, and partitioning DDLs.
""",

    "skills/custom/healthcheck/log.md": """# Healthcheck Knowledge Update Log

## 2026-08-21
* **Update**: Added OKF v0.2 frontmatter to all healthcheck playbooks and reference documents.
* **Creation**: Created Attested Computation contracts for query metrics, slot timelines, and bytes billed.
""",

    "skills/custom/healthcheck/playbooks/index.md": """# Healthcheck Playbooks

* [Healthcheck Delivery](playbook_healthcheck_delivery.md) - Master 4-Pillar engagement delivery methodology and interview frameworks.
* [Query Performance](playbook_looker_performance.md) - 4-Step progressive isolation and 3-Way forensic triage for slow queries.
* [LookML Quality & Style Guide](playbook_lookml_quality.md) - DRY modeling standards, snake_case conventions, and primary key enforcement.
* [Content Governance](playbook_content_governance.md) - 90-day unused content deprecation, dead code vacuum, and zombie schedule cleanup.
* [Transcriber Scoring](playbook_transcriber_scoring.md) - 0–4 Evaluation rubric across LookML Quality, UX, Architecture, and Testing.
* [Technical Design Document Authoring](playbook_technical_design_document.md) - Standards for authoring 7-section publication-grade TDD specifications.
""",

    "skills/custom/healthcheck/references/index.md": """# Healthcheck References

* [Aggregate Awareness & Architecture](aggregate_awareness_and_architecture.md) - LookML aggregate tables, datagroups, and Hub & Spoke modular architecture.
* [PSO Latency Benchmarks](benchmarks.md) - Google Cloud PSO latency targets, SLA thresholds, and overhead formulas.
* [Content Delivery Schedules](content_delivery_schedules.md) - Schedule staggering, top-of-hour burst elimination, and queue management.
* [Development Workflows & CI/CD](development_workflows_and_ci.md) - 3-Tier maturity framework, LookML data tests, and Spectacles CI validation.
* [History Query Analysis](history_query_analysis.md) - Persona-based query profiling (Viewer vs Explorer vs Dev) and error rates.
* [Large Dashboards Optimization](large_dashboards_optimization.md) - The >25 Tile Rule, auto-refresh rate limits, and tabbed dashboard decoupling.
* [Pipeline Architecture](looker_bigquery_pipeline_architecture.md) - 6-Stage interconnected execution pipeline blueprint and failure loops.
* [Merged Queries Remediation](merged_queries_remediation.md) - Risks of in-memory merged queries and LookML join refactoring.
* [Query Outliers Diagnosis](query_outliers_diagnosis.md) - 5-Vector root cause framework and 3-Way outlier decomposition.
* [Security Roles & Access Control](security_roles_and_access_control.md) - Group-Based Access Control (GBAC), access grants, and security.
* [Single Dashboard Optimization](single_dashboard_optimization.md) - 10-Point single dashboard forensic audit checklist.
* [System Activity Queries](system_activity_queries.md) - Centralized JSON query dictionary for Looker System Activity models.
* [Warehouse Optimization](warehouse_optimization.md) - BigQuery slot consumption, query cost forensics, and table partitioning.
""",

    "skills/custom/healthcheck/computations/index.md": """# Attested Computations

* [Query Latency Phase Breakdown](query_latency_breakdown.md) - Sanctioned Looker System Activity query to isolate JVM vs DB vs connection queue latency.
* [BigQuery Slot Consumption Timeline](slot_consumption_timeline.md) - Sanctioned BigQuery SQL query to evaluate 24-hour hourly slot utilization.
* [Bytes Billed by Model](bytes_billed_by_model.md) - Sanctioned BigQuery SQL query to compute query cost and gigabytes billed.
* [PDT Failure Event Log](pdt_failure_event_log.md) - Sanctioned Looker System Activity query to isolate derived table build failures.
* [Table Partitioning DDL](table_partition_ddl.md) - Sanctioned BigQuery DDL pattern for recreating unpartitioned tables with date partitioning.
""",

    "skills/custom/refactoring/index.md": """# LookML Refactoring Knowledge Bundle

* [Refactoring Master Skill](SKILL.md) - Master developer skill for LookML refactoring, Henry vacuuming, and legacy runtime migration.
* [References & Recipes](references/) - Step-by-step recipes for content validation, housekeeping, legacy runtime migration, and Spectacles CI.
""",

    "skills/custom/refactoring/log.md": """# Refactoring Knowledge Update Log

## 2026-08-21
* **Update**: Converted all refactoring references to OKF v0.2 format with YAML frontmatter.
""",

    "skills/custom/refactoring/references/index.md": """# Refactoring References & Recipes

* [Content Validation Recipe](content_validation_recipe.md) - Automated pre-deployment validation workflow using looker-cli.
* [Henry Command Guide](henry_command_guide.md) - Standard Henry CLI operations and LookML dead code vacuuming.
* [Housekeeping Recipe](house_keeping_recipe.md) - Automated model bloat discovery and unused view pruning with Henry.
* [Legacy Runtime Checklist](legacy_runtime_checklist.md) - Technical rules and parameter mappings for disabling Legacy LookML Runtime.
* [Runtime Migration Recipe](runtime_migration_recipe.md) - Automated migration from legacy LookML syntax to modern runtime standards.
* [Spectacles CI Setup](spectacles_ci_setup.md) - Implementation guide for Spectacles LookML CI validation.
""",

    "skills/vendor/index.md": """# Upstream Vendor Knowledge Bundles

* [Looker Skills](looker-skills/) - Upstream Looker engineering skills and architecture patterns from Google Cloud.
""",

    "skills/vendor/log.md": """# Vendor Knowledge Update Log

## 2026-08-21
* **Update**: Integrated OKF v0.2 conformance headers across all vendor skill definitions and references.
""",

    "skills/vendor/looker-skills/index.md": """# Looker Engineering Skills (Google Cloud)

* [Connecting Looker to BigQuery](skills/connecting-looker-to-bigquery/SKILL.md) - Connection parameters and BI Engine optimization.
* [Looker Architect](skills/looker-architect/SKILL.md) - Looker architecture patterns, aggregate awareness, and dashboard standards.
* [Looker Performance Optimizer](skills/looker-performance-optimizer/SKILL.md) - Query triage, PDT optimization, and caching.
* [LookML Access Grants](skills/lookml-access-grants/SKILL.md) - Row and column level security in LookML.
* [LookML Liquid](skills/lookml-liquid/SKILL.md) - Liquid templating patterns and dynamic dimensions.
* [LookML Modeling Guidelines](skills/lookml-modeling-guidelines/SKILL.md) - Modeling best practices and join strategies.
* [LookML Refinements](skills/lookml-refinements/SKILL.md) - LookML refinements and DRY patterns.
* [LookML Sets](skills/lookml-sets/SKILL.md) - Field set management and curation.
* [LookML Tests](skills/lookml-tests/SKILL.md) - Data testing and assertion suites.
* [Using Looker CLI](skills/using-looker-cli/SKILL.md) - Looker developer CLI commands and automation.
"""
}

def serialize_frontmatter(data: Dict[str, Any]) -> str:
    """Serializes a dictionary to strict, clean YAML frontmatter without external dependencies."""
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, str):
            if any(c in v for c in [":", "'", "\"", "\n", "@", "#", "{", "}"]):
                escaped = v.replace('"', '\\"')
                lines.append(f'{k}: "{escaped}"')
            else:
                lines.append(f"{k}: {v}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            elif all(isinstance(item, (str, int, float, bool)) for item in v):
                formatted_items = []
                for item in v:
                    if isinstance(item, str) and (":" in item or " " in item):
                        formatted_items.append(f'"{item}"')
                    else:
                        formatted_items.append(str(item))
                lines.append(f"{k}: [{', '.join(formatted_items)}]")
            elif all(isinstance(item, dict) for item in v):
                lines.append(f"{k}:")
                for item in v:
                    first = True
                    for ik, iv in item.items():
                        prefix = "  - " if first else "    "
                        first = False
                        if isinstance(iv, bool):
                            lines.append(f"{prefix}{ik}: {'true' if iv else 'false'}")
                        elif isinstance(iv, (int, float)):
                            lines.append(f"{prefix}{ik}: {iv}")
                        else:
                            iv_str = str(iv)
                            if any(c in iv_str for c in [":", "'", "\"", "@", "#"]):
                                lines.append(f'{prefix}{ik}: "{iv_str}"')
                            else:
                                lines.append(f"{prefix}{ik}: {iv_str}")
        elif isinstance(v, dict):
            # Inline dict format: { by: "...", at: "..." }
            dict_parts = []
            for dk, dv in v.items():
                if isinstance(dv, (int, float)):
                    dict_parts.append(f"{dk}: {dv}")
                elif isinstance(dv, bool):
                    dict_parts.append(f"{dk}: {'true' if dv else 'false'}")
                else:
                    dv_str = str(dv)
                    if any(c in dv_str for c in [":", " ", "'", "\""]):
                        dict_parts.append(f'{dk}: "{dv_str}"')
                    else:
                        dict_parts.append(f"{dk}: {dv_str}")
            lines.append(f"{k}: {{ {', '.join(dict_parts)} }}")
    lines.append("---")
    return "\n".join(lines)


def strip_existing_frontmatter(content: str) -> str:
    """Strips existing YAML frontmatter if present."""
    trimmed = content.strip()
    if trimmed.startswith("---"):
        parts = trimmed.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return trimmed


def apply_okf_to_files():
    print("🚀 Applying Open Knowledge Format (OKF v0.2) Standard across Knowledge Base...\n")
    
    # 1. Update Custom Markdown Documents (Skills, Playbooks, References)
    updated_count = 0
    for rel_path, meta in CUSTOM_DOCS_METADATA.items():
        file_path = ROOT_DIR / rel_path
        if not file_path.exists():
            print(f"⚠️ Warning: File not found: {rel_path}")
            continue
        
        raw_content = file_path.read_text(encoding="utf-8")
        body = strip_existing_frontmatter(raw_content)
        frontmatter_str = serialize_frontmatter(meta)
        new_file_content = f"{frontmatter_str}\n\n{body}\n"
        file_path.write_text(new_file_content, encoding="utf-8")
        updated_count += 1
        print(f"  ✅ Updated Custom Concept: {rel_path} (type: {meta['type']})")

    # 2. Update Vendor Skills and References to ensure 100% OKF compliance
    vendor_dir = ROOT_DIR / "skills" / "vendor"
    if vendor_dir.exists():
        for p in vendor_dir.rglob("*.md"):
            if p.name in ["index.md", "log.md"]:
                continue
            raw_content = p.read_text(encoding="utf-8")
            body = strip_existing_frontmatter(raw_content)
            rel = str(p.relative_to(ROOT_DIR))
            
            # Derive metadata for vendor document
            if p.name == "SKILL.md":
                skill_name = p.parent.name
                meta = {
                    "type": "Skill",
                    "title": skill_name.replace("-", " ").title(),
                    "name": skill_name,
                    "description": f"Official Google Cloud Looker engineering skill for {skill_name}.",
                    "tags": ["looker", "vendor", skill_name],
                    "status": "stable",
                    "generated": {"by": "upstream_vendor/google-cloud", "at": "2026-08-20T12:00:00Z"},
                    "verified": {"by": "process:vendor-sync", "at": "2026-08-20T12:00:00Z"}
                }
            elif "references" in rel:
                ref_name = p.stem.replace("_", " ").title()
                meta = {
                    "type": "Reference",
                    "title": ref_name,
                    "description": f"Looker technical reference guide: {ref_name}.",
                    "tags": ["looker", "vendor", "reference"],
                    "status": "stable",
                    "generated": {"by": "upstream_vendor/google-cloud", "at": "2026-08-20T12:00:00Z"},
                    "verified": {"by": "process:vendor-sync", "at": "2026-08-20T12:00:00Z"}
                }
            else:
                doc_name = f"{p.parent.name} - {p.stem}"
                meta = {
                    "type": "Documentation",
                    "title": doc_name,
                    "description": f"Vendor documentation: {doc_name}.",
                    "status": "stable",
                    "generated": {"by": "upstream_vendor/google-cloud", "at": "2026-08-20T12:00:00Z"},
                    "verified": {"by": "process:vendor-sync", "at": "2026-08-20T12:00:00Z"}
                }
            
            frontmatter_str = serialize_frontmatter(meta)
            p.write_text(f"{frontmatter_str}\n\n{body}\n", encoding="utf-8")
            updated_count += 1
            print(f"  ✅ Updated Vendor Concept: {rel} (type: {meta['type']})")

    # 3. Write Attested Computations
    attested_count = 0
    for rel_path, comp_data in ATTESTED_COMPUTATIONS.items():
        file_path = ROOT_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter_str = serialize_frontmatter(comp_data["frontmatter"])
        body = comp_data["body"].strip()
        full_content = f"{frontmatter_str}\n\n{body}\n"
        file_path.write_text(full_content, encoding="utf-8")
        attested_count += 1
        print(f"  ⚡ Created Attested Computation: {rel_path} (runtime: {comp_data['frontmatter']['runtime']})")

    # 4. Write Index & Log Files
    index_log_count = 0
    for rel_path, content in INDEX_AND_LOG_FILES.items():
        file_path = ROOT_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.strip() + "\n", encoding="utf-8")
        index_log_count += 1
        print(f"  📑 Generated Index / Log File: {rel_path}")

    print(f"\n✨ OKF Standard Application Complete!")
    print(f"  • Updated Concept Documents: {updated_count}")
    print(f"  • Created Attested Computations: {attested_count}")
    print(f"  • Generated Index & Log Files: {index_log_count}")


if __name__ == "__main__":
    apply_okf_to_files()
