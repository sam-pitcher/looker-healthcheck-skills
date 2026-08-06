#!/usr/bin/env python3
"""
Entrypoint for Looker Healthcheck ADK Agent.
"""

import sys
from pathlib import Path
from agent.app import LookerHealthcheckAgent

def main():
    try:
        agent = LookerHealthcheckAgent()
        report = agent.run_audit()
        
        # Save output
        output_file = Path(__file__).parent / "AUDIT_REPORT.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
            
        print(f"\n✅ Audit complete! Report written to:\n{output_file}\n")
        print("Summary Scorecard Preview:\n")
        print("\n".join(report.split("\n")[:25]))
    except Exception as e:
        print(f"❌ Error running healthcheck audit: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
