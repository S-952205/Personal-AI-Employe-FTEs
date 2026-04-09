"""
Cross-Domain Integration - Gold Tier

Handles integration between Personal and Business domains:
- Domain-aware processing rules
- Cross-domain triggers
- Unified dashboard updates
- Business metrics tracking

This module enhances the orchestrator with:
1. Domain classification (Personal vs Business)
2. Different approval thresholds per domain
3. Cross-domain trigger detection
4. Unified dashboard with business metrics
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger('CrossDomainIntegration')


class DomainClassifier:
    """Classifies items into Personal or Business domains."""
    
    # Business indicators
    BUSINESS_KEYWORDS = [
        'invoice', 'payment', 'client', 'customer', 'project', 'proposal',
        'budget', 'contract', 'meeting', 'deadline', 'deliverable', 'milestone',
        'revenue', 'sales', 'marketing', 'lead', 'prospect', 'business',
        'company', 'organization', 'team', 'department', 'report',
    ]
    
    # Personal indicators
    PERSONAL_KEYWORDS = [
        'family', 'friend', 'personal', 'birthday', 'dinner', 'party',
        'vacation', 'travel', 'health', 'doctor', 'gym', 'fitness',
        'shopping', 'entertainment', 'movie', 'music', 'game',
    ]
    
    # Business sender domains
    BUSINESS_DOMAINS = [
        'company.com', 'business.com', 'corp.com',
    ]
    
    def classify(self, content: str, metadata: Dict = None) -> str:
        """
        Classify content as 'personal' or 'business'.
        Returns domain string.
        """
        content_lower = content.lower()
        
        # Count keyword matches
        business_score = sum(1 for kw in self.BUSINESS_KEYWORDS if kw in content_lower)
        personal_score = sum(1 for kw in self.PERSONAL_KEYWORDS if kw in content_lower)
        
        # Check metadata
        if metadata:
            from_email = metadata.get('from', '').lower()
            subject = metadata.get('subject', '').lower()
            
            # Check sender domain
            if any(domain in from_email for domain in self.BUSINESS_DOMAINS):
                business_score += 3
            
            # Check subject line
            business_score += sum(1 for kw in self.BUSINESS_KEYWORDS if kw in subject)
            personal_score += sum(1 for kw in self.PERSONAL_KEYWORDS if kw in subject)
        
        # Determine domain
        if business_score > personal_score:
            return 'business'
        elif personal_score > business_score:
            return 'personal'
        else:
            return 'unknown'


class ApprovalThresholdManager:
    """Manages different approval thresholds per domain."""
    
    # Default thresholds
    THRESHOLDS = {
        'personal': {
            'email_send': {'threshold': 'known_contacts', 'description': 'Auto-send to known contacts'},
            'social_post': {'threshold': 'always_approve', 'description': 'Always require approval'},
            'payment': {'threshold': 'never_auto', 'description': 'Always require approval'},
        },
        'business': {
            'email_send': {'threshold': 'always_approve', 'description': 'Always require approval'},
            'social_post': {'threshold': 'always_approve', 'description': 'Always require approval'},
            'payment': {'threshold': 'amount_based', 'amount': 500, 'description': 'Approve if > $500'},
            'invoice_create': {'threshold': 'always_approve', 'description': 'Always require approval'},
        },
    }
    
    def requires_approval(self, action: str, domain: str, context: Dict = None) -> bool:
        """
        Check if action requires approval based on domain rules.
        Returns True if approval needed.
        """
        domain_rules = self.THRESHOLDS.get(domain, self.THRESHOLDS['business'])
        action_rules = domain_rules.get(action, {'threshold': 'always_approve'})
        
        threshold = action_rules.get('threshold', 'always_approve')
        
        if threshold == 'always_approve':
            return True
        elif threshold == 'never_auto':
            return False
        elif threshold == 'known_contacts':
            # Auto-send if recipient in known contacts
            if context and context.get('recipient') in self._get_known_contacts():
                return False
            return True
        elif threshold == 'amount_based':
            # Auto-approve if amount below threshold
            max_amount = action_rules.get('amount', 500)
            if context and context.get('amount', 0) < max_amount:
                return False
            return True
        
        return True
    
    def _get_known_contacts(self) -> set:
        """Get known contacts from handbook or config."""
        # This would read from Company_Handbook.md
        # For now, return empty set (always approve)
        return set()


class CrossDomainTriggerDetector:
    """Detects triggers that span personal and business domains."""
    
    def check_triggers(self, item_path: Path, domain: str) -> List[Dict]:
        """
        Check if item should trigger actions in other domain.
        Returns list of triggers.
        """
        triggers = []
        content = item_path.read_text(encoding='utf-8') if item_path.exists() else ''
        
        # Client email on Gmail → Create task in Business domain
        if domain == 'personal' and self._is_client_email(content):
            triggers.append({
                'type': 'client_email_to_business_task',
                'description': 'Client email detected, creating business task',
                'target_domain': 'business',
                'action': 'create_business_task',
            })
        
        # Payment received → Update Odoo invoice status
        if domain == 'business' and self._is_payment_notification(content):
            triggers.append({
                'type': 'payment_received_update_odoo',
                'description': 'Payment notification detected, updating Odoo',
                'target_domain': 'business',
                'action': 'update_odoo_invoice',
            })
        
        return triggers
    
    def _is_client_email(self, content: str) -> bool:
        """Check if email is from client."""
        client_indicators = ['client', 'customer', 'project', 'invoice', 'contract']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in client_indicators)
    
    def _is_payment_notification(self, content: str) -> bool:
        """Check if content is payment notification."""
        payment_indicators = ['payment received', 'transaction complete', 'deposit confirmed']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in payment_indicators)


class UnifiedDashboardUpdater:
    """Updates Dashboard.md with both personal and business metrics."""
    
    def update_dashboard(
        self,
        vault_path: Path,
        metrics: Dict,
    ):
        """
        Update Dashboard.md with unified metrics.
        
        metrics dict should contain:
        - personal: {emails, messages, tasks}
        - business: {revenue, invoices, posts, leads}
        - health: {watchers, mcp_servers, errors}
        """
        dashboard_file = vault_path / 'Dashboard.md'
        
        now = datetime.now()
        
        content = f"""---
type: dashboard
last_updated: {now.strftime('%Y-%m-%d %H:%M')}
status: active
tier: gold
---

# AI Employee Dashboard - Gold Tier

## Executive Summary

| Metric | Personal | Business | Status |
|--------|----------|----------|--------|
| Pending Actions | {metrics.get('personal', {}).get('pending', 0)} | {metrics.get('business', {}).get('pending', 0)} | {'✅' if metrics.get('business', {}).get('pending', 0) < 5 else '⚠️'} |
| Completed Today | {metrics.get('personal', {}).get('completed_today', 0)} | {metrics.get('business', {}).get('completed_today', 0)} | ✅ |
| Revenue MTD | - | ${metrics.get('business', {}).get('revenue_mtd', 0):,} | {'✅' if metrics.get('business', {}).get('revenue_mtd', 0) > 0 else '⏳'} |

---

## Personal Domain

| Metric | Count | Status |
|--------|-------|--------|
| Unread Emails | {metrics.get('personal', {}).get('emails', 0)} | {'⚠️' if metrics.get('personal', {}).get('emails', 0) > 10 else '✅'} |
| Messages | {metrics.get('personal', {}).get('messages', 0)} | {'⚠️' if metrics.get('personal', {}).get('messages', 0) > 5 else '✅'} |
| Tasks Pending | {metrics.get('personal', {}).get('tasks', 0)} | {'⚠️' if metrics.get('personal', {}).get('tasks', 0) > 3 else '✅'} |

---

## Business Domain

### Revenue & Invoicing

| Metric | Value | Status |
|--------|-------|--------|
| Revenue This Week | ${metrics.get('business', {}).get('revenue_week', 0):,} | {'✅' if metrics.get('business', {}).get('revenue_week', 0) > 0 else '⏳'} |
| Revenue MTD | ${metrics.get('business', {}).get('revenue_mtd', 0):,} | {'✅' if metrics.get('business', {}).get('revenue_mtd', 0) >= 5000 else '⚠️'} |
| Invoices Outstanding | {metrics.get('business', {}).get('invoices_outstanding', 0)} | {'⚠️' if metrics.get('business', {}).get('invoices_outstanding', 0) > 5 else '✅'} |
| Pending Payments | ${metrics.get('business', {}).get('payments_pending', 0):,} | {'⚠️' if metrics.get('business', {}).get('payments_pending', 0) > 1000 else '✅'} |

### Social Media

| Platform | Posts This Week | Engagement |
|----------|----------------|------------|
| LinkedIn | {metrics.get('business', {}).get('linkedin_posts', 0)} | {metrics.get('business', {}).get('linkedin_engagement', 0)} |
| Facebook | {metrics.get('business', {}).get('facebook_posts', 0)} | {metrics.get('business', {}).get('facebook_engagement', 0)} |
| Instagram | {metrics.get('business', {}).get('instagram_posts', 0)} | {metrics.get('business', {}).get('instagram_engagement', 0)} |
| Twitter | {metrics.get('business', {}).get('twitter_tweets', 0)} | {metrics.get('business', {}).get('twitter_engagement', 0)} |

---

## Watcher Status

| Watcher | Status | Last Check | Domain |
|---------|--------|------------|--------|
| Gmail | {self._status_emoji(metrics.get('watchers', {}).get('gmail'))} | {metrics.get('watchers', {}).get('gmail_last', '-')} | Personal |
| LinkedIn | {self._status_emoji(metrics.get('watchers', {}).get('linkedin'))} | {metrics.get('watchers', {}).get('linkedin_last', '-')} | Business |
| File System | {self._status_emoji(metrics.get('watchers', {}).get('filesystem'))} | {metrics.get('watchers', {}).get('filesystem_last', '-')} | Both |
| Facebook | {self._status_emoji(metrics.get('watchers', {}).get('facebook'))} | {metrics.get('watchers', {}).get('facebook_last', '-')} | Business |
| Twitter | {self._status_emoji(metrics.get('watchers', {}).get('twitter'))} | {metrics.get('watchers', {}).get('twitter_last', '-')} | Business |

---

## MCP Server Status

| Server | Status | Circuit Breaker |
|--------|--------|----------------|
| Email | {self._status_emoji(metrics.get('mcp', {}).get('email'))} | {metrics.get('mcp', {}).get('email_breaker', 'N/A')} |
| LinkedIn | {self._status_emoji(metrics.get('mcp', {}).get('linkedin'))} | {metrics.get('mcp', {}).get('linkedin_breaker', 'N/A')} |
| Facebook | {self._status_emoji(metrics.get('mcp', {}).get('facebook'))} | {metrics.get('mcp', {}).get('facebook_breaker', 'N/A')} |
| Twitter | {self._status_emoji(metrics.get('mcp', {}).get('twitter'))} | {metrics.get('mcp', {}).get('twitter_breaker', 'N/A')} |
| Odoo | {self._status_emoji(metrics.get('mcp', {}).get('odoo'))} | {metrics.get('mcp', {}).get('odoo_breaker', 'N/A')} |

---

## Recent Activity

{self._format_recent_activity(metrics.get('recent_activity', []))}

---

## Quick Links

- [Inbox](./Inbox/) - Personal
- [Needs Action](./Needs_Action/) - All domains
- [Pending Approval](./Pending_Approval/) - HITL workflow
- [Approved](./Approved/) - Ready to execute
- [Done](./Done/) - Completed
- [Briefings](./Briefings/) - CEO briefings
- [Accounting](./Accounting/) - Odoo sync

---

## System Health

| Component | Status | Errors Today |
|-----------|--------|--------------|
| Orchestrator | {self._status_emoji(metrics.get('health', {}).get('orchestrator'))} | {metrics.get('health', {}).get('errors', 0)} |
| Ralph Wiggum Loop | {self._status_emoji(metrics.get('health', {}).get('ralph_wiggum'))} | - |
| Circuit Breakers | {self._status_emoji(metrics.get('health', {}).get('circuit_breakers'))} | {metrics.get('health', {}).get('open_breakers', 0)} open |

---

*Generated by AI Employee v1.0 - Gold Tier*
*Last full briefing: {metrics.get('last_briefing', 'Not yet generated')}*
"""
        
        dashboard_file.write_text(content, encoding='utf-8')
        logger.info("📊 Dashboard updated with Gold Tier metrics")
    
    def _status_emoji(self, status) -> str:
        """Convert status to emoji."""
        if status in ['online', 'running', 'closed', 'active']:
            return '✅'
        elif status in ['offline', 'stopped', 'open', 'error']:
            return '❌'
        elif status in ['starting', 'half_open']:
            return '⚠️'
        else:
            return '⏳'
    
    def _format_recent_activity(self, activities: List[Dict]) -> str:
        """Format recent activity as markdown table."""
        if not activities:
            return "_No recent activity._\n"
        
        table = "| Time | Type | Domain | Status |\n|------|------|--------|--------|\n"
        for activity in activities[:10]:
            time_str = activity.get('time', '-')[:16]
            type_str = activity.get('type', '-')
            domain = activity.get('domain', '-')
            status = activity.get('status', '-')
            table += f"| {time_str} | {type_str} | {domain} | {status} |\n"
        
        return table


# Global instances for use by orchestrator
classifier = DomainClassifier()
approval_manager = ApprovalThresholdManager()
trigger_detector = CrossDomainTriggerDetector()
dashboard_updater = UnifiedDashboardUpdater()


def classify_item(content: str, metadata: Dict = None) -> str:
    """Classify item into domain."""
    return classifier.classify(content, metadata)


def check_approval_required(action: str, domain: str, context: Dict = None) -> bool:
    """Check if action requires approval."""
    return approval_manager.requires_approval(action, domain, context)


def check_cross_domain_triggers(item_path: Path, domain: str) -> List[Dict]:
    """Check for cross-domain triggers."""
    return trigger_detector.check_triggers(item_path, domain)


def update_gold_dashboard(vault_path: Path, metrics: Dict):
    """Update dashboard with Gold Tier metrics."""
    dashboard_updater.update_dashboard(vault_path, metrics)
