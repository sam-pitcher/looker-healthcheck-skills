#!/usr/bin/env python3
"""
ADK Session & Trace Inspector.
Extracts and formats complete execution traces, tool calls, subagent handoffs,
and model thoughts from agent/.adk/session.db.
"""

import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "agent" / ".adk" / "session.db"

def get_connection():
    if not DB_PATH.exists():
        print(f"Error: Session database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(str(DB_PATH))

def list_sessions(limit=10):
    conn = get_connection()
    query = """
    SELECT s.id, s.create_time, s.update_time, 
           COUNT(e.id) as event_count
    FROM sessions s
    LEFT JOIN events e ON s.id = e.session_id
    GROUP BY s.id
    ORDER BY s.update_time DESC
    LIMIT ?
    """
    rows = conn.execute(query, (limit,)).fetchall()
    if not rows:
        print("No sessions found in database.")
        return

    print(f"### 📋 Recent ADK Sessions ({len(rows)} Found):\n")
    print(f"| Session ID | Events | Updated At |")
    print(f"| :--- | :---: | :--- |")
    for r in rows:
        sid, created, updated, count = r
        up_str = str(updated)[:19] if updated else "N/A"
        print(f"| `{sid}` | {count} | {up_str} |")

def dump_session_trace(session_id=None):
    conn = get_connection()
    if not session_id:
        # Get latest session
        latest = conn.execute("SELECT id FROM sessions ORDER BY update_time DESC LIMIT 1").fetchone()
        if not latest:
            print("No sessions found.")
            return
        session_id = latest[0]

    events = conn.execute(
        "SELECT id, event_data FROM events WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()

    if not events:
        print(f"No events found for session `{session_id}`.")
        return

    print(f"# 🕵️ Trace Log for Session: `{session_id}`\n")
    print(f"Total Events Recorded: {len(events)}\n")
    print("=" * 80)

    for idx, (ev_id, raw_data) in enumerate(events, 1):
        if not raw_data:
            continue
        try:
            data = json.loads(raw_data)
        except Exception:
            continue

        author = data.get("author") or "Agent"
        role = data.get("content", {}).get("role", "")
        parts = data.get("content", {}).get("parts", [])
        ts = data.get("timestamp")
        time_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S") if ts else ""

        print(f"\n### [Event {idx} | {time_str}] Author: **{author}** ({role})")

        for p in parts:
            if not isinstance(p, dict):
                continue

            # 1. Tool / Function Call
            if "function_call" in p:
                fc = p["function_call"]
                fn_name = fc.get("name")
                args = fc.get("args", {})
                print(f"\n🔧 **TOOL INVOCATION: `{fn_name}`**")
                print(f"```json\n{json.dumps(args, indent=2, default=str)}\n```")

            # 2. Tool / Function Response
            elif "function_response" in p:
                fr = p["function_response"]
                fn_name = fr.get("name")
                resp = fr.get("response", {})
                resp_preview = json.dumps(resp, indent=2, default=str)
                if len(resp_preview) > 1000:
                    resp_preview = resp_preview[:1000] + "\n... (truncated)"
                print(f"\n📥 **TOOL RESPONSE: `{fn_name}`**")
                print(f"```json\n{resp_preview}\n```")

            # 3. Model Text Output
            elif "text" in p and p["text"]:
                txt = p["text"].strip()
                print(f"\n💬 **MESSAGE / THOUGHT:**\n{txt}")

        print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description="Inspect ADK Agent traces and function calls.")
    parser.add_argument("--list", "-l", action="store_true", help="List recent sessions")
    parser.add_argument("--session", "-s", type=str, default=None, help="Session ID to inspect (defaults to latest)")
    parser.add_argument("--limit", type=int, default=10, help="Number of sessions to list")

    args = parser.parse_args()

    if args.list:
        list_sessions(limit=args.limit)
    else:
        dump_session_trace(session_id=args.session)

if __name__ == "__main__":
    main()
