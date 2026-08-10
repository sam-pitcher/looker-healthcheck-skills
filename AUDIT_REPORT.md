# Looker Healthcheck Audit
**Target Instance:** `https://915eab0a-ce5e-423b-81fb-1e93c2f3424d.looker.app`

## 1. Component 2: Performance Audit Scorecard
| Metric Name | Observed Value | Target Benchmark | Status |
| :--- | :---: | :---: | :---: |
| **Average Async Runtime** | `0.56s` | `< 5.00s` | **HEALTHY** |
| **Indicative Looker Overhead** | `54.1%` | `< 20.0%` | **CRITICAL** |
| **Cache Hit Percentage** | `0.0%` | `> 50.0%` | **CRITICAL** |
| **Execute Main Query (DB)** | `0.25s` | `< 4.87s` | **HEALTHY** |
| **Acquire Connection** | `0.013s` | `< 0.238s` | **HEALTHY** |
| **Per-User Throttler** | `0.001s` | `0.000s` | **HEALTHY** |
| **Worker Queue Time** | `0.008s` | `0.000s` | **HEALTHY** |
| **Project Init** | `0.000s` | `< 0.100s` | **HEALTHY** |
| **Model Init (Compute)** | `0.00s` | `< 2.42s` | **HEALTHY** |
| **Model Init (Cache)** | `0.00s` | `< 0.50s` | **HEALTHY** |
| **Explore Init (Compute)** | `0.000s` | `< 0.233s` | **HEALTHY** |
| **Explore Init (Cache)** | `0.000s` | `< 0.351s` | **HEALTHY** |
| **SQL Prepare Time** | `0.112s` | `< 0.439s` | **HEALTHY** |
| **Stream to Cache** | `0.239s` | `< 0.223s` | **WARNING** |
| **Post Processing** | `0.003s` | `< 0.223s` | **HEALTHY** |

## 2. Component 1: Strategy & Developer Baseline
- **Active Looker Developers:** `11`
- **Active Looker Administrators:** `1`

## 3. Component 4: Unused Content & Zombie Schedules
- **90-Day Stale Dashboards Identified:** `2`
- **Zombie Schedules (Inactive Users >90 Days):** `0`