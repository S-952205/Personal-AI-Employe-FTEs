"""
Orchestrator for AI Employee - Silver Tier

Enhanced orchestrator with HITL (Human-in-the-Loop) workflow,
multi-watcher support, and MCP server integration.

Uses Kilo Code for AI reasoning and processing.
"""

import subprocess
import logging
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

# Import audit logger for Gold Tier compliance
import sys
sys.path.insert(0, str(Path(__file__).parent))
from audit_logger import get_audit_logger, AuditLogger
from ralph_wiggum import RalphWiggumLoop
from cross_domain_integration import DomainClassifier, ApprovalThresholdManager

# Configure logging - file + clean console
import logging
import sys
import io
from logging.handlers import RotatingFileHandler

# Console handler - only show important messages
class CleanConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Only show warnings, errors, and specific info messages
        msg = record.getMessage()
        important = (
            record.levelno >= logging.WARNING or
            'Posted' in msg or
            'Moved to' in msg or
            'START' in msg or
            'STOP' in msg or
            'Error' in msg or
            'Failed' in msg or
            'Done' in msg
        )
        if important:
            super().emit(record)

# File handler (for audit trail)
file_handler = RotatingFileHandler('logs/orchestrator.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.DEBUG)

# Console handler (clean output)
console_handler = CleanConsoleHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
console_handler.setLevel(logging.INFO)

# Configure logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers = [file_handler, console_handler]

logger = logging.getLogger('Orchestrator')


class Orchestrator:
    """Main orchestrator for AI Employee with HITL workflow."""

    def __init__(self, vault_path: Path, check_interval: int = 30):
        self.vault_path = vault_path
        self.check_interval = check_interval

        # Key directories
        self.inbox_path = vault_path / 'Inbox'
        self.needs_action_path = vault_path / 'Needs_Action'
        self.done_path = vault_path / 'Done'
        self.plans_path = vault_path / 'Plans'
        self.approved_path = vault_path / 'Approved'
        self.pending_approval_path = vault_path / 'Pending_Approval'
        self.rejected_path = vault_path / 'Rejected'
        self.in_progress_path = vault_path / 'In_Progress'

        # Ensure all directories exist
        for path in [
            self.inbox_path, self.needs_action_path, self.done_path,
            self.plans_path, self.approved_path, self.pending_approval_path,
            self.rejected_path, self.in_progress_path
        ]:
            path.mkdir(parents=True, exist_ok=True)

        # Track processed files
        self.processed_files = set()

        # Core markdown files
        self.dashboard_path = vault_path / 'Dashboard.md'
        self.handbook_path = vault_path / 'Company_Handbook.md'
        self.business_goals_path = vault_path / 'Business_Goals.md'

        # MCP Server configuration
        self.mcp_config = self._load_mcp_config()
        
        # Initialize audit logger for Gold Tier compliance
        self.audit = get_audit_logger(vault_path)

        # Initialize cross-domain classifier
        self.domain_classifier = DomainClassifier()
        self.approval_thresholds = ApprovalThresholdManager()

    def _load_mcp_config(self) -> Dict:
        """Load MCP server configuration."""
        config_path = self.vault_path.parent / 'mcp-config.json'
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding='utf-8'))
            except Exception as e:
                logger.warning(f"Could not load MCP config: {e}")
        return {
            'email': {'enabled': True, 'require_approval_for_send': True},
            'linkedin': {'enabled': True, 'require_approval_for_post': True},
        }

    def get_pending_items(self) -> List[Path]:
        """Get all unprocessed .md files in Needs_Action."""
        if not self.needs_action_path.exists():
            return []

        pending = []
        for md_file in self.needs_action_path.glob('*.md'):
            # Skip if already in processed_files (in-memory tracking)
            if md_file.name in self.processed_files:
                continue

            # Skip if already processed (has approval request created status)
            content = md_file.read_text(encoding='utf-8')
            if '**Status:** Approval request created' in content:
                logger.debug(f"Skipping already processed: {md_file.name}")
                continue

            pending.append(md_file)

        return pending

    def get_approved_items(self) -> List[Path]:
        """Get all items in Approved folder awaiting action."""
        if not self.approved_path.exists():
            return []

        return list(self.approved_path.glob('*.md'))

    def get_pending_approvals(self) -> List[Path]:
        """Get all items awaiting human approval."""
        if not self.pending_approval_path.exists():
            return []

        return list(self.pending_approval_path.glob('*.md'))

    def update_dashboard(self, pending_count: int = None, approved_count: int = None, approval_pending_count: int = None):
        """Update Dashboard.md with REAL-TIME data from all sources.

        Pulls live counts from vault folders, audit logs, watchers, and MCP configs.
        Called after EVERY run cycle — never stale.
        """
        now = datetime.now()

        # If counts not provided, fetch live
        if pending_count is None:
            pending_count = len(list(self.needs_action_path.glob('*.md'))) if self.needs_action_path.exists() else 0
        if approved_count is None:
            approved_count = len(list(self.approved_path.glob('*.md'))) if self.approved_path.exists() else 0
        if approval_pending_count is None:
            approval_pending_count = len(list(self.pending_approval_path.glob('*.md'))) if self.pending_approval_path.exists() else 0

        # Live folder counts
        done_count = len(list(self.done_path.glob('*.md'))) if self.done_path.exists() else 0
        inbox_count = len(list(self.inbox_path.glob('*'))) if self.inbox_path.exists() else 0
        plans_count = len(list(self.plans_path.glob('*.md'))) if self.plans_path.exists() else 0
        in_progress_count = len(list(self.in_progress_path.glob('*.md'))) if self.in_progress_path.exists() else 0
        rejected_count = len(list(self.rejected_path.glob('*.md'))) if self.rejected_path.exists() else 0

        # Today's audit log stats
        today_audit_count = 0
        today_email_sent = 0
        today_fb_posts = 0
        today_tw_posts = 0
        today_errors = 0
        audit_log_file = self.vault_path / 'Logs' / f'{now.strftime("%Y-%m-%d")}.json'
        if audit_log_file.exists():
            try:
                for line in audit_log_file.read_text(encoding='utf-8', errors='ignore').strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line.strip())
                        today_audit_count += 1
                        atype = entry.get('action_type', '')
                        result = entry.get('result', '')
                        if atype == 'email_send' and result == 'success':
                            today_email_sent += 1
                        elif atype == 'facebook_post':
                            today_fb_posts += 1
                        elif atype == 'twitter_post':
                            today_tw_posts += 1
                        if atype.startswith('error_'):
                            today_errors += 1
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

        # MCP server status (read directly from mcp-config.json)
        servers_config = self.mcp_config.get('servers', {})
        email_mcp_status = '[...] Enabled' if not servers_config.get('email', {}).get('disabled', True) else '❌ Disabled'
        linkedin_mcp_status = '[...] Enabled' if not servers_config.get('linkedin', {}).get('disabled', True) else '❌ Disabled'
        facebook_mcp_status = '[...] Enabled' if not servers_config.get('facebook', {}).get('disabled', True) else '❌ Disabled'
        twitter_mcp_status = '[...] Enabled' if not servers_config.get('twitter', {}).get('disabled', True) else '❌ Disabled'
        odoo_mcp_status = '[...] Enabled' if not servers_config.get('odoo', {}).get('disabled', True) else '❌ Disabled'

        # Recent activity (last 5 done items)
        recent_activity = ""
        if self.done_path.exists():
            done_items = sorted(self.done_path.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
            if done_items:
                recent_activity = "| Time | File | Type |\n|------|------|------|\n"
                for item in done_items:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime).strftime('%H:%M')
                    item_type = 'unknown'
                    content = item.read_text(encoding='utf-8', errors='ignore')
                    if 'type:' in content:
                        try:
                            fm = content.split('---')[1]
                            for line in fm.split('\n'):
                                if line.strip().startswith('type:'):
                                    item_type = line.split(':', 1)[1].strip()
                                    break
                        except:
                            pass
                    recent_activity += f"| {mtime} | {item.name[:35]} | {item_type} |\n"
            else:
                recent_activity = "_No completed items yet._\n"

        # Build dashboard
        pending_status = "⚠️ Pending" if pending_count > 0 else "[...] Clear"
        approved_status_text = "[INFO] Ready" if approved_count > 0 else "[...] None"
        approval_status_text = "⏳ Awaiting Review" if approval_pending_count > 0 else "[...] None"

        content = f"""---
type: dashboard
last_updated: {now.strftime('%Y-%m-%d %H:%M:%S')}
status: active
tier: gold
---

# AI Employee Dashboard — Gold Tier

## Executive Summary (LIVE)

| Metric | Count | Status |
|--------|-------|--------|
| Needs Action | {pending_count} | {pending_status} |
| Approved (Ready to Execute) | {approved_count} | {approved_status_text} |
| Pending Approvals | {approval_pending_count} | {approval_status_text} |
| Done (Completed) | {done_count} | {'[...]' if done_count > 0 else '⏳'} |
| Inbox | {inbox_count} | ⏳ |
| Plans | {plans_count} | ⏳ |
| In Progress | {in_progress_count} | ⏳ |
| Rejected | {rejected_count} | {'⚠️' if rejected_count > 0 else '[...]'} |

---

## Today's Activity ({now.strftime('%Y-%m-%d')})

| Metric | Count |
|--------|-------|
| Audit Log Entries | {today_audit_count} |
| Emails Sent | {today_email_sent} |
| Facebook Posts | {today_fb_posts} |
| Twitter Posts | {today_tw_posts} |
| Errors | {today_errors} |

---

## MCP Server Status

| Server | Status |
|--------|--------|
| Email | {email_mcp_status} |
| LinkedIn | {linkedin_mcp_status} |
| Facebook | {facebook_mcp_status} |
| Twitter | {twitter_mcp_status} |
| Odoo | {odoo_mcp_status} |

---

## Recent Completed Activity

{recent_activity}

---

## Quick Links

- [Needs Action](./Needs_Action/) — {pending_count} items
- [Approved](./Approved/) — {approved_count} items
- [Pending Approval](./Pending_Approval/) — {approval_pending_count} items
- [Done](./Done/) — {done_count} items
- [Briefings](./Briefings/)
- [Accounting](./Accounting/)
- [Logs](./Logs/)

---

*Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')} — Auto-refreshed every cycle*
*AI Employee v1.0 — Gold Tier*
"""

        self.dashboard_path.write_text(content, encoding='utf-8')
        logger.info(f"[DONE] Dashboard updated LIVE: {pending_count} action | {approved_count} approved | {approval_pending_count} pending approval | {done_count} done")

    def create_plan(self, items: List[Path]) -> Optional[Path]:
        """Create a Plan.md file for Claude to process."""
        if not items:
            return None

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plan_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_path = self.plans_path / f'PLAN_{plan_id}.md'

        items_list = '\n'.join([f"- `{item.name}`" for item in items])

        # Determine item types
        item_types = set()
        for item in items:
            content = item.read_text(encoding='utf-8')
            if 'type: email' in content:
                item_types.add('email')
            elif 'type: linkedin' in content:
                item_types.add('linkedin')
            elif 'type: file_drop' in content:
                item_types.add('file')

        content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: pending
items_count: {len(items)}
item_types: {', '.join(item_types)}
---

# Processing Plan {plan_id}

## Items to Process

{items_list}

## Instructions for Kilo Code

1. Read each item in the list above from `/Needs_Action/`
2. Review the [Company Handbook](../Company_Handbook.md) for rules of engagement
3. Review the [Business Goals](../Business_Goals.md) for context
4. Process each item according to the handbook rules

## Processing Guidelines

### For Emails:
- Read and understand the email content
- Determine priority based on sender and content
- Draft appropriate response if needed
- For sensitive actions (payments, new contacts), create approval request

### For LinkedIn:
- Review notifications/messages for business opportunities
- Prioritize connection requests from relevant professionals
- Draft responses for important messages

### For Files:
- Review file content
- Categorize appropriately
- Take action or archive

## Human-in-the-Loop (HITL)

For sensitive actions, create approval requests in `/Pending_Approval/`:
- Payments > $50
- Sending emails to new contacts
- LinkedIn posts (draft only, requires approval)
- Connection requests to VIPs

## Completion Criteria

- [ ] All items processed
- [ ] Dashboard updated
- [ ] Required approval files created in /Pending_Approval/
- [ ] Processed items moved to /Done/ with notes

---

*Created by Orchestrator at {now}*
"""

        plan_path.write_text(content, encoding='utf-8')
        logger.info(f"Created plan: {plan_path.name}")
        return plan_path

    def create_approval_request(self, item: Path, action_type: str, details: Dict) -> Optional[Path]:
        """Create an approval request file in Pending_Approval."""
        try:
            approval_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            approval_path = self.pending_approval_path / f'APPROVAL_{action_type}_{approval_id}.md'

            content = f"""---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
status: pending
priority: {details.get('priority', 'normal')}
source_item: {item.name}
---

# Approval Required: {action_type.replace('_', ' ').title()}

## Details

{json.dumps(details, indent=2)}

## Source

This request was generated while processing: `{item.name}`

## Action Required

To **APPROVE**:
1. Move this file to `/Approved/` folder
2. The orchestrator will execute the action

To **REJECT**:
1. Move this file to `/Rejected/` folder
2. Add reason for rejection in notes section

To **MODIFY**:
1. Edit this file with changes
2. Move to `/Approved/` when ready

---

## Processing Notes

_Add notes here_

---

*Expires: {datetime.now().strftime('%Y-%m-%d')} EOD*
"""

            approval_path.write_text(content, encoding='utf-8')
            logger.info(f"Created approval request: {approval_path.name}")
            return approval_path

        except Exception as e:
            logger.error(f"Error creating approval request: {e}")
            return None

    def trigger_kilo(self, plan_path: Path, output_file: Path = None) -> bool:
        """Trigger Kilo Code to process the plan."""
        if not plan_path.exists():
            logger.error(f"Plan file not found: {plan_path}")
            return False

        logger.info(f"Triggering Kilo Code for plan: {plan_path.name}")

        # Get list of emails to process
        emails_to_process = [p.name for p in plan_path.parent.parent.glob('Needs_Action/*.md')]
        
        # Read email content for context
        email_contexts = []
        for email_file in emails_to_process:
            email_path = plan_path.parent.parent / 'Needs_Action' / email_file
            if email_path.exists():
                content = email_path.read_text(encoding='utf-8')
                # Extract key info
                from_email = ''
                subject = ''
                for line in content.split('\n')[:20]:
                    if line.startswith('from:'):
                        from_email = line.split(':', 1)[1].strip()
                    if line.startswith('subject:'):
                        subject = line.split(':', 1)[1].strip()
                email_contexts.append(f"File: {email_file}, From: {from_email}, Subject: {subject}")
        
        email_context_str = '\n'.join(email_contexts)

        # Build the prompt for Kilo - SIMPLE JSON FORMAT
        prompt = f'''You are my AI Employee. Process these emails from Needs_Action folder.

**Emails to process:**
{email_context_str}

**RULES:**
- Unknown sender with business inquiry -> approval_required + draft response
- Known contact -> approval_required + draft response  
- Promotional/newsletter -> archive
- Test/greeting from yourself -> archive

**OUTPUT FORMAT:**
Output ONLY JSON in a code block. Example:
```json
[
  {{"email_file": "EMAIL_test.md", "decision": "approval_required", "reason": "Business inquiry", "draft_response": "Dear Sender,\\n\\nThank you for your email.\\n\\nBest regards"}},
  {{"email_file": "EMAIL_promo.md", "decision": "archive", "reason": "Newsletter", "draft_response": ""}}
]
```

Begin. Output ONLY the JSON:'''

        try:
            # Run Kilo Code with the prompt
            cmd = f'kilo --prompt "{prompt}"'

            logger.info(f"Running: {cmd}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                shell=True,  # Required on Windows for PATH resolution
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                logger.info("Kilo Code completed successfully")
                
                # Save Kilo's output to a file for parsing
                if output_file:
                    output_file.write_text(result.stdout, encoding='utf-8')
                    logger.info(f"Kilo output saved to: {output_file}")
                    logger.info(f"Kilo output preview: {result.stdout[:500]}...")
                
                return True
            else:
                logger.error(f"Kilo Code failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Kilo Code timed out after 10 minutes")
            return False
        except FileNotFoundError:
            logger.error("Kilo Code not found. Please ensure 'kilo' is in PATH")
            return False
        except Exception as e:
            logger.error(f"Error triggering Kilo Code: {e}")
            return False

    def process_approved_items(self, items: List[Path]):
        """Process items that have been approved - execute MCP actions."""
        for item in items:
            logger.info(f"Processing approved item: {item.name}")

            try:
                # Read the approval file
                content = item.read_text(encoding='utf-8')

                # Extract action type and details
                action_type = "unknown"
                if "action: " in content:
                    for line in content.split('\n'):
                        if line.startswith('action:'):
                            action_type = line.split(':')[1].strip()
                            break

                # Extract email details if this is an email action
                email_to = ""
                email_subject = ""
                email_body = ""

                if action_type == "send_email":
                    # Extract recipient from "- **To:**" line (new format)
                    for line in content.split('\n'):
                        # New format: - **To:** email@example.com
                        if '- **To:**' in line or '- To:' in line:
                            # Extract email after colon, remove markdown and whitespace
                            email_part = line.split(':', 1)[1].strip()
                            # Remove markdown bold markers and any leading asterisks
                            email_to = email_part.replace('**', '').strip()
                            break
                    
                    # Extract subject
                    for line in content.split('\n'):
                        if '- **Subject:**' in line or '- Subject:' in line:
                            subject_part = line.split(':', 1)[1].strip()
                            email_subject = subject_part.replace('**', '').strip()
                            break
                    
                    # Try to extract draft response
                    if "## Draft Response" in content or "## Email Response" in content:
                        # Get content between "## Draft Response" and next section
                        parts = content.split("## Draft Response")
                        if len(parts) > 1:
                            draft_section = parts[1].split('\n---\n')[0].strip()
                            # Remove markdown quote markers
                            draft_lines = []
                            for line in draft_section.split('\n'):
                                if line.startswith('>'):
                                    draft_lines.append(line[1:].strip())
                                elif not line.startswith('##') and line.strip():
                                    draft_lines.append(line.strip())
                            email_body = '\n'.join(draft_lines)

                    logger.info(f"Extracted email details - To: {email_to}, Subject: {email_subject}, Body length: {len(email_body) if email_body else 0}")

                # Add processing note
                content += f"\n\n---\n\n**Processed:** {datetime.now().isoformat()}\n**Status:** Approved and executing\n"
                content += f"**Action Type:** {action_type}\n"

                # Execute the action via MCP
                if action_type == "send_email" and email_to and email_body:
                    logger.info(f"Sending email via MCP to: {email_to}")
                    content += f"**Email To:** {email_to}\n"
                    content += f"**Email Subject:** {email_subject}\n"

                    # Try to send via MCP client
                    try:
                        mcp_result = self._send_email_via_mcp(email_to, email_subject, email_body)
                        if mcp_result.get('success', False):
                            content += f"**MCP Result:** Email sent successfully\n"
                            logger.info(f"[OK] Email sent successfully to {email_to}")
                            
                            # AUDIT LOG: Email sent successfully
                            self.audit.log_email_send(
                                to=email_to,
                                subject=email_subject,
                                result="success",
                                message_id=mcp_result.get('message_id'),
                                approval_status="approved",
                                approved_by="human",
                                source_item=item.name
                            )
                        else:
                            content += f"**MCP Result:** {mcp_result.get('error', 'Unknown error')}\n"
                            logger.warning(f"Email send failed: {mcp_result.get('error')}")
                            
                            # AUDIT LOG: Email send failed
                            self.audit.log_email_send(
                                to=email_to,
                                subject=email_subject,
                                result="failure",
                                error=mcp_result.get('error'),
                                approval_status="approved",
                                approved_by="human",
                                source_item=item.name
                            )
                    except Exception as mcp_error:
                        content += f"**MCP Error:** {str(mcp_error)}\n"
                        logger.error(f"MCP email send error: {mcp_error}")
                        
                        # AUDIT LOG: MCP error
                        self.audit.log_email_send(
                            to=email_to,
                            subject=email_subject,
                            result="failure",
                            error=str(mcp_error),
                            approval_status="approved",
                            approved_by="human",
                            source_item=item.name
                        )
                elif action_type == "facebook_post":
                    # Extract Facebook post details
                    fb_message = ""
                    fb_image_url = ""
                    fb_link = ""

                    for line in content.split('\n'):
                        if '- **Message:**' in line or '- Message:' in line:
                            fb_message = line.split(':', 1)[1].strip().replace('**', '').strip()
                        elif '- **Image URL:**' in line or '- Image URL:' in line:
                            fb_image_url = line.split(':', 1)[1].strip().replace('**', '').strip()
                        elif '- **Link:**' in line or '- Link:' in line:
                            fb_link = line.split(':', 1)[1].strip().replace('**', '').strip()

                    # If message not in standard format, try frontmatter or raw extraction
                    if not fb_message:
                        for line in content.split('\n'):
                            if line.startswith('message:'):
                                fb_message = line.split(':', 1)[1].strip()
                                break

                    if fb_message:
                        logger.info(f"Posting to Facebook: {fb_message[:50]}...")
                        content += f"**Facebook Message:** {fb_message}\n"

                        try:
                            mcp_result = self._post_to_facebook(fb_message, fb_image_url, fb_link)
                            if mcp_result.get('success', False):
                                content += f"**MCP Result:** Facebook post published\n"
                                content += f"**Post ID:** {mcp_result.get('post_id', 'N/A')}\n"
                                logger.info("Facebook post successful")

                                self.audit.log_action(
                                    action_type="facebook_post",
                                    target="facebook_page",
                                    result="success",
                                    details={"message": fb_message[:100], "post_id": mcp_result.get('post_id')},
                                    approval_status="approved",
                                    approved_by="human",
                                    source_item=item.name
                                )
                            else:
                                content += f"**MCP Result:** {mcp_result.get('error', 'Unknown error')}\n"
                                logger.warning(f"Facebook post failed: {mcp_result.get('error')}")

                                self.audit.log_action(
                                    action_type="facebook_post",
                                    target="facebook_page",
                                    result="failure",
                                    error=mcp_result.get('error'),
                                    approval_status="approved",
                                    approved_by="human",
                                    source_item=item.name
                                )
                        except Exception as mcp_error:
                            content += f"**MCP Error:** {str(mcp_error)}\n"
                            logger.error(f"Facebook post error: {mcp_error}")

                            self.audit.log_action(
                                action_type="facebook_post",
                                target="facebook_page",
                                result="failure",
                                error=str(mcp_error),
                                approval_status="approved",
                                approved_by="human",
                                source_item=item.name
                            )
                    else:
                        content += "**Warning:** Cannot post to Facebook - missing message content\n"
                        logger.warning("Cannot post to Facebook - missing message")

                elif action_type == "twitter_post":
                    # Extract Twitter post details
                    tweet_text = ""

                    for line in content.split('\n'):
                        if '- **Tweet:**' in line or '- Tweet:' in line:
                            tweet_text = line.split(':', 1)[1].strip().replace('**', '').strip()
                        elif '- **Message:**' in line or '- Message:' in line:
                            tweet_text = line.split(':', 1)[1].strip().replace('**', '').strip()

                    if not tweet_text:
                        for line in content.split('\n'):
                            if line.startswith('message:'):
                                tweet_text = line.split(':', 1)[1].strip()
                                break

                    if tweet_text:
                        if len(tweet_text) > 280:
                            content += f"**Warning:** Tweet text too long ({len(tweet_text)} chars), truncating\n"
                            tweet_text = tweet_text[:280]

                        logger.info(f"Posting to Twitter: {tweet_text[:50]}...")
                        content += f"**Tweet:** {tweet_text}\n"

                        try:
                            mcp_result = self._post_to_twitter(tweet_text)
                            if mcp_result.get('success', False):
                                content += f"**MCP Result:** Tweet published\n"
                                content += f"**Tweet ID:** {mcp_result.get('tweet_id', 'N/A')}\n"
                                logger.info("Twitter post successful")

                                self.audit.log_action(
                                    action_type="twitter_post",
                                    target="twitter",
                                    result="success",
                                    details={"tweet": tweet_text[:100], "tweet_id": mcp_result.get('tweet_id')},
                                    approval_status="approved",
                                    approved_by="human",
                                    source_item=item.name
                                )
                            else:
                                content += f"**MCP Result:** {mcp_result.get('error', 'Unknown error')}\n"
                                logger.warning(f"Twitter post failed: {mcp_result.get('error')}")

                                self.audit.log_action(
                                    action_type="twitter_post",
                                    target="twitter",
                                    result="failure",
                                    error=mcp_result.get('error'),
                                    approval_status="approved",
                                    approved_by="human",
                                    source_item=item.name
                                )
                        except Exception as mcp_error:
                            content += f"**MCP Error:** {str(mcp_error)}\n"
                            logger.error(f"Twitter post error: {mcp_error}")

                            self.audit.log_action(
                                action_type="twitter_post",
                                target="twitter",
                                result="failure",
                                error=str(mcp_error),
                                approval_status="approved",
                                approved_by="human",
                                source_item=item.name
                            )
                    else:
                        content += "**Warning:** Cannot post to Twitter - missing tweet text\n"
                        logger.warning("Cannot post to Twitter - missing tweet text")

                elif action_type == "send_email":
                    missing = []
                    if not email_to:
                        missing.append("recipient (To:)")
                    if not email_body:
                        missing.append("email body")
                    content += f"**Warning:** Cannot send - missing: {', '.join(missing)}\n"
                    logger.warning(f"Cannot send email - missing: {', '.join(missing)}")
                else:
                    content += f"**Note:** Action logged for execution\n"
                    logger.info(f"Action type {action_type} logged")

                item.write_text(content, encoding='utf-8')

                # Move approval file to Done
                dest = self.done_path / item.name
                item.rename(dest)
                logger.info(f"Moved to Done: {dest.name}")

                # CRITICAL FIX: Also move original email file to Done/ to prevent re-processing
                if action_type == "send_email":
                    source_item = None
                    # Extract source_item from frontmatter
                    item_content = dest.read_text(encoding='utf-8')
                    for line in item_content.split('\n'):
                        if line.startswith('source_item:'):
                            source_item = line.split(':', 1)[1].strip()
                            break

                    if source_item:
                        original_email = self.needs_action_path / source_item
                        if original_email.exists():
                            # Move original email to Done/ with reference to approval
                            email_content = original_email.read_text(encoding='utf-8')
                            email_content += f"\n\n---\n\n**Linked Approval:** {dest.name}\n**Email Sent:** {datetime.now().isoformat()}\n"
                            original_email.write_text(email_content, encoding='utf-8')
                            email_dest = self.done_path / source_item
                            original_email.rename(email_dest)
                            logger.info(f"[OK] Also moved original email to Done: {source_item}")
                        else:
                            # Check if already in Done/
                            already_done = self.done_path / source_item
                            if already_done.exists():
                                logger.debug(f"Original email already in Done: {source_item}")
                            else:
                                logger.warning(f"Original email not found: {source_item}")

            except Exception as e:
                logger.error(f"Error processing approved item {item.name}: {e}")

    def _send_email_via_mcp(self, to: str, subject: str, body: str) -> Dict:
        """Send email using direct Gmail API (more reliable than MCP)."""
        try:
            # Use direct Gmail API instead of MCP
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            import base64
            import pickle
            
            # Load credentials
            token_path = self.vault_path.parent / 'token.pickle'
            if not token_path.exists():
                return {'success': False, 'error': 'Token file not found'}
            
            with open(token_path, 'rb') as f:
                creds = pickle.load(f)
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            
            # Get sender email
            profile = service.users().getProfile(userId='me').execute()
            sender_email = profile['emailAddress']
            
            # Create message
            message = MIMEText(body, 'plain')
            message['to'] = to
            message['from'] = sender_email
            message['subject'] = subject
            
            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent_message = service.users().messages().send(
                userId='me', 
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully to {to}, Message ID: {sent_message['id']}")
            return {
                'success': True, 
                'message_id': sent_message['id'],
                'thread_id': sent_message['threadId']
            }
            
        except Exception as e:
            logger.error(f"Direct Gmail send error: {e}")
            return {'success': False, 'error': str(e)}

    def _post_to_facebook(self, message: str, image_url: str = None, link: str = None) -> Dict:
        """Post to Facebook Page via Graph API using the facebook_post.py script approach."""
        try:
            import requests
            import re

            # Load Facebook config from MCP server file
            mcp_config_path = self.vault_path.parent / 'mcp-servers' / 'facebook-mcp' / 'index.js'
            if not mcp_config_path.exists():
                return {'success': False, 'error': 'Facebook MCP config not found'}

            content = mcp_config_path.read_text(encoding='utf-8')
            token_match = re.search(r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'([^']+)'", content)
            page_id_match = re.search(r"FACEBOOK_PAGE_ID:\s*'([^']+)'", content)

            if not token_match or not page_id_match:
                return {'success': False, 'error': 'Facebook credentials not configured'}

            token = token_match.group(1)
            page_id = page_id_match.group(1)

            # Post to Facebook Page
            post_data = {
                'message': message,
                'published': True,
                'access_token': token,
            }

            if image_url:
                post_data['url'] = image_url
            if link:
                post_data['link'] = link

            response = requests.post(
                f'https://graph.facebook.com/v19.0/{page_id}/feed',
                json=post_data,
                timeout=30
            )

            if not response.ok:
                err = response.json().get('error', {})
                return {'success': False, 'error': err.get('message', 'Unknown error')}

            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'url': f"https://facebook.com/{result.get('id')}"
            }

        except Exception as e:
            logger.error(f"Facebook post error: {e}")
            return {'success': False, 'error': str(e)}

    def _post_to_twitter(self, text: str) -> Dict:
        """Post to Twitter/X via API v2 using OAuth 1.0a."""
        try:
            import requests
            import re
            import base64
            import hashlib
            import hmac
            from urllib.parse import quote

            # Load Twitter config from MCP server file
            mcp_config_path = self.vault_path.parent / 'mcp-servers' / 'twitter-mcp' / 'index.js'
            if not mcp_config_path.exists():
                return {'success': False, 'error': 'Twitter MCP config not found'}

            content = mcp_config_path.read_text(encoding='utf-8')

            def extract(key):
                m = re.search(rf"{key}:\s*'([^']+)'", content)
                return m.group(1) if m else ''

            api_key = extract('TWITTER_API_KEY')
            api_secret = extract('TWITTER_API_SECRET')
            access_token = extract('TWITTER_ACCESS_TOKEN')
            access_token_secret = extract('TWITTER_ACCESS_TOKEN_SECRET')

            if not all([api_key, api_secret, access_token, access_token_secret]):
                return {'success': False, 'error': 'Twitter credentials not configured'}

            # OAuth 1.0a signing
            import time
            url = 'https://api.twitter.com/2/tweets'
            nonce = base64.b64encode(hashlib.md5(str(time.time()).encode()).digest()).decode()[:32]
            timestamp = str(int(time.time()))

            oauth_params = {
                'oauth_consumer_key': api_key,
                'oauth_nonce': nonce,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': timestamp,
                'oauth_token': access_token,
                'oauth_version': '1.0',
            }

            # Build signature base
            param_str = '&'.join(
                f"{quote(k, safe='~')}={quote(v, safe='~')}"
                for k, v in sorted(oauth_params.items())
            )
            base_string = f"POST&{quote(url, safe='~')}&{quote(param_str, safe='~')}"
            signing_key = f"{quote(api_secret, safe='~')}&{quote(access_token_secret, safe='~')}"
            signature = base64.b64encode(
                hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
            ).decode()

            oauth_params['oauth_signature'] = signature
            auth_header = 'OAuth ' + ', '.join(
                f'{quote(k, safe="~")}="{quote(v, safe="~")}"'
                for k, v in sorted(oauth_params.items())
            )

            # Post tweet
            response = requests.post(
                url,
                json={'text': text},
                headers={
                    'Authorization': auth_header,
                    'Content-Type': 'application/json',
                },
                timeout=30
            )

            if not response.ok:
                err = response.json()
                errors = err.get('errors', [])
                error_msg = '; '.join(e.get('message', str(e)) for e in errors) if errors else response.text
                return {'success': False, 'error': error_msg}

            result = response.json()
            tweet_id = result.get('data', {}).get('id')
            return {
                'success': True,
                'tweet_id': tweet_id,
                'url': f"https://twitter.com/i/web/status/{tweet_id}"
            }

        except Exception as e:
            logger.error(f"Twitter post error: {e}")
            return {'success': False, 'error': str(e)}

    def auto_post_social(self):
        """Auto-generate, auto-approve, and post social media in ONE cycle.
        
        Full autonomous: Kilo generates -> creates plan -> posts immediately -> Done.
        No manual approval needed for social media posts (low risk).
        """
        import subprocess
        import re
        import json

        # Read business goals
        if not self.business_goals_path.exists():
            logger.info("Business_Goals.md not found, skipping social post generation")
            return False

        goals_content = self.business_goals_path.read_text(encoding='utf-8')
        handbook_rules = ""
        if self.handbook_path.exists():
            handbook_rules = self.handbook_path.read_text(encoding='utf-8')

        today = datetime.now().strftime('%Y-%m-%d')
        done_path = self.done_path
        pending_path = self.pending_approval_path

        # Check if we already posted today (look in Done/)
        fb_done = list(done_path.glob(f'FACEBOOK_POST_AUTO_{today}*'))
        tw_done = list(done_path.glob(f'TWITTER_POST_AUTO_{today}*'))
        if fb_done and tw_done:
            logger.info("Social posts already posted today, skipping")
            return False

        # Build Kilo prompt
        prompt = f'''You are my AI Employee social media manager. Generate ONE Facebook post and ONE Twitter/X post.

## Business Goals
{goals_content}

## Company Rules
{handbook_rules}

## Rules
- Facebook: Engaging, professional, 1-2 paragraphs, relevant hashtags
- Twitter: Under 280 chars, action-oriented, 2-3 hashtags
- Reference specific goals, metrics, projects from Business_Goals.md
- Tone: Professional but approachable

## Output - JSON ONLY
```json
{{
  "facebook": "Facebook post text",
  "twitter": "Twitter post text (max 280 chars)"
}}
```
Output ONLY JSON.'''

        # Run Kilo
        logger.info("[DONE] Kilo generating social posts...")
        fb_message = None
        tw_message = None

        try:
            result = subprocess.run(
                'kilo --prompt "' + prompt.replace('"', "'").replace('\n', ' ') + '"',
                capture_output=True, text=True, timeout=45,
                encoding='utf-8', errors='replace', shell=True,
            )
            output = result.stdout
            json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            json_str = json_match.group(1) if json_match else output
            posts = json.loads(json_str)
            fb_message = posts.get('facebook', '')
            tw_message = posts.get('twitter', '')
            logger.info(f"  FB: {fb_message[:60]}...")
            logger.info(f"  TW: {tw_message[:60]}...")
        except Exception as e:
            logger.warning(f"Kilo failed: {e}, using fallback")
            fb_message = self._generate_post_content("facebook", goals_content, handbook_rules)
            tw_message = self._generate_post_content("twitter", goals_content, handbook_rules)

        if not fb_message and not tw_message:
            return False

        # Create Plan.md
        plan_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_path = self.plans_path / f'PLAN_SOCIAL_{today}_{plan_id}.md'
        plan_path.write_text(f"""---
type: plan
created: {datetime.now().isoformat()}
status: auto_posted
---

# Social Media Plan - {today}

## Facebook Post
{fb_message}

## Twitter Post
{tw_message}

*Generated & posted by AI Employee (Kilo) at {datetime.now().strftime('%H:%M')}*
""", encoding='utf-8')
        logger.info(f"[CYCLE] Plan created: {plan_path.name}")

        posted_any = False

        # Post to Facebook
        if fb_message and not fb_done:
            logger.info("[WARNING] Posting to Facebook...")
            result = self._post_to_facebook(fb_message)
            if result.get('success'):
                # Write completion record to Done/
                done_file = done_path / f'FACEBOOK_POST_AUTO_{today}_{plan_id}.md'
                done_file.write_text(f"""---
type: social_post
platform: facebook
posted: {datetime.now().isoformat()}
status: published
source: ai_generated_kilo
---

# Facebook Post Published

## Message
{fb_message}

## Result
- **Post ID:** {result.get('post_id')}
- **URL:** {result.get('url')}
- **Posted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

*Auto-posted by AI Employee*
""", encoding='utf-8')
                logger.info(f"[...] Facebook posted: {result.get('url')}")

                self.audit.log_action(
                    action_type="facebook_post",
                    target="facebook_page",
                    result="success",
                    details={"message": fb_message[:100], "post_id": result.get('post_id')},
                    approval_status="auto_approved",
                    approved_by="ai_employee",
                    source_item="auto_generated"
                )
                posted_any = True
            else:
                logger.warning(f"❌ Facebook failed: {result.get('error')}")

        # Post to Twitter
        if tw_message and not tw_done:
            logger.info("🐦 Posting to Twitter...")
            result = self._post_to_twitter(tw_message)
            if result.get('success'):
                done_file = done_path / f'TWITTER_POST_AUTO_{today}_{plan_id}.md'
                done_file.write_text(f"""---
type: social_post
platform: twitter
posted: {datetime.now().isoformat()}
status: published
source: ai_generated_kilo
---

# Twitter Post Published

## Tweet
{tw_message}

## Result
- **Tweet ID:** {result.get('tweet_id')}
- **URL:** {result.get('url')}
- **Posted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

*Auto-posted by AI Employee*
""", encoding='utf-8')
                logger.info(f"[...] Twitter posted: {result.get('url')}")

                self.audit.log_action(
                    action_type="twitter_post",
                    target="twitter",
                    result="success",
                    details={"tweet": tw_message[:100], "tweet_id": result.get('tweet_id')},
                    approval_status="auto_approved",
                    approved_by="ai_employee",
                    source_item="auto_generated"
                )
                posted_any = True
            else:
                logger.warning(f"❌ Twitter failed: {result.get('error')}")

        return posted_any

    def generate_social_posts(self):
        """Auto-generate social media posts from Business_Goals.md using Kilo AI.
        
        Reads business context + handbook rules, asks Kilo to generate relevant
        posts for Facebook and Twitter, then creates approval files.
        Only generates ONE post per platform per cycle to avoid spam.
        """
        import subprocess
        import re
        import json

        # Read business goals
        if not self.business_goals_path.exists():
            logger.info("Business_Goals.md not found, skipping social post generation")
            return

        goals_content = self.business_goals_path.read_text(encoding='utf-8')

        # Read company handbook for tone/rules
        handbook_rules = ""
        if self.handbook_path.exists():
            handbook_rules = self.handbook_path.read_text(encoding='utf-8')

        # Check if we already generated today
        today = datetime.now().strftime('%Y-%m-%d')
        fb_pattern = f"FACEBOOK_POST_AUTO_{today}"
        tw_pattern = f"TWITTER_POST_AUTO_{today}"

        # Check Done/ — only skip if already POSTED (not just generated)
        fb_done = list(self.done_path.glob(f'{fb_pattern}*'))
        tw_done = list(self.done_path.glob(f'{tw_pattern}*'))
        if fb_done and tw_done:
            logger.info("Social posts already posted today, skipping")
            return

        # Always generate NEW posts each run (unique filenames with timestamp)
        # Old pending approvals stay — user can approve multiple posts

        # Build Kilo prompt for AI-powered content generation
        prompt = f'''You are my AI Employee's social media manager. Generate ONE Facebook post and ONE Twitter/X post about AI, technology, and current world trends.

## Business Context (use as reference, not main topic)
{goals_content}

## Company Rules
{handbook_rules}

## Topics to Cover (pick something trending/relevant)
- Latest AI developments (LLMs, autonomous agents, AI automation)
- Technology trends shaping 2026 (AI in business, productivity tools)
- Current world events with tech angle (AI regulation, digital transformation)
- AI Employee / Digital FTE concept (24/7 autonomous workers)
- Business automation, future of work, remote work tools
- Breaking tech news or announcements

## Rules
- Facebook: Engaging, professional, 1-2 paragraphs, relevant hashtags
- Twitter: Under 280 chars, punchy, trending-aware, 2-3 hashtags
- Each run should generate DIFFERENT content — do not repeat previous posts
- Be specific, reference real trends or concepts, avoid generic fluff
- Tone: Insightful, forward-looking, professional but approachable

## Output Format - JSON ONLY
```json
{{
  "facebook": "Your Facebook post text here",
  "twitter": "Your Twitter post text here (max 280 chars)"
}}
```

Output ONLY the JSON. No explanation.'''

        # Run Kilo to generate
        logger.info("[DONE] Asking Kilo to generate social media posts (AI/tech topics)...")
        try:
            # Try Kilo CLI first (with short timeout since it's interactive)
            result = subprocess.run(
                'kilo --prompt "' + prompt.replace('"', "'").replace('\n', ' ') + '"',
                capture_output=True,
                text=True,
                timeout=45,
                encoding='utf-8',
                errors='replace',
                shell=True,
            )

            output = result.stdout
            if result.returncode != 0:
                logger.warning(f"Kilo returned error: {result.stderr[:200]}")
                # Fallback to template-based
                fb_message = self._generate_post_content("facebook", goals_content, handbook_rules)
                tw_message = self._generate_post_content("twitter", goals_content, handbook_rules)
            else:
                # Extract JSON from Kilo output
                json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
                json_str = json_match.group(1) if json_match else output

                try:
                    posts = json.loads(json_str)
                    fb_message = posts.get('facebook', '')
                    tw_message = posts.get('twitter', '')
                    logger.info(f"Kilo generated Facebook post: {fb_message[:60]}...")
                    logger.info(f"Kilo generated Twitter post: {tw_message[:60]}...")
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Kilo JSON, using fallback templates")
                    fb_message = self._generate_post_content("facebook", goals_content, handbook_rules)
                    tw_message = self._generate_post_content("twitter", goals_content, handbook_rules)

        except subprocess.TimeoutExpired:
            logger.warning("Kilo timed out, using fallback templates")
            fb_message = self._generate_post_content("facebook", goals_content, handbook_rules)
            tw_message = self._generate_post_content("twitter", goals_content, handbook_rules)
        except Exception as e:
            logger.warning(f"Kilo error: {e}, using fallback templates")
            fb_message = self._generate_post_content("facebook", goals_content, handbook_rules)
            tw_message = self._generate_post_content("twitter", goals_content, handbook_rules)

        # Create Plan.md
        plan_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_path = self.plans_path / f'PLAN_SOCIAL_{today}_{plan_id}.md'
        plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: generated
platforms: facebook, twitter
source: ai_employee_kilo
---

# Social Media Plan - {today}

## Generated Posts

### Facebook Post
{fb_message}

### Twitter Post
{tw_message}

## Workflow
1. Review posts in `/Pending_Approval/`
2. Edit if needed
3. Move to `/Approved/` to publish
4. Run orchestrator again to execute

---

*Generated by AI Employee (Kilo) at {datetime.now().strftime('%H:%M')}*
"""
        plan_path.write_text(plan_content, encoding='utf-8')
        logger.info(f"Created social media plan: {plan_path.name}")

        # Create Facebook approval file
        if fb_message:
            ts = datetime.now().strftime('%H%M%S')
            fb_approval_path = self.pending_approval_path / f'FACEBOOK_POST_AUTO_{today}_{ts}.md'
            fb_content = f"""---
type: approval_request
action: facebook_post
created: {datetime.now().isoformat()}
status: pending
priority: normal
source: ai_generated_kilo
platform: facebook
---

# AI-Generated Facebook Post

## Details
- **Message:** {fb_message}
- **Platform:** Facebook Page
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Source:** Kilo AI - Business Goals Analysis

## To Approve
Move this file to `/Approved/` folder to publish.

## To Reject
Move this file to `/Rejected/` folder.

## To Edit
Modify the message above, then move to `/Approved/`.
"""
            fb_approval_path.write_text(fb_content, encoding='utf-8')
            logger.info(f"[...] Auto-generated Facebook post: {fb_approval_path.name}")

        # Create Twitter approval file
        if tw_message:
            ts = datetime.now().strftime('%H%M%S')
            tw_approval_path = self.pending_approval_path / f'TWITTER_POST_AUTO_{today}_{ts}.md'
            tw_content = f"""---
type: approval_request
action: twitter_post
created: {datetime.now().isoformat()}
status: pending
priority: normal
source: ai_generated_kilo
platform: twitter
---

# AI-Generated Twitter Post

## Details
- **Tweet:** {tw_message}
- **Platform:** Twitter/X
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Source:** Kilo AI - Business Goals Analysis

## To Approve
Move this file to `/Approved/` folder to publish.

## To Reject
Move this file to `/Rejected/` folder.

## To Edit
Modify the tweet text above (max 280 chars), then move to `/Approved/`.
"""
            tw_approval_path.write_text(tw_content, encoding='utf-8')
            logger.info(f"[...] Auto-generated Twitter post: {tw_approval_path.name}")

    def _generate_post_content(self, platform: str, goals: str, handbook: str = "") -> str:
        """Generate social media post content based on business goals.
        
        Uses rule-based generation (no LLM needed) to create relevant posts.
        """
        import random
        from datetime import datetime

        # Extract context from business goals
        revenue_target = ""
        mtd = ""
        projects = []

        for line in goals.split('\n'):
            if 'Monthly goal:' in line:
                revenue_target = line.split(':')[1].strip()
            elif 'Current MTD:' in line:
                mtd = line.split(':')[1].strip()
            elif line.strip().startswith('|') and 'Planning' in line:
                projects.append(line.strip())

        # Post templates based on platform
        today = datetime.now()

        if platform == "facebook":
            templates = [
                f"🚀 Working towards our Q1 2026 goals! Monthly target: {revenue_target}. We're building something great. #AI #Innovation #Business",
                f"[START] AI Employee update: Automating business operations one step at a time. Building autonomous systems that work 24/7. #AIAutomation #DigitalFTE",
                f"[DONE] Q1 2026 Update: Our AI Employee is handling email, social media, and accounting autonomously. The future of work is here. #AI #Productivity",
                f"[STOP] This week's focus: {revenue_target} monthly revenue target. Our AI assistant is working around the clock to make it happen. #StartupLife #AI",
                f"[INFO] Did you know? Our AI Employee monitors Gmail, posts on social media, and manages invoices — all autonomously with human approval. #AI #Automation",
            ]
        else:  # twitter
            templates = [
                f"🚀 Q1 2026 Goal: {revenue_target}/month. Our AI Employee is working 24/7 to make it happen. #AIAutomation #BuildInPublic",
                f"[START] AI Employee can now:\n[...] Monitor emails\n[...] Auto-post on social media\n[...] Manage invoices\n[...] Generate CEO briefings\n\nThe future is autonomous. #AI",
                f"[DONE] Building an AI Employee that works 24/7. Currently at {mtd} MTD towards our {revenue_target} goal. Progress > Perfection. #BuildInPublic",
                f"[INFO] Our AI Employee just posted this tweet autonomously (with human approval, of course). Testing autonomous social media. #AI #Automation",
                f"[STOP] Q1 2026: Building autonomous business systems. AI handles email, social, accounting. Human approves, AI executes. #AIAutomation",
            ]

        return random.choice(templates)

    def parse_kilo_output(self, output_file: Path) -> Dict:
        """Parse Kilo's output to extract approval requests and archive decisions."""
        if not output_file.exists():
            return {'approvals': [], 'archives': []}

        content = output_file.read_text(encoding='utf-8')
        result = {'approvals': [], 'archives': [], 'raw_output': content}

        import json
        import re

        # Try to extract JSON from the output
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        json_str = json_match.group(1) if json_match else content

        try:
            # Parse JSON array
            decisions = json.loads(json_str)
            
            if isinstance(decisions, list):
                for decision in decisions:
                    email_file = decision.get('email_file', '')
                    decision_type = decision.get('decision', '')
                    reason = decision.get('reason', '')
                    draft_response = decision.get('draft_response', '')

                    if decision_type == 'approval_required' and draft_response:
                        # Create approval request content
                        approval_content = f"""---
type: approval_request
action: send_email
created: {datetime.now().isoformat()}
status: pending
priority: high
source_item: {email_file}
---

# Approval Required: Send Email Response

## Email Details
- To: (extract from email file)
- Subject: Re: (see original email)
- Reason: Business response requires approval

## Draft Response

{draft_response}

## To Approve
Move this file to `/Approved/` folder to send this email.

## To Reject
Move this file to `/Rejected/` folder and add reason.

---

## Processing Notes

_Add notes here_
"""
                        result['approvals'].append({
                            'source': email_file,
                            'content': approval_content,
                            'draft_response': draft_response
                        })
                    elif decision_type == 'archive':
                        result['archives'].append({
                            'source': email_file,
                            'reason': reason
                        })
                    else:
                        logger.warning(f"Unknown decision type: {decision_type} for {email_file}")
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {e}")
            logger.debug(f"Raw output: {content[:500]}...")
            # Fallback: try to extract any EMAIL_*.md references and archive them
            archive_pattern = r'EMAIL_\w+\.md'
            matches = re.findall(archive_pattern, content)
            for email_file in matches:
                result['archives'].append({
                    'source': email_file,
                    'reason': 'Processed (JSON parse failed, defaulting to archive)'
                })

        return result

    def run_once(self):
        """Run a single processing cycle."""
        logger.info("Starting processing cycle")

        # Get pending items
        pending = self.get_pending_items()
        approved = self.get_approved_items()
        pending_approvals = self.get_pending_approvals()

        logger.info(f"Found {len(pending)} pending items, {len(approved)} approved items, {len(pending_approvals)} awaiting approval")

        # Update dashboard
        self.update_dashboard(len(pending), len(approved), len(pending_approvals))

        # Process approved items first (execute MCP actions: email, Facebook, Twitter)
        if approved:
            self.process_approved_items(approved)

        # Auto-generate social media posts (creates approval files in Pending_Approval/)
        self.generate_social_posts()

        # Process pending emails using Kilo Email Processor (Silver Tier AI reasoning)
        if pending:
            logger.info(f"Processing {len(pending)} email(s) with Kilo Email Processor")

            try:
                from kilo_email_processor import KiloEmailProcessor
                processor = KiloEmailProcessor(self.vault_path)
                results = processor.process_with_kilo()
                
                logger.info(f"Processing results: {results}")

            except Exception as e:
                logger.error(f"Kilo Email Processor failed: {e}")
                # Fallback: move to In_Progress for manual review
                for item in pending:
                    in_progress_file = self.in_progress_path / item.name
                    content = item.read_text(encoding='utf-8')
                    content += f"\n\n---\n\n**Error:** {e}\n**Status:** Needs manual review\n"
                    item.write_text(content, encoding='utf-8')
                    if in_progress_file != item:
                        item.rename(in_progress_file)
                logger.warning(f"Moved {len(pending)} items to In_Progress for manual review")

        logger.info("Processing cycle complete")

        # REFRESH DASHBOARD with final counts after all processing
        final_pending = len(self.get_pending_items())
        final_approved = len(self.get_approved_items())
        final_pending_approvals = len(self.get_pending_approvals())
        self.update_dashboard(final_pending, final_approved, final_pending_approvals)

# Print summary for user
        if pending_approvals:
            print(f"\n[APPROVAL] Awaiting your approval:")
            for item in pending_approvals:
                print(f"  [-] {item.name}")
            print(f"\n  -> Move files to Approved/ then run again to post")


    def run(self, max_iterations=10):
        """Run orchestrator with Ralph Wiggum autonomous loop.
        
        Keeps cycling until all automated tasks are done.
        Stops when only Pending_Approval items remain (waiting for human).
        """
        logger.info(f"[START] Starting Ralph Wiggum autonomous loop (max {max_iterations} iterations)")
        logger.info(f"   Vault: {self.vault_path}")

        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[CYCLE] Iteration {iteration}/{max_iterations}")
            logger.info(f"{'='*60}")

            # Run one processing cycle
            self.run_once()

            # Check what's left
            pending = self.get_pending_items()       # Needs_Action
            approved = self.get_approved_items()     # Approved (ready to execute)
            pending_approvals = self.get_pending_approvals()  # Waiting for human

            logger.info(f"  Status: {len(pending)} action items | {len(approved)} approved | {len(pending_approvals)} awaiting human approval")

            # If nothing for AI to do, we're done
            if len(pending) == 0 and len(approved) == 0:
                if len(pending_approvals) > 0:
                    logger.info(f"\n⏳ AI work complete. {len(pending_approvals)} item(s) waiting for your approval.")
                else:
                    logger.info(f"\n[...] All tasks complete!")
                # Final dashboard refresh
                self.update_dashboard(0, 0, len(pending_approvals))
                return

            # Final dashboard refresh for this iteration
            self.update_dashboard(len(pending), len(approved), len(pending_approvals))

            # Brief pause before next iteration
            time.sleep(5)

        logger.warning(f"\n⚠️ Max iterations ({max_iterations}) reached. Some items may still be pending.")


def main():
    """Main entry point for the orchestrator."""
    # Get the vault path (personal-ai-employee folder)
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'

    logger.info(f"Vault path: {vault_path}")

    # Create and run orchestrator
    orchestrator = Orchestrator(vault_path, check_interval=30)
    orchestrator.run()


if __name__ == '__main__':
    main()
