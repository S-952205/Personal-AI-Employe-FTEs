#!/usr/bin/env python3
"""
Setup Windows Task Scheduler for Gold Tier

Creates scheduled tasks:
1. CEO Briefing — Every Sunday at 10:00 PM
2. (NO Orchestrator - PM2 handles that!)

Usage:
    python scripts\setup_scheduled_tasks.py          (install CEO Briefing only)
    python scripts\setup_scheduled_tasks.py --remove  (remove all tasks)
    python scripts\setup_scheduled_tasks.py --list    (list tasks)
"""

import subprocess
import sys
import argparse
from pathlib import Path

SCRIPTS = Path(__file__).parent
PYTHON = sys.executable

def run_schtasks(cmd):
    """Run schtasks command and return result."""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print(f"  ✅ {result.stdout.strip()}")
    else:
        # May already exist
        if "already exists" in result.stderr.lower() or "already been scheduled" in result.stderr.lower():
            print(f"  ⚠️  Already exists (update needed)")
        else:
            print(f"  ❌ {result.stderr.strip()[:100]}")
    return result.returncode == 0

def get_python_path():
    """Get Python executable path for schtasks."""
    return sys.executable.replace(' ', '^ ').replace('\\', '\\\\')

def get_script_path(name):
    """Get full script path."""
    return str((SCRIPTS / name).absolute()).replace(' ', '^ ').replace('\\', '\\\\')

def install():
    """Create scheduled tasks - CEO Briefing ONLY."""
    print("\n" + "="*60)
    print("SETTING UP WINDOWS TASK SCHEDULER")
    print("="*60)
    print("\nNOTE: Orchestrator/run.py is NOT scheduled!")
    print("      PM2 already runs orchestrator continuously.")
    print("      Scheduling both causes duplicate post generation!")

    py = get_python_path()

    # Task 1: CEO Briefing — Every Sunday at 10:00 PM
    print("\n📊 Task: CEO Briefing (Sunday 10:00 PM)")
    cmd = (
        f'schtasks /Create /TN "AI_Employee_CEO_Briefing" '
        f'/TR "{py} {get_script_path('ceo_briefing.py')}" '
        f'/SC WEEKLY /D SUN /ST 22:00 '
        f'/RL HIGHEST /F'
    )
    run_schtasks(cmd)

    print(f"\n{'='*60}")
    print("SETUP COMPLETE")
    print(f"{'='*60}")
    print("\nTo verify:")
    print("  schtasks /Query /TN AI_Employee_CEO_Briefing")
    print("\nTo remove:")
    print("  python scripts\\setup_scheduled_tasks.py --remove")

def remove():
    """Remove scheduled tasks."""
    print("\nRemoving scheduled tasks...")
    run_schtasks('schtasks /Delete /TN "AI_Employee_CEO_Briefing" /F')
    run_schtasks('schtasks /Delete /TN "AI_Employee_Orchestrator" /F')
    print("Done.")

def list_tasks():
    """List AI Employee tasks."""
    print("\nScheduled Tasks:")
    subprocess.run('schtasks /Query /TN AI_Employee_CEO_Briefing', shell=True)
    print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remove', action='store_true', help='Remove tasks')
    parser.add_argument('--list', action='store_true', help='List tasks')
    args = parser.parse_args()

    if args.remove:
        remove()
    elif args.list:
        list_tasks()
    else:
        install()
