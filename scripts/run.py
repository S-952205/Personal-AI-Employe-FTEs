#!/usr/bin/env python3
"""
AI Employee — Gold Tier Autonomous Loop

ONE script. Keeps running forever.
Generates posts → waits for your approval → posts → loops.

Usage:
    python scripts\run.py --watch          (generates + watches Approved/ folder, auto-posts)
    python scripts\run.py                  (same as --watch)

Flow (continuous):
    1. Qwen generates Facebook + Twitter posts (AI/tech topics)
    2. Creates approval files in Pending_Approval/
    3. WAITING — script stays alive, watches Approved/ folder
    4. You move file to Approved/ → script detects → posts via MCP → Done/
    5. Generates more posts → keeps looping
    6. Ctrl+C to stop
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import Orchestrator

vault = Path(__file__).parent.parent / 'personal-ai-employee'
o = Orchestrator(vault, check_interval=30)

def main():
    print("\n" + "="*60)
    print("🤖 AI Employee — Gold Tier Autonomous Loop")
    print("="*60)
    print("  1. Qwen generates AI/tech posts → Pending_Approval/")
    print("  2. You review → move to Approved/")
    print("  3. Script detects → auto-posts → Done/")
    print("  4. Keeps generating → keeps looping")
    print("  Ctrl+C to stop")
    print("="*60)

    # Track what we've already processed this session
    processed_approved = set()
    last_generate_time = None
    generate_interval = 300  # 5 minutes between new post generation
    check_interval = 10       # Check Approved/ folder every 10 seconds

    print(f"\n📊 Settings: New posts every {generate_interval//60}min | Checking Approved/ every {check_interval}s\n")

    cycle = 0
    try:
        while True:
            cycle += 1
            now = datetime.now()

            # === STEP 1: Generate new posts (once per interval) ===
            if last_generate_time is None or (now - last_generate_time).total_seconds() >= generate_interval:
                print(f"\n{'='*60}")
                print(f"🔄 Cycle {cycle} — {now.strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                print("🧠 Generating new social posts via Qwen...")
                o.generate_social_posts()
                last_generate_time = now

            # === STEP 2: Check Approved/ folder for new approvals ===
            approved_items = o.get_approved_items()
            new_approved = [f for f in approved_items if f.name not in processed_approved]

            if new_approved:
                print(f"\n📬 Detected {len(new_approved)} approved item(s):")
                for item in new_approved:
                    print(f"  ✅ {item.name}")
                print(f"\n📤 Posting...")
                o.process_approved_items(new_approved)
                for item in new_approved:
                    processed_approved.add(item.name)

            # === STEP 3: Show current status (compact) ===
            pending_approvals = o.get_pending_approvals()

            if new_approved:
                print(f"✅ Posted {len(new_approved)} item(s)")

            # REFRESH DASHBOARD every cycle
            o.update_dashboard()

            if cycle % 3 == 0 or new_approved:  # Show status every 3rd cycle or when posting
                print(f"📊 {len(pending_approvals)} pending | Posted: {len(processed_approved)}", end="")
                if pending_approvals:
                    print(f"  | Awaiting:", end="")
                    for item in pending_approvals[:3]:
                        print(f" {item.name[:40]}", end="")
                print()
            else:
                print(".", end="", flush=True)

            # === STEP 4: Wait before next check ===
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print(f"🛑 AI Employee stopping...")
        print(f"   Total cycles: {cycle}")
        print(f"   Posts generated: {cycle}")
        print(f"   Posts published: {len(processed_approved)}")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
