---
name: looker_performance
type: Skill
title: "Looker Performance & Query Lifecycle Master Skill"
description: "Tactical guidelines, System Activity metrics dictionary, and query lifecycle phase decomposition."
status: stable
verified:
  - by: "human:google-pso-architect"
    date: "2026-08-27"
sources:
  - resource: "skills/looker_performance/references/benchmarks.md"
    title: "Google Cloud PSO Latency SLAs"
---

# Looker Performance & Content Optimization Skill

This skill guides the inspection of query latency phase decomposition (Looker JVM overhead vs DB execute vs queue wait), dashboard tile concurrency (>25 tiles), auto-refresh abuse (<30m), and schedule stacking.
