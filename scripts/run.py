#!/usr/bin/env python3
"""AI Employee - Gold Tier Autonomous Loop"""
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import Orchestrator

vault = Path(__file__).parent.parent / 'personal-ai-employee'
o = Orchestrator(vault, check_interval=30)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    log("AI Employee - Gold Tier Started")
    log(f"Vault: {vault}")

    processed = set()
    last_gen = None
    check_interval = 10

    cycle = 0
    try:
        while True:
            cycle += 1
            now = datetime.now()

            # Generate posts (every 6 hours)
            if last_gen is None or (now - last_gen).total_seconds() >= 21600:
                log("Generating social posts...")
                o.generate_social_posts()
                last_gen = now

            # Process emails
            pending = o.get_pending_items()
            if pending:
                log(f"Processing {len(pending)} email(s)...")
                try:
                    from kilo_email_processor import KiloEmailProcessor
                    processor = KiloEmailProcessor(vault)
                    processor.process_with_kilo()
                except Exception as e:
                    log(f"Error: {e}")

            # Check approved folder
            approved = o.get_approved_items()
            new_approved = [f for f in approved if f.name not in processed]

            if new_approved:
                log(f"Posting {len(new_approved)} item(s)...")
                o.process_approved_items(new_approved)
                for item in new_approved:
                    processed.add(item.name)

            o.update_dashboard()

            # Status
            pending_approvals = o.get_pending_approvals()
            if new_approved:
                log(f"Done - Posted {len(new_approved)}")
            elif pending_approvals and cycle % 6 == 0:
                log(f"Pending: {len(pending_approvals)} awaiting approval")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        log(f"Stopped. Cycles: {cycle}, Posted: {len(processed)}")


if __name__ == '__main__':
    main()