"""
Orchestrator for AI Employee - Bronze Tier

Monitors the Needs_Action folder and triggers Qwen Code processing.
This is the main coordination script for the AI Employee.
"""

import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Orchestrator')


class Orchestrator:
    """Main orchestrator for AI Employee tasks."""
    
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
        
        # Ensure all directories exist
        for path in [
            self.inbox_path,
            self.needs_action_path,
            self.done_path,
            self.plans_path,
            self.approved_path,
            self.pending_approval_path
        ]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Track processed files
        self.processed_files = set()
        
        # Core markdown files
        self.dashboard_path = vault_path / 'Dashboard.md'
        self.handbook_path = vault_path / 'Company_Handbook.md'
        self.business_goals_path = vault_path / 'Business_Goals.md'
    
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
    
    def update_dashboard(self, pending_count: int, approved_count: int):
        """Update the Dashboard.md with current status."""
        if not self.dashboard_path.exists():
            logger.warning("Dashboard.md not found")
            return
        
        try:
            content = self.dashboard_path.read_text(encoding='utf-8')
            
            # Update pending actions count
            if "Pending Actions |" in content:
                content = content.replace(
                    "Pending Actions | 0 |",
                    f"Pending Actions | {pending_count} |"
                )
            
            # Update status emoji
            status = "⚠️ Pending" if pending_count > 0 else "✅ Clear"
            if "Pending Actions |" in content:
                content = content.replace(
                    "✅ Clear |",
                    status
                )
            
            # Update last processed time
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if "Last Processed |" in content:
                content = content.replace(
                    "Last Processed | - |",
                    f"Last Processed | {now} |"
                )
            
            self.dashboard_path.write_text(content, encoding='utf-8')
            logger.info(f"Dashboard updated: {pending_count} pending, {approved_count} approved")
            
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

        content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: pending
items_count: {len(items)}
---

# Processing Plan {plan_id}

## Items to Process

{items_list}

## Instructions for Claude Code

1. Read each item in the list above from `/Needs_Action/`
2. Review the [Company Handbook](../Company_Handbook.md) for rules of engagement
3. Review the [Business Goals](../Business_Goals.md) for context
4. Process each item according to the handbook rules
5. For each item:
   - Determine the appropriate action
   - If approval is needed, create a file in `/Pending_Approval/`
   - If action can be taken automatically, do so
   - Move processed item to `/Done/` with processing notes
6. Update the [Dashboard](../Dashboard.md) with results

## Completion Criteria

- [ ] All items processed
- [ ] Dashboard updated
- [ ] Any required approval files created
- [ ] Processed items moved to /Done/

---

*Created by Orchestrator at {now}*
"""

        plan_path.write_text(content, encoding='utf-8')
        logger.info(f"Created plan: {plan_path.name}")
        return plan_path
    
    def trigger_qwen(self, plan_path: Path) -> bool:
        """Trigger Qwen Code to process the plan."""
        if not plan_path.exists():
            logger.error(f"Plan file not found: {plan_path}")
            return False

        logger.info(f"Triggering Qwen Code for plan: {plan_path.name}")

        # Build the prompt for Qwen
        prompt = f"""You are my AI Employee. Process the plan at `{plan_path}`.

Follow these steps:
1. Read the plan file to understand what needs to be done
2. Review the Company Handbook for rules of engagement
3. Process each item in the Needs_Action folder
4. Apply the rules from the handbook
5. Create approval requests when needed
6. Move completed items to /Done with processing notes
7. Update the Dashboard

Remember:
- Always be transparent and log your actions
- Require approval for sensitive actions (payments > $50, new contacts, etc.)
- Be proactive in identifying issues and suggesting improvements
"""

        try:
            # Run Qwen Code with the prompt
            # Note: This assumes 'qwen' is in PATH
            cmd = f'qwen --prompt "{prompt}"'

            logger.info(f"Running: {cmd}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                shell=True,  # Required on Windows for PATH resolution
                encoding='utf-8',  # Explicit UTF-8 encoding
                errors='replace'  # Replace undecodable characters
            )

            if result.returncode == 0:
                logger.info("Qwen Code completed successfully")
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
        """Process items that have been approved."""
        for item in items:
            logger.info(f"Processing approved item: {item.name}")
            # For Bronze tier, we just log and move to Done
            # Silver/Gold tiers would execute actual actions here
            
            # Add processing note
            content = item.read_text(encoding='utf-8')
            content += f"\n\n---\n\n**Processed:** {datetime.now().isoformat()}\n**Status:** Approved and completed\n"
            item.write_text(content, encoding='utf-8')
            
            # Move to Done
            dest = self.done_path / item.name
            item.rename(dest)
            logger.info(f"Moved to Done: {dest.name}")
    
    def run_once(self):
        """Run a single processing cycle with Ralph Wiggum Loop."""
        logger.info("Starting processing cycle")

        # Get pending items
        pending = self.get_pending_items()
        approved = self.get_approved_items()

        logger.info(f"Found {len(pending)} pending items, {len(approved)} approved items")

        # Update dashboard
        self.update_dashboard(len(pending), len(approved))

        # Process approved items first
        if approved:
            self.process_approved_items(approved)

        # Ralph Wiggum Loop: Keep triggering Qwen until items are in /Done
        if pending:
            plan_path = self.create_plan(pending)
            if plan_path:
                max_iterations = 5  # Prevent infinite loops
                iteration = 0
                original_pending = list(pending)  # Keep track of original items

                while iteration < max_iterations:
                    iteration += 1
                    logger.info(f"Ralph Wiggum Loop: Iteration {iteration}/{max_iterations}")

                    success = self.trigger_qwen(plan_path)

                    if not success:
                        logger.error("Qwen Code failed, stopping loop")
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
                    # Fallback: If Qwen couldn't complete, move files to Done with note
                    # This prevents infinite loops when Qwen lacks MCP capabilities
                    for item in original_pending:
                        if item.exists():
                            logger.info(f"Fallback: Moving {item.name} to Done (Qwen lacked MCP access)")
                            content = item.read_text(encoding='utf-8')
                            content += f"\n\n---\n\n**Note:** Qwen Code was triggered but could not process this item automatically.\n"
                            content += f"**Reason:** File system MCP not configured.\n"
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
