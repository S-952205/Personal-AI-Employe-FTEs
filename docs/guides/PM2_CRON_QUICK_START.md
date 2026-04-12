# PM2 + Cron Quick Start Guide

**Purpose:** Keep your AI Employee running 24/7 with auto-restart, scheduled jobs, and log management.

---

## What's Included

| Component | What It Does |
|-----------|-------------|
| **PM2** | Process manager — keeps your scripts alive, auto-restarts on crash |
| **ecosystem.config.cjs** | Defines 5 processes: Gmail Watcher, LinkedIn Watcher, File Watcher, Orchestrator, PM2 Cron |
| **pm2_cron.py** | Internal scheduler that runs timed jobs (CEO Briefing, auto-posts, etc.) |

---

## 1. Install PM2

```powershell
# Open PowerShell in your project folder
npm install -g pm2
```

---

## 2. Start Everything

```powershell
# From project root (C:\Projects\Personal-AI-Employe-FTEs)
pm2 start ecosystem.config.cjs

# Save the process list (so PM2 remembers on reboot)
pm2 save
```

This starts **5 processes**:

| Process Name | What It Does |
|-------------|-------------|
| `gmail-watcher` | Monitors Gmail for new emails every 2 min |
| `linkedin-watcher` | Monitors LinkedIn inbox (manual input mode) |
| `filesystem-watcher` | Watches Inbox/ folder for new files |
| `orchestrator` | Main brain — reads Needs_Action, triggers Qwen, processes approvals |
| `pm2-cron` | Scheduler — runs timed jobs (see below) |

---

## 3. Check Status

```powershell
# See all processes running (or stopped)
pm2 status

# See all logs in real-time
pm2 logs

# See logs for a specific process
pm2 logs orchestrator
pm2 logs pm2-cron
pm2 logs gmail-watcher

# See only errors
pm2 logs --err
```

---

## 4. Scheduled Jobs (via pm2-cron)

The `pm2_cron.py` script runs **continuously** and triggers jobs at configured times. Here's the current schedule:

| Job | Schedule | Cron Expression | What It Does |
|-----|----------|-----------------|-------------|
| **CEO Briefing** | Every Sunday 10 PM | `0 22 * * 0` | Generates weekly business report in Briefings/ |
| **Social Auto-Post** | Every 6 hours | `0 */6 * * *` | Runs `run.py` — generates + posts social media |
| **Daily Audit Summary** | Every day 3 AM | `0 3 * * *` | Runs test suite (disabled by default) |
| **Facebook Token Check** | Every Monday 9 AM | `0 9 * * 1` | Checks if Facebook token is valid (disabled by default) |

### Enable/Disable Jobs

Edit `scripts/pm2_cron.py` and change `enabled=True` or `enabled=False`:

```python
# Enable auto-posting
CronJob(
    name="Social Auto-Post",
    cron_expr="0 */6 * * *",
    command=[PYTHON, str(SCRIPTS / 'run.py')],
    enabled=True  # <-- Change this
),
```

Then restart:
```powershell
pm2 restart pm2-cron
```

---

## 5. Manage Processes

```powershell
# Restart all
pm2 restart all

# Restart one process
pm2 restart orchestrator

# Stop all
pm2 stop all

# Stop one
pm2 stop gmail-watcher

# Delete all (remove from PM2)
pm2 delete all

# View memory usage
pm2 monit
```

---

## 6. Auto-Start on Windows Boot

PM2 doesn't have native Windows startup support, but you have two options:

### Option A: Use pm2-startup (recommended)

```powershell
npm install -g pm2-windows-startup
pm2-startup install
pm2 save
```

### Option B: Use Windows Task Scheduler

```powershell
# Run the setup script
scripts\setup-tasks.bat
```

This creates a scheduled task that runs `pm2 resurrect` on login.

---

## 7. Log Files

All PM2 logs go to `logs/` folder:

| File | Contains |
|------|----------|
| `logs/pm2-orchestrator-out.log` | Orchestrator output |
| `logs/pm2-orchestrator-error.log` | Orchestrator errors |
| `logs/pm2-cron-out.log` | Cron scheduler output |
| `logs/pm2-cron-error.log` | Cron errors |
| `logs/pm2-gmail-watcher-out.log` | Gmail watcher output |

Logs include timestamps in format `YYYY-MM-DD HH:mm:ss`.

---

## 8. Troubleshooting

### Process keeps restarting (crash loop)

```powershell
# Check the error log
pm2 logs orchestrator --lines 100

# Or read the file
type logs\pm2-orchestrator-error.log
```

### PM2 says "process in error state"

```powershell
# Delete and restart
pm2 delete orchestrator
pm2 start ecosystem.config.cjs --only orchestrator
```

### Cron job didn't run at scheduled time

1. Check if pm2-cron is running: `pm2 status`
2. Check cron logs: `pm2 logs pm2-cron`
3. Verify the job is enabled in `scripts/pm2_cron.py`

### Want to change a cron schedule

1. Edit `scripts/pm2_cron.py` → find the job → change `cron_expr`
2. Restart: `pm2 restart pm2-cron`

---

## Cron Expression Format

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0=Sunday, 6=Saturday)
│ │ │ │ │
* * * * *
```

### Common Patterns

| Expression | Meaning |
|------------|---------|
| `0 */2 * * *` | Every 2 hours |
| `30 8 * * 1-5` | Weekdays at 8:30 AM |
| `0 0 * * 0` | Every Sunday at midnight |
| `*/15 * * * *` | Every 15 minutes |
| `0 9 * * *` | Every day at 9 AM |

---

## Quick Reference Card

```powershell
# START:     pm2 start ecosystem.config.cjs
# STATUS:    pm2 status
# LOGS:      pm2 logs
# RESTART:   pm2 restart all
# STOP:      pm2 stop all
# SAVE:      pm2 save
# MONITOR:   pm2 monit
```
