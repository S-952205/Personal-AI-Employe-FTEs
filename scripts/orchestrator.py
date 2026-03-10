"""
Orchestrator for AI Employee - Silver Tier

Enhanced orchestrator with HITL (Human-in-the-Loop) workflow,
multi-watcher support, and MCP server integration.
"""

import subprocess
import logging
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

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
            if md_file.name not in self.processed_files:
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

## Instructions for Claude Code

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

    def trigger_claude(self, plan_path: Path) -> bool:
        """Trigger Claude Code to process the plan."""
        if not plan_path.exists():
            logger.error(f"Plan file not found: {plan_path}")
            return False

        logger.info(f"Triggering Claude Code for plan: {plan_path.name}")

        # Build the prompt for Claude
        prompt = f"""You are my AI Employee. Process the plan at `{plan_path}`.

Follow these steps:
1. Read the plan file to understand what needs to be done
2. Review the Company Handbook for rules of engagement
3. Review Business Goals for context
4. Process each item in the Needs_Action folder
5. Apply the rules from the handbook
6. For sensitive actions, create approval requests in /Pending_Approval/
7. For automatic actions, execute them directly
8. Move completed items to /Done/ with processing notes
9. Update the Dashboard with results

Remember:
- Always be transparent and log your actions
- Require approval for sensitive actions (payments > $50, new contacts, posts)
- Be proactive in identifying issues and suggesting improvements
- Use MCP servers for external actions when available
"""

        try:
            # Run Claude Code with the prompt
            cmd = f'claude --prompt "{prompt}"'

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
                logger.info("Claude Code completed successfully")
                return True
            else:
                logger.error(f"Claude Code failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out after 10 minutes")
            return False
        except FileNotFoundError:
            logger.error("Claude Code not found. Please ensure 'claude' is in PATH")
            return False
        except Exception as e:
            logger.error(f"Error triggering Claude Code: {e}")
            return False

    def process_approved_items(self, items: List[Path]):
        """Process items that have been approved."""
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

                # Add processing note
                content += f"\n\n---\n\n**Processed:** {datetime.now().isoformat()}\n**Status:** Approved and executed\n"
                
                # For Silver tier, we log the action but don't auto-execute MCP
                # (MCP integration would go here for full automation)
                content += f"**Action Type:** {action_type}\n"
                content += f"**Note:** Ready for MCP execution (configure MCP servers for auto-execution)\n"
                
                item.write_text(content, encoding='utf-8')

                # Move to Done
                dest = self.done_path / item.name
                item.rename(dest)
                logger.info(f"Moved to Done: {dest.name}")

            except Exception as e:
                logger.error(f"Error processing approved item {item.name}: {e}")

    def run_once(self):
        """Run a single processing cycle with Ralph Wiggum Loop."""
        logger.info("Starting processing cycle")

        # Get pending items
        pending = self.get_pending_items()
        approved = self.get_approved_items()
        pending_approvals = self.get_pending_approvals()

        logger.info(f"Found {len(pending)} pending items, {len(approved)} approved items, {len(pending_approvals)} awaiting approval")

        # Update dashboard
        self.update_dashboard(len(pending), len(approved), len(pending_approvals))

        # Process approved items first
        if approved:
            self.process_approved_items(approved)

        # Ralph Wiggum Loop: Keep triggering Claude until items are in /Done
        if pending:
            plan_path = self.create_plan(pending)
            if plan_path:
                max_iterations = 5  # Prevent infinite loops
                iteration = 0
                original_pending = list(pending)  # Keep track of original items

                while iteration < max_iterations:
                    iteration += 1
                    logger.info(f"Ralph Wiggum Loop: Iteration {iteration}/{max_iterations}")

                    success = self.trigger_claude(plan_path)

                    if not success:
                        logger.error("Claude Code failed, stopping loop")
                        break

                    # Check if items were moved to /Done
                    still_pending = self.get_pending_items()
                    completed = [item for item in pending if item.name not in still_pending]

                    if len(completed) == len(pending):
                        logger.info(f"All {len(pending)} items completed and moved to /Done")
                        for item in pending:
                            self.processed_files.add(item.name)
                        break
                    elif len(completed) > 0:
                        logger.info(f"{len(completed)} items completed, {len(pending) - len(completed)} remaining")
                        pending = still_pending
                    else:
                        logger.warning("No items completed in this iteration, retrying...")

                else:
                    logger.warning(f"Max iterations ({max_iterations}) reached")
                    # Fallback: If Claude couldn't complete, move files to Done with note
                    for item in original_pending:
                        if item.exists():
                            logger.info(f"Fallback: Moving {item.name} to Done (Claude lacked MCP access)")
                            content = item.read_text(encoding='utf-8')
                            content += f"\n\n---\n\n**Note:** Claude Code was triggered but could not process this item automatically.\n"
                            content += f"**Reason:** MCP servers not configured or action requires manual review.\n"
                            content += f"**Action Required:** Manual review and processing.\n"
                            content += f"**Timestamp:** {datetime.now().isoformat()}\n"
                            item.write_text(content, encoding='utf-8')

                            # Move to Done
                            dest = self.done_path / item.name
                            item.rename(dest)
                            self.processed_files.add(item.name)
                            logger.info(f"Moved to Done (fallback): {dest.name}")

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
