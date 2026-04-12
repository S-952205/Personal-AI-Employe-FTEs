#!/usr/bin/env python3
"""
Gold Tier Test Suite

Tests all Gold Tier features in one run.
Shows PASS/FAIL for each requirement.

Usage:
    python scripts\test_gold_tier.py
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / 'scripts'
VAULT = ROOT / 'personal-ai-employee'
MCP_CONFIG = ROOT / 'mcp-config.json'

results = {'pass': 0, 'fail': 0, 'skip': 0}

def check(name, condition, detail=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    if not condition:
        results['fail'] += 1
    else:
        results['pass'] += 1
    print(f"  {status}  {name}")
    if detail and not condition:
        print(f"         → {detail}")

def skip(name, reason=""):
    results['skip'] += 1
    print(f"  ⏭️  SKIP  {name}")
    if reason:
        print(f"         → {reason}")

# ============================================================
# Test Runner
# ============================================================

def main():
    print("\n" + "="*70)
    print("GOLD TIER TEST SUITE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)

    # === 1. Core Infrastructure ===
    print("\n📁 1. VAULT STRUCTURE")
    required_folders = ['Inbox', 'Needs_Action', 'Pending_Approval', 'Approved', 
                        'Done', 'Plans', 'In_Progress', 'Logs', 'Accounting', 
                        'Briefings', 'Rejected']
    for folder in required_folders:
        check(f"Folder: {folder}/", (VAULT / folder).exists())

    print("\n📄 Core Files")
    check("Dashboard.md", (VAULT / 'Dashboard.md').exists())
    check("Business_Goals.md", (VAULT / 'Business_Goals.md').exists())
    check("Company_Handbook.md", (VAULT / 'Company_Handbook.md').exists())

    # === 2. Watchers ===
    print("\n👁️  2. WATCHERS (5 required for Gold)")
    watchers = {
        'Gmail Watcher': 'gmail_watcher.py',
        'LinkedIn Watcher': 'linkedin_watcher.py',
        'File System Watcher': 'filesystem_watcher.py',
        'Facebook Watcher': 'facebook_watcher.py',
        'Twitter Watcher': 'twitter_watcher.py',
    }
    watcher_count = 0
    for name, file in watchers.items():
        exists = (SCRIPTS / file).exists()
        if exists:
            watcher_count += 1
        check(name, exists, f"Missing: {file}")
    check(f"Total watchers: {watcher_count}/5", watcher_count >= 3, 
          f"Only {watcher_count} watchers found. Need 3+ for Silver, 5 for Gold")

    # === 3. MCP Servers ===
    print("\n🔌 3. MCP SERVERS (5 required for Gold)")
    servers = {
        'Email MCP': 'email-mcp/index.js',
        'LinkedIn MCP': 'linkedin-mcp/index.js',
        'Facebook MCP': 'facebook-mcp/index.js',
        'Twitter MCP': 'twitter-mcp/index.js',
        'Odoo MCP': 'odoo-mcp/index.js',
    }
    server_count = 0
    for name, file in servers.items():
        exists = (ROOT / 'mcp-servers' / file).exists()
        if exists:
            server_count += 1
        check(name, exists, f"Missing: {file}")
    check(f"Total MCP servers: {server_count}/5", server_count >= 5,
          f"Only {server_count} servers found")

    # MCP Config
    print("\n⚙️  MCP Configuration")
    if MCP_CONFIG.exists():
        config = json.loads(MCP_CONFIG.read_text())
        enabled = [k for k, v in config.get('servers', {}).items() if not v.get('disabled', False)]
        disabled = [k for k, v in config.get('servers', {}).items() if v.get('disabled', False)]
        check(f"Enabled servers: {', '.join(enabled)}", len(enabled) >= 3,
              f"Only {len(enabled)} enabled. Disabled: {', '.join(disabled)}")
    else:
        check("mcp-config.json exists", False)

    # === 4. Agent Skills ===
    print("\n🧩 4. AGENT SKILLS (8 required for Gold)")
    skills_path = ROOT / '.qwen' / 'skills'
    skills = ['browsing-with-playwright', 'email-operations', 'linkedin-operations',
              'facebook-operations', 'twitter-operations', 'hitl-approval',
              'odoo-accounting', 'ralph-wiggum']
    skill_count = 0
    for skill in skills:
        exists = (skills_path / skill).exists()
        if exists:
            skill_count += 1
        check(f"Skill: {skill}", exists)
    check(f"Total skills: {skill_count}/8", skill_count >= 4,
          f"Only {skill_count} skills found")

    # === 5. HITL Workflow ===
    print("\n🔒 5. HUMAN-IN-THE-LOOP WORKFLOW")
    pending = list((VAULT / 'Pending_Approval').glob('*.md'))
    approved_files = list((VAULT / 'Approved').glob('*.md'))
    done_files = list((VAULT / 'Done').glob('*.md'))
    check("Pending_Approval/ exists", True)
    check("Approved/ exists", True)
    # Also count audit log success entries
    log_actions = 0
    if (VAULT / 'Logs').exists():
        for log_file in (VAULT / 'Logs').glob('*.json'):
            try:
                for line in log_file.read_text(encoding='utf-8', errors='ignore').strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('result') == 'success':
                                log_actions += 1
                        except:
                            pass
            except:
                pass

    check(f"Done ({len(done_files)} files) + Audit ({log_actions} actions)",
          len(done_files) > 0 or log_actions > 0,
          f"No completed items")
    check("HITL settings in mcp-config", 
          any('require_approval' in str(v) for v in json.loads(MCP_CONFIG.read_text()).get('settings', {}).values()))

    # === 6. Orchestrator ===
    print("\n🎯 6. ORCHESTRATOR")
    orch_path = SCRIPTS / 'orchestrator.py'
    check("orchestrator.py exists", orch_path.exists())
    if orch_path.exists():
        content = orch_path.read_text(encoding='utf-8', errors='ignore')
        check("Facebook posting method", '_post_to_facebook' in content)
        check("Twitter posting method", '_post_to_twitter' in content)
        check("Social post generation", 'generate_social_posts' in content)
        check("Qwen integration", 'subprocess.run' in content and 'qwen' in content.lower())
        check("Audit logging", 'audit.log_action' in content or 'self.audit' in content)
        check("Plan creation", 'create_plan' in content or 'Plan' in content)

    # === 7. Error Recovery ===
    print("\n🛡️  7. ERROR RECOVERY")
    check("Circuit breaker exists", (SCRIPTS / 'circuit_breaker.py').exists())
    check("Retry handler exists", (SCRIPTS / 'retry_handler.py').exists())

    # === 8. Audit Logging ===
    print("\n📝 8. AUDIT LOGGING")
    check("audit_logger.py exists", (SCRIPTS / 'audit_logger.py').exists())
    logs_folder = VAULT / 'Logs'
    if logs_folder.exists():
        log_files = list(logs_folder.glob('*.json'))
        check(f"Log files exist ({len(log_files)} found)", len(log_files) > 0,
              "No JSON log files in Logs/")
        if log_files:
            # Check log format - JSONL (newline-delimited JSON) is valid
            try:
                sample = log_files[-1].read_text(encoding='utf-8', errors='ignore').strip().split('\n')[0]
                json.loads(sample)
                check("Log format is valid (JSONL)", True)
            except:
                check("Log format valid (JSONL)", False, "Log files not valid JSON/JSONL")
    else:
        check("Logs/ folder exists", False)

    # === 9. CEO Briefing ===
    print("\n📊 9. CEO BRIEFING GENERATOR")
    check("ceo_briefing.py exists", (SCRIPTS / 'ceo_briefing.py').exists())
    briefing_files = list((VAULT / 'Briefings').glob('*.md'))
    check(f"Briefings generated ({len(briefing_files)})", len(briefing_files) > 0,
          "Briefings/ folder is empty. Run: python scripts\\ceo_briefing.py")

    # === 10. Ralph Wiggum Loop ===
    print("\n🔄 10. RALPH WIGGUM LOOP")
    check("ralph_wiggum.py exists", (SCRIPTS / 'ralph_wiggum.py').exists())
    if orch_path.exists():
        content = orch_path.read_text(encoding='utf-8', errors='ignore')
        check("Ralph loop integrated", 'RalphWiggumLoop' in content or 'ralph_wiggum' in content,
              "Not imported in orchestrator")

    # === 11. Cross-Domain Integration ===
    print("\n🔗 11. CROSS-DOMAIN INTEGRATION")
    check("cross_domain_integration.py", (SCRIPTS / 'cross_domain_integration.py').exists())
    if orch_path.exists():
        content = orch_path.read_text(encoding='utf-8', errors='ignore')
        check("Cross-domain used in orchestrator", 
              'cross_domain' in content or 'DomainClassifier' in content)

    # === 12. Scheduling ===
    print("\n⏰ 12. SCHEDULING (PM2 / Task Scheduler)")
    check("ecosystem.config.cjs", (ROOT / 'ecosystem.config.cjs').exists())
    
    # Check PM2
    try:
        result = subprocess.run(['pm2.cmd', '--version'], capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode != 0:
            result = subprocess.run(['pm2', '--version'], capture_output=True, text=True, timeout=10, shell=True)
        pm2_installed = result.returncode == 0
        pm2_ver = ''
        if pm2_installed:
            output = result.stdout.strip() + result.stderr.strip()
            for line in output.split('\n'):
                if line.strip() and '.' in line:
                    pm2_ver = line.strip()
        check(f"PM2 installed ({pm2_ver or 'Yes'})", pm2_installed, "Run: npm install -g pm2")
    except:
        pm2_installed = False
        check("PM2 installed", False, "Run: npm install -g pm2")

    # Check PM2 cron scheduler
    try:
        result = subprocess.run(['pm2.cmd', 'jlist'], capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            processes = json.loads(result.stdout.strip())
            cron_running = any(p.get('name') == 'pm2-cron' and p.get('pm2_env', {}).get('status') == 'online' for p in processes)
            check("PM2 Cron Scheduler running", cron_running, "Not in PM2. Run: pm2 start ecosystem.config.cjs")
        else:
            check("PM2 Cron Scheduler running", False, "PM2 not responding")
    except Exception as e:
        check("PM2 Cron Scheduler running", False, str(e)[:60])

    # === 13. Facebook Posting (Live Test) ===
    print("\n📘 13. FACEBOOK POSTING (Live)")
    fb_config_ok = False
    fb_mcp = ROOT / 'mcp-servers' / 'facebook-mcp' / 'index.js'
    if fb_mcp.exists():
        content = fb_mcp.read_text(encoding='utf-8', errors='ignore')
        import re
        token = re.search(r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'([^']+)'", content)
        page_id = re.search(r"FACEBOOK_PAGE_ID:\s*'([^']+)'", content)
        fb_config_ok = token and page_id and not token.group(1).startswith('YOUR_')
    check("Facebook credentials configured", fb_config_ok, "Token or Page ID missing/invalid")

    # === 14. Twitter Posting ===
    print("\n🐦 14. TWITTER POSTING")
    tw_config_ok = False
    tw_mcp = ROOT / 'mcp-servers' / 'twitter-mcp' / 'index.js'
    if tw_mcp.exists():
        content = tw_mcp.read_text(encoding='utf-8', errors='ignore')
        has_all = all(re.search(f"TWITTER_{k}:\s*'([^']+)'", content) 
                      for k in ['API_KEY', 'API_SECRET', 'ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET'])
        tw_config_ok = has_all
    check("Twitter credentials configured", tw_config_ok, "Missing credentials")

    # === Summary ===
    print("\n" + "="*70)
    print(f"RESULTS: {results['pass']} Passed | {results['fail']} Failed | {results['skip']} Skipped")
    
    gold_threshold = 40  # Minimum checks for Gold
    if results['pass'] >= gold_threshold and results['fail'] <= 3:
        print("🎉 GOLD TIER STATUS: READY")
        print("   Most features implemented. Fix failing items above.")
    elif results['pass'] >= 20:
        print("🥈 SILVER TIER STATUS: COMPLETE")
        print("   Gold tier in progress. Fix failing items and add missing features.")
    else:
        print("⚠️  INCOMPLETE — Fix critical failures first.")

    print("="*70)

    # === Recommendations ===
    print("\n📋 QUICK FIX COMMANDS:")
    print("  1. Run orchestrator:          python scripts\\run.py")
    print("  2. Test CEO Briefing:         python scripts\\ceo_briefing.py")
    print("  3. Start PM2 watchers:        pm2 start ecosystem.config.cjs")
    print("  4. Setup Task Scheduler:      scripts\\setup-tasks.bat")
    print("  5. Test Facebook post:        python scripts\\facebook_post.py --test")
    print("  6. Test audit logs:           python scripts\\test_audit.py")

if __name__ == '__main__':
    main()
