"""
Orchestrator for AI Employee - Silver Tier

Enhanced orchestrator with HITL (Human-in-the-Loop) workflow,
multi-watcher support, and MCP server integration.

Uses Qwen Code for AI reasoning and processing.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
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

    def update_dashboard(self, pending_count: int, approved_count: int, approval_pending_count: int):
        """Update the Dashboard.md with current status."""
        if not self.dashboard_path.exists():
            logger.warning("Dashboard.md not found")
            return

        try:
            content = self.dashboard_path.read_text(encoding='utf-8')

            # Update pending actions count and status
            if "Pending Actions |" in content:
                # Extract the line and update count
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "Pending Actions |" in line:
                        status_emoji = "⚠️ Pending" if pending_count > 0 else "✅ Clear"
                        lines[i] = f"| Pending Actions | {pending_count} | {status_emoji} |"
                        break
                content = '\n'.join(lines)

            # Update pending approvals
            if "Pending Approvals |" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "Pending Approvals |" in line:
                        status_emoji = "⏳ Awaiting Review" if approval_pending_count > 0 else "✅ None"
                        lines[i] = f"| Pending Approvals | {approval_pending_count} | {status_emoji} |"
                        break
                content = '\n'.join(lines)

            # Update last processed time
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if "Last Processed |" in content:
                content = content.replace(
                    "Last Processed | - |",
                    f"Last Processed | {now} |"
                )
                content = content.replace(
                    f"Last Processed | {now.split(' ')[0]} |",
                    f"Last Processed | {now} |"
                )

            self.dashboard_path.write_text(content, encoding='utf-8')
            logger.info(f"Dashboard updated: {pending_count} pending, {approved_count} approved, {approval_pending_count} awaiting approval")

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

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

## Instructions for Qwen Code

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

    def trigger_qwen(self, plan_path: Path, output_file: Path = None) -> bool:
        """Trigger Qwen Code to process the plan."""
        if not plan_path.exists():
            logger.error(f"Plan file not found: {plan_path}")
            return False

        logger.info(f"Triggering Qwen Code for plan: {plan_path.name}")

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

        # Build the prompt for Qwen - SIMPLE JSON FORMAT
        prompt = f'''You are my AI Employee. Process these emails from Needs_Action folder.

**Emails to process:**
{email_context_str}

**RULES:**
- Unknown sender with business inquiry → approval_required + draft response
- Known contact → approval_required + draft response  
- Promotional/newsletter → archive
- Test/greeting from yourself → archive

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
            # Run Qwen Code with the prompt
            cmd = f'qwen --prompt "{prompt}"'

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
                logger.info("Qwen Code completed successfully")
                
                # Save Qwen's output to a file for parsing
                if output_file:
                    output_file.write_text(result.stdout, encoding='utf-8')
                    logger.info(f"Qwen output saved to: {output_file}")
                    logger.info(f"Qwen output preview: {result.stdout[:500]}...")
                
                return True
            else:
                logger.error(f"Qwen Code failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Qwen Code timed out after 10 minutes")
            return False
        except FileNotFoundError:
            logger.error("Qwen Code not found. Please ensure 'qwen' is in PATH")
            return False
        except Exception as e:
            logger.error(f"Error triggering Qwen Code: {e}")
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
                            logger.info(f"✓ Email sent successfully to {email_to}")
                            
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
                            logger.info(f"✓ Also moved original email to Done: {source_item}")
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

    def parse_qwen_output(self, output_file: Path) -> Dict:
        """Parse Qwen's output to extract approval requests and archive decisions."""
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

        # Process approved items first (execute MCP actions)
        if approved:
            self.process_approved_items(approved)

        # Process pending emails using Qwen Email Processor (Silver Tier AI reasoning)
        if pending:
            logger.info(f"Processing {len(pending)} email(s) with Qwen Email Processor")

            try:
                from qwen_email_processor import QwenEmailProcessor
                processor = QwenEmailProcessor(self.vault_path)
                results = processor.process_with_qwen()

                logger.info(f"Processing results: {results}")

            except Exception as e:
                logger.error(f"Qwen Email Processor failed: {e}")
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

    def run(self):
        """Run the orchestrator in a continuous loop."""
        logger.info(f"Starting Orchestrator for vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info("Press Ctrl+C to stop")

        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Error in processing cycle: {e}")

            time.sleep(self.check_interval)


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
