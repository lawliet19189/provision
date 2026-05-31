"""
Weekly runner — starts a Provision intelligence session and streams events.
Handles the query_supabase custom tool on the client side.

Usage:
  cp .env.example .env  # fill in your values
  source .env
  python3 agents/run_weekly.py
"""

import os
import sys
import json
import time
from pathlib import Path
import anthropic
from supabase_tool import execute_query

client = anthropic.Anthropic()

COORDINATOR_ID = os.environ["PROVISION_COORDINATOR_ID"]
ENV_ID         = os.environ["PROVISION_ENV_ID"]


def run():
    print("Starting Provision weekly intelligence pipeline...")
    print(f"Watch in Console: https://platform.claude.com/workspaces/default/sessions/\n")

    session = client.beta.sessions.create(
        agent=COORDINATOR_ID,
        environment_id=ENV_ID,
        title="Provision Weekly Report — 2026-05-31",
    )
    print(f"Session: {session.id}")
    print(f"Watch in Console: https://platform.claude.com/workspaces/default/sessions/{session.id}\n")

    # Stream-first, then send the kickoff
    with client.beta.sessions.events.stream(session_id=session.id) as stream:
        client.beta.sessions.events.send(
            session_id=session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": "Run the weekly intelligence pipeline for the week of 2026-05-24 to 2026-05-30."}]
            }]
        )

        for event in stream:
            _handle_event(event, session.id)
            if event.type == "session.status_terminated":
                break
            if (event.type == "session.status_idle"
                    and getattr(event, "stop_reason", None)
                    and event.stop_reason.type != "requires_action"):
                break

    print("\n✓ Pipeline complete.")
    _download_and_print_report(session.id)


def _handle_event(event, session_id: str):
    t = event.type

    if t == "agent.message":
        for block in event.content:
            if block.type == "text" and block.text.strip():
                print(f"\n[{getattr(event, 'agent_name', 'agent')}] {block.text.strip()}")

    elif t == "agent.custom_tool_use" and event.name == "query_supabase":
        sql = event.input.get("sql", "")
        agent_name = getattr(event, "agent_name", "DataAgent")
        print(f"\n[{agent_name}] → query_supabase:\n  {sql[:120]}{'...' if len(sql) > 120 else ''}")
        result = execute_query(sql)
        # Send result back, echoing the thread if it's a subagent call
        tool_result = {
            "type": "user.custom_tool_result",
            "custom_tool_use_id": event.id,
            "content": [{"type": "text", "text": result}],
        }
        thread_id = getattr(event, "session_thread_id", None)
        if thread_id:
            tool_result["session_thread_id"] = thread_id
        client.beta.sessions.events.send(session_id=session_id, events=[tool_result])

    elif t == "session.status_running":
        print(".", end="", flush=True)

    elif t == "session.thread_created":
        agent = getattr(event, "agent_name", "subagent")
        print(f"\n[coordinator] → spawning {agent}")

    elif t == "session.thread_status_idle":
        agent = getattr(event, "agent_name", "subagent")
        print(f"\n[{agent}] done.")

    elif t == "session.error":
        print(f"\n[error] {event}")

    elif t == "session.status_terminated":
        print("\n[session terminated]")


def _download_and_print_report(session_id: str):
    out_dir = Path(__file__).parent / "intelligence"
    out_dir.mkdir(exist_ok=True)

    # Brief wait for session container to finish indexing output files
    time.sleep(3)

    print("\nDownloading output files from session container...")
    files = client.beta.files.list(
        scope_id=session_id,
        betas=["managed-agents-2026-04-01"],
    )

    saved = []
    for f in files.data:
        dest = out_dir / Path(f.filename).name
        content = client.beta.files.download(f.id)
        dest.write_bytes(content.read())
        saved.append((f.filename, dest))
        print(f"  ✓ {f.filename} → {dest}")

    if not saved:
        print("  No output files found. The agents may not have written to /mnt/session/outputs/.")
        print("  Check the session in Console for details.")
        return

    # Print the weekly report if present
    report_path = out_dir / "weekly_report.json"
    if not report_path.exists():
        print(f"\nweekly_report.json not found among downloads. Files saved: {[s[1] for s in saved]}")
        return

    with open(report_path) as f:
        report = json.load(f)

    print("\n" + "=" * 60)
    print("PROVISION WEEKLY INTELLIGENCE REPORT")
    print("=" * 60)
    print(f"\n{report.get('headline', '')}")
    print(f"\nTL;DR: {report.get('marco_tldr', '')}")

    actions = report.get("actions", [])
    if actions:
        print("\nTop Actions:")
        for a in actions[:3]:
            print(f"  {a['priority']}. {a['action']}")
            print(f"     Why: {a['why']}")

    print(f"\nFull reports saved to agents/intelligence/")


if __name__ == "__main__":
    # Check required env vars
    required = ["ANTHROPIC_API_KEY", "PROVISION_COORDINATOR_ID", "PROVISION_ENV_ID",
                "SUPABASE_HOST", "SUPABASE_USER", "SUPABASE_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your values, then: source .env")
        sys.exit(1)

    run()
