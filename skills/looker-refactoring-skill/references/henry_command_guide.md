# Henry Command Guide for Model Bloat & Cleanup

This reference guide documents standard Henry CLI commands for auditing model bloat, unused explores, and unused views across any Looker model.

---

## 1. Core Henry Commands

### `henry pulse`
Runs a high-level project scan to identify explores and views that have had zero user queries over a given timeframe.
```bash
# Scan entire instance / default model for 90 days of inactivity
henry pulse --timeframe=90

# Scan a specific model
henry pulse --model=<model_name> --timeframe=90
```

### `henry vacuum`
Scans at the explore and field level to identify specific dimensions and measures that have never been used in queries, looks, or dashboards.
```bash
# Vacuum specific explore
henry vacuum --model=<model_name> --explore=<explore_name> --timeframe=90
```

---

## 2. Programmatic Execution via Python Wrapper

You can run Henry programmatically from within our agent using `scripts/run_henry.py`:
```python
from scripts.run_henry import run_henry_pulse, run_henry_vacuum

# Run Pulse
pulse_results = run_henry_pulse(model="<model_name>", timeframe=90)

# Run Vacuum
vacuum_results = run_henry_vacuum(model="<model_name>", explore="<explore_name>", timeframe=90)
```
