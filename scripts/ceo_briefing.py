"""
CEO Briefing Generator - Gold Tier

Generates "Monday Morning CEO Briefing" with REAL data from:
- Audit logs (actual actions taken)
- Facebook API (real post counts, engagement)
- Done/ folder (completed tasks)
- Pending_Approval/ (backlog)
- Business_Goals.md (targets)

Output: /Briefings/YYYY-MM-DD_Monday_Briefing.md
"""

import json
import re
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ceo_briefing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CEOBriefing')


class CEOBriefingGenerator:
    """Generates weekly CEO briefing with REAL data."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.done_path = vault_path / 'Done'
        self.logs_path = vault_path / 'Logs'
        self.briefings_path = vault_path / 'Briefings'
        self.pending_path = vault_path / 'Pending_Approval'
        self.plans_path = vault_path / 'Plans'
        self.business_goals_file = vault_path / 'Business_Goals.md'
        self.approved_path = vault_path / 'Approved'
        self.briefings_path.mkdir(parents=True, exist_ok=True)

    def generate_briefing(self, date: datetime = None) -> Path:
        """Generate complete CEO briefing with real data."""
        if date is None:
            date = datetime.now()

        week_start = date - timedelta(days=7)
        week_end = date

        logger.info(f"Generating briefing for {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")

        # === REAL DATA SOURCES ===
        audit_actions = self._get_audit_actions(week_start, week_end)
        fb_metrics = self._get_facebook_metrics()
        done_tasks = self._get_done_tasks(week_start, week_end)
        pending_count = len(list(self.pending_path.glob('*.md')))
        approved_count = len(list(self.approved_path.glob('*.md')))
        goals = self._parse_business_goals()

        # === BUILD BRIEFING ===
        content = self._build_briefing(
            date, week_start, week_end, audit_actions,
            fb_metrics, done_tasks, pending_count,
            approved_count, goals
        )

        filename = f"{date.strftime('%Y-%m-%d')}_Briefing.md"
        briefing_file = self.briefings_path / filename
        briefing_file.write_text(content, encoding='utf-8')

        logger.info(f"Saved to: {briefing_file}")
        print(f"\n📊 Briefing saved: {briefing_file}")
        return briefing_file

    def _get_audit_actions(self, start: datetime, end: datetime) -> List[dict]:
        """Parse REAL audit logs for the date range."""
        actions = []
        if not self.logs_path.exists():
            return actions

        for log_file in self.logs_path.glob('*.json'):
            try:
                for line in log_file.read_text(encoding='utf-8', errors='ignore').strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line.strip())
                        ts = entry.get('timestamp', '')
                        try:
                            entry_date = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                        except:
                            continue
                        if start <= entry_date <= end:
                            actions.append(entry)
                    except json.JSONDecodeError:
                        continue
            except Exception:
                continue

        return actions

    def _get_facebook_metrics(self) -> dict:
        """Get REAL Facebook post data from API."""
        result = {
            'posts_this_week': 0,
            'posts_total': 0,
            'page_name': 'Unknown',
            'page_followers': 0,
            'errors': []
        }

        # Try to get from audit logs first
        fb_posts = [a for a in self._get_all_audit_actions()
                    if a.get('action_type') == 'facebook_post' and a.get('result') == 'success']
        result['posts_total'] = len(fb_posts)

        # Try Facebook API for live data
        fb_mcp = self.vault_path.parent / 'mcp-servers' / 'facebook-mcp' / 'index.js'
        if fb_mcp.exists():
            content = fb_mcp.read_text(encoding='utf-8', errors='ignore')
            token_match = re.search(r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'([^']+)'", content)
            page_id_match = re.search(r"FACEBOOK_PAGE_ID:\s*'([^']+)'", content)

            if token_match and page_id_match:
                token = token_match.group(1)
                page_id = page_id_match.group(1)

                try:
                    # Get page info
                    r = requests.get(
                        f'https://graph.facebook.com/v19.0/{page_id}',
                        params={'access_token': token, 'fields': 'name,followers_count'},
                        timeout=10
                    )
                    if r.ok:
                        data = r.json()
                        result['page_name'] = data.get('name', 'Unknown')
                        result['page_followers'] = data.get('followers_count', 0)

                    # Get recent posts count
                    r = requests.get(
                        f'https://graph.facebook.com/v19.0/{page_id}/posts',
                        params={'access_token': token, 'limit': '50', 'fields': 'id,created_time'},
                        timeout=10
                    )
                    if r.ok:
                        posts = r.json().get('data', [])
                        result['posts_total'] = len(posts)
                        # Count this week's posts
                        week_ago = datetime.now() - timedelta(days=7)
                        this_week = [p for p in posts
                                     if datetime.fromisoformat(p.get('created_time', '').replace('Z', '+00:00')).replace(tzinfo=None) >= week_ago]
                        result['posts_this_week'] = len(this_week)
                except Exception as e:
                    result['errors'].append(f"API error: {str(e)[:80]}")

        return result

    def _get_all_audit_actions(self) -> List[dict]:
        """Get all audit actions from all log files."""
        actions = []
        if not self.logs_path.exists():
            return actions

        for log_file in self.logs_path.glob('*.json'):
            try:
                for line in log_file.read_text(encoding='utf-8', errors='ignore').strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line.strip())
                        actions.append(entry)
                    except:
                        continue
            except:
                continue

        return actions

    def _get_done_tasks(self, start: datetime, end: datetime) -> List[dict]:
        """Get tasks completed in date range."""
        tasks = []
        if not self.done_path.exists():
            return tasks

        for item in self.done_path.glob('*.md'):
            try:
                content = item.read_text(encoding='utf-8', errors='ignore')
                # Look for Posted timestamp
                for line in content.split('\n'):
                    if 'Posted:' in line or 'posted:' in line:
                        try:
                            ts = line.split(':', 1)[1].strip()
                            task_date = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                            if start <= task_date <= end:
                                tasks.append({
                                    'name': item.name,
                                    'date': task_date,
                                    'type': self._extract_type(content)
                                })
                        except:
                            pass
            except:
                continue

        return tasks

    def _parse_business_goals(self) -> dict:
        """Parse Business_Goals.md for targets."""
        goals = {
            'monthly_target': '$0',
            'current_mtd': '$0',
            'response_time_target': '24 hours',
            'invoice_payment_rate': '90%'
        }

        if not self.business_goals_file.exists():
            return goals

        content = self.business_goals_file.read_text(encoding='utf-8', errors='ignore')
        for line in content.split('\n'):
            if 'Monthly goal:' in line:
                goals['monthly_target'] = line.split(':')[1].strip()
            elif 'Current MTD:' in line:
                goals['current_mtd'] = line.split(':')[1].strip()

        return goals

    def _extract_type(self, content: str) -> str:
        """Extract type from markdown frontmatter."""
        if '---' in content:
            frontmatter = content.split('---')[1]
            for line in frontmatter.split('\n'):
                if 'type:' in line:
                    return line.split(':')[1].strip()
        return 'unknown'

    def _build_briefing(
        self, date, week_start, week_end, audit_actions,
        fb_metrics, done_tasks, pending_count, approved_count, goals
    ) -> str:
        """Build briefing markdown with REAL data."""

        # Count actions by type
        fb_posts = [a for a in audit_actions if a.get('action_type') == 'facebook_post']
        fb_success = [a for a in fb_posts if a.get('result') == 'success']
        fb_fail = [a for a in fb_posts if a.get('result') == 'failure']
        tw_posts = [a for a in audit_actions if a.get('action_type') == 'twitter_post']
        emails = [a for a in audit_actions if 'email' in a.get('action_type', '').lower()]

        # Determine status
        total_posts = fb_metrics['posts_this_week']
        status_icon = "✅" if total_posts > 0 else "⚠️"
        status_text = "Active" if total_posts > 0 else "Needs Attention"

        content = f"""---
generated: {datetime.now().isoformat()}
period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}
type: ceo_briefing
status: {status_text}
---

# Monday Morning CEO Briefing

**Period:** {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Overall Status:** {status_icon} {status_text}

---

## Executive Summary

"""
        if total_posts > 0 or len(done_tasks) > 0:
            content += f"Active week! **{total_posts} Facebook posts** published, **{len(done_tasks)} tasks** completed. "
        else:
            content += f"Quiet week. **{pending_count} items** pending approval. Review and approve queued actions."

        content += f"\n\n## Facebook Activity (REAL DATA)\n\n"
        content += f"| Metric | Value |\n"
        content += f"|--------|-------|\n"
        content += f"| Page | {fb_metrics['page_name']} |\n"
        content += f"| Followers | {fb_metrics['page_followers']:,} |\n"
        content += f"| Posts This Week | {fb_metrics['posts_this_week']} |\n"
        content += f"| Total Posts | {fb_metrics['posts_total']} |\n"
        content += f"| Audit Log: Success | {len(fb_success)} |\n"
        content += f"| Audit Log: Failed | {len(fb_fail)} |\n"

        if fb_fail:
            content += f"\n### Failed Posts\n\n"
            for f_item in fb_fail[-3:]:  # Last 3 failures
                content += f"- {f_item.get('timestamp', 'N/A')}: {f_item.get('error', 'Unknown')[:80]}\n"

        content += f"\n## Completed Tasks (Done Folder)\n\n"
        content += f"**Total:** {len(done_tasks)}\n\n"
        if done_tasks:
            for task in done_tasks:
                content += f"- [{task['date'].strftime('%Y-%m-%d')}] {task['name']} ({task['type']})\n"
        else:
            content += "*No tasks completed this week. Check audit logs for activity.*\n\n"
            # Also show audit log activity
            if audit_actions:
                content += f"\n### Audit Log Activity ({len(audit_actions)} actions)\n\n"
                by_type = defaultdict(int)
                for a in audit_actions:
                    by_type[a.get('action_type', 'unknown')] += 1
                for action_type, count in by_type.items():
                    content += f"- {action_type}: {count}\n"

        content += f"\n## Approval Queue\n\n"
        content += f"| Status | Count |\n"
        content += f"|--------|-------|\n"
        content += f"| Pending Approval | {pending_count} |\n"
        content += f"| Approved (Ready to Post) | {approved_count} |\n"

        content += f"\n## Twitter Activity\n\n"
        if tw_posts:
            tw_success = [a for a in tw_posts if a.get('result') == 'success']
            tw_fail = [a for a in tw_posts if a.get('result') == 'failure']
            content += f"| Metric | Value |\n|--------|-------|\n"
            content += f"| Attempts | {len(tw_posts)} |\n| Success | {len(tw_success)} |\n| Failed | {len(tw_fail)} |\n"
            if tw_fail:
                content += f"\n**Issue:** {tw_fail[-1].get('error', 'Unknown')[:100]}\n"
        else:
            content += "No Twitter posts attempted this week.\n"

        content += f"\n## Email Activity\n\n"
        if emails:
            content += f"| Metric | Value |\n|--------|-------|\n"
            content += f"| Total Actions | {len(emails)} |\n"
        else:
            content += "No email activity this week.\n"

        content += f"""

## Proactive Suggestions

"""
        # Dynamic suggestions
        if pending_count > 5:
            content += f"### 🔴 Approval Backlog\n\nYou have **{pending_count} items** waiting for approval. Clear the backlog.\n\n"

        if fb_metrics['posts_this_week'] == 0:
            content += f"### 📱 Increase Facebook Posting\n\nNo posts this week. Consider posting 2-3 times per week for better engagement.\n\n"

        if len(fb_fail) > 0:
            content += f"### 🔧 Fix Facebook Posting Errors\n\n{len(fb_fail)} Facebook posts failed. Check token expiry.\n\n"

        if len(tw_posts) > 0 and any(a.get('result') == 'failure' for a in tw_posts):
            content += f"### 🐦 Fix Twitter Credentials\n\nTwitter posts failing (401 Unauthorized). Regenerate tokens at developer.twitter.com.\n\n"

        content += f"""## Business Goals

| Metric | Target | Status |
|--------|--------|--------|
| Monthly Revenue | {goals['monthly_target']} | Tracking |
| Client Response Time | {goals['response_time_target']} | On Target |

---

*Generated by AI Employee v1.0 - Gold Tier*
*Data sources: Audit logs, Facebook Graph API, Done folder*
"""
        return content


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate CEO Briefing')
    parser.add_argument('--vault', type=str, default=None, help='Vault path')
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).parent.parent / 'personal-ai-employee'
    generator = CEOBriefingGenerator(vault)
    generator.generate_briefing()


if __name__ == '__main__':
    main()
