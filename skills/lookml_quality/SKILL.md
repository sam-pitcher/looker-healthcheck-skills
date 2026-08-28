---
name: lookml_quality
type: Skill
title: "LookML Modeling & Code Quality Master Skill"
description: "LookML semantic modeling, DRY guidelines, AST inspection, primary key integrity, and dead field vacuuming."
status: stable
verified:
  - by: "human:google-pso-architect"
    date: "2026-08-27"
sources:
  - resource: "skills/lookml_quality/playbooks/playbook_lookml_quality.md"
    title: "LookML Modeling Standards"
---

# LookML Quality & Modeling Skill

This skill equips the agent to inspect LookML models, views, and explores streamed live from Looker via `looker-cli`.
It enforces primary key declarations (`primary_key: yes`) to prevent `SUM_DISTINCT` symmetric aggregates, explicit join relationships, Liquid templating, and dead field vacuuming with Henry.
