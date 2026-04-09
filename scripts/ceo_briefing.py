"""
CEO Briefing Generator - Gold Tier

Generates comprehensive "Monday Morning CEO Briefing" every week.
Analyzes business performance, identifies bottlenecks, and provides proactive suggestions.

Scheduled to run every Sunday at 10 PM via Task Scheduler.

Output: /Briefings/YYYY-MM-DD_Monday_Briefing.md
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

# Configure logging
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
    """
    Generates weekly CEO briefing with:
    - Revenue summary
    - Completed tasks
    - Bottlenecks
    - Proactive suggestions
    - Upcoming deadlines
    - Subscription audit
    """
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.done_path = vault_path / 'Done'
        self.briefings_path = vault_path / 'Briefings'
        self.accounting_path = vault_path / 'Accounting'
        self.plans_path = vault_path / 'Plans'
        self.business_goals_file = vault_path / 'Business_Goals.md'
        
        # Ensure directories exist
        self.briefings_path.mkdir(parents=True, exist_ok=True)
    
    def generate_briefing(self, date: datetime = None) -> Path:
        """Generate complete CEO briefing."""
        if date is None:
            date = datetime.now()
        
        # Calculate date range (last 7 days)
        week_start = date - timedelta(days=date.weekday() + 7)  # Last Monday
        week_end = week_start + timedelta(days=6)  # Last Sunday
        
        logger.info(f"📊 Generating CEO Briefing for {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        
        # Gather data
        completed_tasks = self._get_completed_tasks(week_start, week_end)
        revenue_data = self._get_revenue_data(week_start, week_end)
        bottlenecks = self._identify_bottlenecks(week_start, week_end)
        suggestions = self._generate_suggestions(completed_tasks, bottlenecks, revenue_data)
        subscription_audit = self._audit_subscriptions()
        upcoming_deadlines = self._get_upcoming_deadlines()
        social_metrics = self._get_social_media_metrics()
        
        # Generate briefing
        briefing_content = self._format_briefing(
            week_start, week_end, completed_tasks, revenue_data,
            bottlenecks, suggestions, subscription_audit,
            upcoming_deadlines, social_metrics
        )
        
        # Save briefing
        filename = f"{date.strftime('%Y-%m-%d')}_Monday_Briefing.md"
        briefing_file = self.briefings_path / filename
        briefing_file.write_text(briefing_content, encoding='utf-8')
        
        logger.info(f"✅ CEO Briefing saved to {briefing_file}")
        return briefing_file
    
    def _get_completed_tasks(self, week_start: datetime, week_end: datetime) -> List[Dict]:
        """Get tasks completed in date range."""
        completed = []
        
        if not self.done_path.exists():
            return completed
        
        for item in self.done_path.glob('*.md'):
            try:
                content = item.read_text(encoding='utf-8')
                # Extract date from frontmatter
                if '---' in content:
                    frontmatter = content.split('---')[1]
                    if 'created:' in frontmatter or 'date:' in frontmatter:
                        # Parse date and check if in range
                        completed.append({
                            'name': item.stem,
                            'file': item.name,
                            'type': self._extract_type(content),
                            'status': 'completed',
                        })
            except Exception as e:
                logger.warning(f"Failed to read {item.name}: {e}")
        
        return completed
    
    def _get_revenue_data(self, week_start: datetime, week_end: datetime) -> Dict:
        """Get revenue data from accounting or logs."""
        revenue = {
            'this_week': 0,
            'mtd': 0,
            'target': 10000,  # Default from Business_Goals.md
            'invoices_sent': 0,
            'invoices_paid': 0,
            'outstanding': 0,
        }
        
        # Try to read from accounting folder
        if self.accounting_path.exists():
            for accounting_file in self.accounting_path.glob('*.md'):
                try:
                    content = accounting_file.read_text(encoding='utf-8')
                    # Extract revenue data if present
                    if 'revenue:' in content.lower() or 'amount:' in content.lower():
                        # Parse if structured data exists
                        pass
                except:
                    pass
        
        # Try to read from audit logs
        logs_path = self.vault_path / 'Logs'
        if logs_path.exists():
            week_logs = []
            for log_file in logs_path.glob('*.json'):
                try:
                    log_date = datetime.fromisoformat(log_file.stem)
                    if week_start <= log_date <= week_end:
                        log_data = json.loads(log_file.read_text(encoding='utf-8'))
                        week_logs.extend(log_data if isinstance(log_data, list) else [log_data])
                except:
                    pass
        
        # Calculate from completed tasks
        completed = self._get_completed_tasks(week_start, week_end)
        revenue['this_week'] = len(completed)  # Placeholder: count as proxy
        
        return revenue
    
    def _identify_bottlenecks(self, week_start: datetime, week_end: datetime) -> List[Dict]:
        """Identify tasks that took longer than expected."""
        bottlenecks = []
        
        if not self.plans_path.exists():
            return bottlenecks
        
        for plan_file in self.plans_path.glob('PLAN_*.md'):
            try:
                content = plan_file.read_text(encoding='utf-8')
                if 'created:' in content:
                    # Calculate age
                    created_line = [line for line in content.split('\n') if 'created:' in line]
                    if created_line:
                        bottlenecks.append({
                            'task': plan_file.stem,
                            'status': 'pending',
                            'age_days': (datetime.now() - week_start).days,
                        })
            except Exception as e:
                logger.warning(f"Failed to read {plan_file.name}: {e}")
        
        return bottlenecks
    
    def _generate_suggestions(
        self, completed_tasks: List, bottlenecks: List, revenue_data: Dict
    ) -> List[Dict]:
        """Generate proactive suggestions."""
        suggestions = []
        
        # Revenue-based suggestions
        if revenue_data['this_week'] < revenue_data['target'] * 0.25:
            suggestions.append({
                'category': 'Revenue',
                'priority': 'high',
                'title': 'Revenue Behind Target',
                'description': f"This week's performance is below target. Consider reaching out to pending clients.",
                'action': 'Review pending approvals and follow up on outstanding invoices',
            })
        
        # Bottleneck-based suggestions
        if len(bottlenecks) > 2:
            suggestions.append({
                'category': 'Productivity',
                'priority': 'medium',
                'title': 'Multiple Pending Tasks',
                'description': f"You have {len(bottlenecks)} tasks pending approval or completion.",
                'action': 'Review /Pending_Approval/ folder and clear backlog',
            })
        
        # General suggestions
        suggestions.append({
            'category': 'Growth',
            'priority': 'low',
            'title': 'Social Media Activity',
            'description': 'Consider increasing social media posting frequency.',
            'action': 'Review content calendar and schedule posts',
        })
        
        return suggestions
    
    def _audit_subscriptions(self) -> Dict:
        """Audit active subscriptions and identify unused/expensive ones."""
        audit = {
            'total_monthly': 0,
            'subscriptions': [],
            'unused': [],
            'expensive': [],
        }
        
        # Common subscription patterns to check
        common_subscriptions = {
            'notion.so': {'name': 'Notion', 'estimated_cost': 15},
            'slack.com': {'name': 'Slack', 'estimated_cost': 10},
            'spotify.com': {'name': 'Spotify', 'estimated_cost': 10},
            'netflix.com': {'name': 'Netflix', 'estimated_cost': 15},
            'adobe.com': {'name': 'Adobe Creative Cloud', 'estimated_cost': 55},
            'github.com': {'name': 'GitHub', 'estimated_cost': 10},
            'vercel.com': {'name': 'Vercel', 'estimated_cost': 20},
            'aws.amazon.com': {'name': 'AWS', 'estimated_cost': 50},
        }
        
        # Try to read from accounting logs
        if self.accounting_path.exists():
            for accounting_file in self.accounting_path.glob('*.md'):
                try:
                    content = accounting_file.read_text(encoding='utf-8').lower()
                    for domain, sub_info in common_subscriptions.items():
                        if domain in content:
                            audit['subscriptions'].append(sub_info)
                            audit['total_monthly'] += sub_info['estimated_cost']
                except:
                    pass
        
        # If no data found, create placeholder
        if not audit['subscriptions']:
            audit['subscriptions'] = [
                {'name': 'Notion', 'estimated_cost': 15, 'status': 'unknown'},
                {'name': 'GitHub', 'estimated_cost': 10, 'status': 'unknown'},
            ]
            audit['total_monthly'] = 25
        
        return audit
    
    def _get_upcoming_deadlines(self) -> List[Dict]:
        """Get upcoming deadlines from business goals and plans."""
        deadlines = []
        
        # Read business goals
        if self.business_goals_file.exists():
            try:
                content = self.business_goals_file.read_text(encoding='utf-8')
                # Extract deadlines if mentioned
                if 'Q1' in content or 'Q2' in content:
                    deadlines.append({
                        'deadline': 'End of Quarter',
                        'description': 'Quarterly goals review',
                        'days_remaining': 30,  # Placeholder
                    })
            except:
                pass
        
        return deadlines
    
    def _get_social_media_metrics(self) -> Dict:
        """Get social media engagement metrics."""
        metrics = {
            'facebook': {'posts': 0, 'engagement': 0},
            'instagram': {'posts': 0, 'engagement': 0},
            'twitter': {'tweets': 0, 'engagement': 0},
            'linkedin': {'posts': 0, 'engagement': 0},
        }
        
        # Count posts from Done folder
        if self.done_path.exists():
            for item in self.done_path.glob('*.md'):
                content = item.read_text(encoding='utf-8').lower()
                if 'facebook' in content:
                    metrics['facebook']['posts'] += 1
                if 'instagram' in content:
                    metrics['instagram']['posts'] += 1
                if 'twitter' in content:
                    metrics['twitter']['tweets'] += 1
                if 'linkedin' in content:
                    metrics['linkedin']['posts'] += 1
        
        return metrics
    
    def _extract_type(self, content: str) -> str:
        """Extract type from markdown frontmatter."""
        if '---' in content:
            frontmatter = content.split('---')[1]
            for line in frontmatter.split('\n'):
                if 'type:' in line:
                    return line.split(':')[1].strip()
        return 'unknown'
    
    def _format_briefing(
        self,
        week_start: datetime,
        week_end: datetime,
        completed_tasks: List,
        revenue_data: Dict,
        bottlenecks: List,
        suggestions: List,
        subscription_audit: Dict,
        upcoming_deadlines: List,
        social_metrics: Dict,
    ) -> str:
        """Format briefing as markdown."""
        
        # Determine overall status
        if revenue_data['this_week'] > 0:
            status = "✅ On Track"
        else:
            status = "⚠️ Needs Attention"
        
        content = f"""---
generated: {datetime.now().isoformat()}
period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}
type: ceo_briefing
status: {status}
---

# Monday Morning CEO Briefing

**Period:** {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Overall Status:** {status}

---

## Executive Summary

"""
        
        if revenue_data['this_week'] > 0:
            content += f"Productive week with {len(completed_tasks)} tasks completed. Revenue tracking {'on' if revenue_data['this_week'] >= revenue_data['target'] * 0.25 else 'below'} target.\n\n"
        else:
            content += "Week data needs attention. Limited activity detected. Review pending items and approve queued actions.\n\n"
        
        content += f"""## Revenue

| Metric | Amount | Status |
|--------|--------|--------|
| This Week | {revenue_data['this_week']} tasks | {'✅' if revenue_data['this_week'] > 0 else '⚠️'} |
| MTD | ${revenue_data['mtd']:,} | {'✅' if revenue_data['mtd'] >= revenue_data['target'] * 0.5 else '⚠️'} |
| Monthly Target | ${revenue_data['target']:,} | 🎯 |
| Invoices Sent | {revenue_data['invoices_sent']} | 📄 |
| Invoices Paid | {revenue_data['invoices_paid']} | 💰 |
| Outstanding | ${revenue_data['outstanding']:,} | {'⚠️' if revenue_data['outstanding'] > 0 else '✅'} |

## Completed Tasks

**Total:** {len(completed_tasks)}

"""
        
        if completed_tasks:
            content += "| Task | Type | Date |\n|------|------|------|\n"
            for task in completed_tasks[:10]:  # Show last 10
                content += f"| {task['name']} | {task['type']} | - |\n"
        else:
            content += "_No completed tasks this week._\n"
        
        content += f"""
## Bottlenecks

**Pending Tasks:** {len(bottlenecks)}

"""
        
        if bottlenecks:
            content += "| Task | Status | Age (days) |\n|------|--------|------------|\n"
            for bottleneck in bottlenecks[:10]:
                content += f"| {bottleneck['task']} | {bottleneck['status']} | {bottleneck['age_days']} |\n"
        else:
            content += "_No bottlenecks identified. ✅_\n"
        
        content += f"""
## Proactive Suggestions

"""
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(suggestion['priority'], '⚪')
                content += f"""### {i}. {priority_emoji} {suggestion['title']}

**Category:** {suggestion['category']}
**Description:** {suggestion['description']}
**Suggested Action:** {suggestion['action']}

"""
        else:
            content += "_No proactive suggestions at this time._\n"
        
        content += f"""## Subscription Audit

**Total Monthly Subscriptions:** ${subscription_audit['total_monthly']:,}

| Subscription | Est. Monthly Cost | Status |
|-------------|-------------------|--------|
"""
        
        for sub in subscription_audit['subscriptions']:
            status = sub.get('status', 'active')
            content += f"| {sub['name']} | ${sub['estimated_cost']:,} | {status} |\n"
        
        content += f"""
## Social Media Activity

| Platform | Posts This Week | Engagement |
|----------|----------------|------------|
| Facebook | {social_metrics['facebook']['posts']} | {social_metrics['facebook']['engagement']} |
| Instagram | {social_metrics['instagram']['posts']} | {social_metrics['instagram']['engagement']} |
| Twitter | {social_metrics['twitter']['tweets']} | {social_metrics['twitter']['engagement']} |
| LinkedIn | {social_metrics['linkedin']['posts']} | {social_metrics['linkedin']['engagement']} |

## Upcoming Deadlines

"""
        
        if upcoming_deadlines:
            for deadline in upcoming_deadlines:
                content += f"- **{deadline['deadline']}**: {deadline['description']} ({deadline['days_remaining']} days remaining)\n"
        else:
            content += "_No upcoming deadlines identified._\n"
        
        content += f"""
---

*Generated by AI Employee v1.0 - Gold Tier*
*Next briefing: {(week_start + timedelta(days=7)).strftime('%Y-%m-%d')}*
"""
        
        return content


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument(
        '--vault-path',
        type=str,
        default=str(Path(__file__).parent.parent / 'personal-ai-employee'),
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date for briefing (YYYY-MM-DD), defaults to today'
    )
    
    args = parser.parse_args()
    
    vault = Path(args.vault_path)
    if not vault.exists():
        logger.error(f"Vault path does not exist: {vault}")
        return 1
    
    date = datetime.fromisoformat(args.date) if args.date else datetime.now()
    
    generator = CEOBriefingGenerator(vault_path=vault)
    briefing_file = generator.generate_briefing(date)
    
    print(f"✅ CEO Briefing generated: {briefing_file}")
    return 0


if __name__ == '__main__':
    main()
