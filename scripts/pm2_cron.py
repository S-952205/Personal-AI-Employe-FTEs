#!/usr/bin/env python3
"""
PM2 Cron Scheduler for AI Employee

Runs continuously. Triggers scheduled jobs at configured times.
Managed by PM2 — auto-restarts on crash.

Scheduled Jobs:
  - CEO Briefing: Every Sunday at 10:00 PM
  - Social Post: Every 6 hours (optional)
  - Vault Backup: Daily at 3:00 AM

Usage:
    pm2 start ecosystem.config.cjs  (includes this as a PM2 process)
    python scripts/pm2_cron.py      (standalone for testing)
"""

import time
import subprocess
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

SCRIPTS = Path(__file__).parent
PYTHON = sys.executable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PM2-Cron] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pm2_cron.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PM2Cron')


class CronJob:
    """A scheduled job with cron-like expression."""

    def __init__(self, name: str, cron_expr: str, command: list, enabled: bool = True):
        """
        Args:
            name: Job name
            cron_expr: Cron expression (minute hour day_of_month month day_of_week)
                       e.g., "0 22 * * 0" = Every Sunday at 10:00 PM
            command: Command to run (list of args)
            enabled: Whether this job is active
        """
        self.name = name
        self.cron_expr = cron_expr
        self.command = command
        self.enabled = enabled
        self.last_run = None
        self.parse_cron()

    def parse_cron(self):
        """Parse cron expression into schedule rules."""
        parts = self.cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {self.cron_expr}. Expected 5 fields.")

        self.minute = parts[0]     # 0-59
        self.hour = parts[1]       # 0-23
        self.day_of_month = parts[2]  # 1-31
        self.month = parts[3]      # 1-12
        self.day_of_week = parts[4]   # 0=Sunday, 1=Monday, etc.

    def should_run(self, now: datetime) -> bool:
        """Check if job should run at this time."""
        # Don't run more than once per minute
        if self.last_run and (now - self.last_run).total_seconds() < 60:
            return False

        # Check minute
        if self.minute != '*' and int(self.minute) != now.minute:
            return False

        # Check hour
        if self.hour != '*' and int(self.hour) != now.hour:
            return False

        # Check day of month
        if self.day_of_month != '*' and int(self.day_of_month) != now.day:
            return False

        # Check month
        if self.month != '*' and int(self.month) != now.month:
            return False

        # Check day of week (0=Sunday, 6=Saturday)
        if self.day_of_week != '*':
            # Python: Monday=0, Sunday=6
            # Cron: Sunday=0, Saturday=6
            python_dow = now.weekday()  # 0=Monday
            cron_dow = (python_dow + 1) % 7  # Convert to cron: 0=Sunday
            if cron_dow != int(self.day_of_week):
                return False

        return True

    def execute(self):
        """Run the job."""
        logger.info(f"🚀 Running job: {self.name}")
        logger.info(f"   Command: {' '.join(self.command)}")

        try:
            result = subprocess.run(
                self.command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                logger.info(f"✅ Job {self.name} completed successfully")
                if result.stdout:
                    for line in result.stdout.strip().split('\n')[-5:]:
                        logger.info(f"   {line}")
            else:
                logger.warning(f"⚠️  Job {self.name} exited with code {result.returncode}")
                if result.stderr:
                    for line in result.stderr.strip().split('\n')[-5:]:
                        logger.warning(f"   {line}")

            self.last_run = datetime.now()

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Job {self.name} timed out (5 min)")
        except Exception as e:
            logger.error(f"❌ Job {self.name} failed: {e}")


def main():
    logger.info("🔄 PM2 Cron Scheduler started")
    logger.info(f"   Python: {PYTHON}")
    logger.info(f"   Scripts: {SCRIPTS}")

    # ============================================================
    # Define Scheduled Jobs
    # ============================================================

    jobs = [
        # CEO Briefing — Every Sunday at 10:00 PM (22:00)
        CronJob(
            name="CEO Briefing",
            cron_expr="0 22 * * 0",  # minute=0, hour=22, every Sunday
            command=[PYTHON, str(SCRIPTS / 'ceo_briefing.py')],
            enabled=True
        ),

        # Social Media Auto-Post — Every 6 hours at minute 0
        CronJob(
            name="Social Auto-Post",
            cron_expr="0 */6 * * *",  # Every 6 hours
            command=[PYTHON, str(SCRIPTS / 'run.py')],
            enabled=True  # Set to False if you prefer manual approval
        ),

        # Daily Audit Summary — Every day at 3:00 AM
        CronJob(
            name="Daily Audit Summary",
            cron_expr="0 3 * * *",  # Every day at 3 AM
            command=[PYTHON, str(SCRIPTS / 'test_gold_tier.py')],
            enabled=False  # Disabled by default
        ),

        # Facebook Token Check — Every Monday at 9:00 AM
        CronJob(
            name="Facebook Token Check",
            cron_expr="0 9 * * 1",  # Every Monday at 9 AM
            command=[PYTHON, str(SCRIPTS / 'fb_token_diagnostic.py'), '--no-update'],
            enabled=False  # Disabled by default
        ),
    ]

    # Log schedule
    logger.info("\n📅 Scheduled Jobs:")
    for job in jobs:
        status = "✅" if job.enabled else "❌"
        logger.info(f"  {status} {job.name}: cron='{job.cron_expr}'")

    logger.info("\n⏰ Waiting for scheduled times... (Ctrl+C to stop)")

    # Main loop — check every 30 seconds
    while True:
        try:
            now = datetime.now()

            for job in jobs:
                if not job.enabled:
                    continue

                if job.should_run(now):
                    logger.info(f"\n{'='*50}")
                    job.execute()
                    logger.info(f"{'='*50}")

            # Sleep 30 seconds (check twice per minute)
            time.sleep(30)

        except KeyboardInterrupt:
            logger.info("\n🛑 Cron scheduler stopping...")
            break
        except Exception as e:
            logger.error(f"❌ Cron loop error: {e}")
            time.sleep(60)


if __name__ == '__main__':
    main()
