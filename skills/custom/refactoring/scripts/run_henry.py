#!/usr/bin/env python3
"""
Python wrapper for Henry CLI (Pulse & Vacuum).
Automates model bloat and unused content detection across Looker projects.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

def run_henry_pulse(model: Optional[str] = None, timeframe: int = 90) -> Dict[str, Any]:
    """
    Runs Henry Pulse to identify unused explores and views over a given timeframe (default: 90 days).
    """
    cmd = ["henry", "pulse", f"--timeframe={timeframe}"]
    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout if result.stdout else result.stderr
        return {
            "status": "success" if result.returncode == 0 else "warning",
            "command": " ".join(cmd),
            "output": output
        }
    except FileNotFoundError:
        # Fallback to direct python module execution
        venv_python = Path(__file__).parents[3] / ".venv/bin/python"
        cmd = [str(venv_python), "-m", "henry", "pulse", f"--timeframe={timeframe}"]
        if model:
            cmd.extend(["--model", model])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return {
                "status": "success" if result.returncode == 0 else "warning",
                "command": " ".join(cmd),
                "output": result.stdout or result.stderr
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to execute Henry: {str(e)}"}

def run_henry_vacuum(model: Optional[str] = None, explore: Optional[str] = None, timeframe: int = 90) -> Dict[str, Any]:
    """
    Runs Henry Vacuum to identify unused fields within models/explores over a given timeframe.
    """
    cmd = ["henry", "vacuum", f"--timeframe={timeframe}"]
    if model:
        cmd.extend(["--model", model])
    if explore:
        cmd.extend(["--explore", explore])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "status": "success" if result.returncode == 0 else "warning",
            "command": " ".join(cmd),
            "output": result.stdout or result.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    timeframe = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    model = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(run_henry_pulse(model, timeframe), indent=2))
