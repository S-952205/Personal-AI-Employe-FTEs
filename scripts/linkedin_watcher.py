"""
LinkedIn Watcher for AI Employee - Silver Tier

Monitors LinkedIn and creates action files for Qwen AI to process.
Since LinkedIn blocks automated login, this watcher:
1. Creates sample LinkedIn items for demo
2. Reads from manual input file (LinkedIn_Inbox.md)
3. Qwen AI processes items and drafts posts

Flow:
  Watcher → Creates action files → Qwen processes → Creates approval → You approve → Post
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/linkedin_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInWatcher')


class LinkedInWatcher:
    """LinkedIn watcher that creates action files for Qwen AI."""

    def __init__(self, vault_path: str, check_interval: int = 300):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.processed_items = set()

        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> List[Dict]:
        """Check for LinkedIn activity."""
        items = []
        
        # Check for manual input file
        manual_input = self.vault_path / 'LinkedIn_Inbox.md'
        
        if manual_input.exists():
            logger.info("Found LinkedIn_Inbox.md - processing...")
            content = manual_input.read_text(encoding='utf-8')
            items.append({
                'type': 'manual_input',
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            # Archive the input file
            archive_path = self.vault_path / 'Inbox' / f'LINKEDIN_INBOX_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            manual_input.rename(archive_path)
            logger.info(f"Archived input to: {archive_path.name}")
        
        # Demo mode: create one sample item on first run
        elif len(self.processed_items) == 0:
            logger.info("Creating sample LinkedIn opportunity for demo...")
            items = [self._create_sample_opportunity()]
        
        return items

    def _create_sample_opportunity(self) -> Dict:
        """Create a sample business opportunity for demo."""
        return {
            'type': 'opportunity',
            'content': '''From: John Smith (CEO at TechCorp)
Message: "Hi! I saw your profile and I'm interested in your services. We're looking for a consultant for a Q2 project. Are you available for a call next week?"

Profile: https://linkedin.com/in/johnsmith
Company: TechCorp (500+ employees)
Industry: Technology
''',
            'category': 'business_opportunity',
            'timestamp': datetime.now().isoformat()
        }

    def determine_priority(self, item: Dict) -> str:
        """Determine item priority."""
        category = item.get('category', 'general')
        content = item.get('content', '').lower()

        if category in ['opportunity', 'business_opportunity']:
            return 'high'

        if any(word in content for word in ['urgent', 'asap', 'interview', 'offer']):
            return 'urgent'

        return 'normal'

    def create_action_file(self, item: Dict) -> Optional[Path]:
        """Create an action file in Needs_Action folder."""
        try:
            item_type = item.get('type', 'unknown')
            content = item.get('content', '')
            category = item.get('category', 'general')
            priority = self.determine_priority(item)

            filepath = self.needs_action / f'LINKEDIN_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'

            content_text = f"""---
type: linkedin_{item_type}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
category: {category}
---

# LinkedIn {item_type.title()}

**Category:** {category.title()}

**Priority:** {priority.upper()}

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Content

{content}

---

## Suggested Actions for Qwen AI

"""
            if item_type == 'opportunity' or category == 'business_opportunity':
                content_text += """### Qwen AI Tasks:
1. Review the opportunity
2. Draft a professional response
3. Create a LinkedIn post about this opportunity (for business generation)
4. Save draft to /Plans/ folder
5. Create approval request in /Pending_Approval/

### Post Draft Instructions:
- Create an engaging post about business opportunities
- Include relevant hashtags: #AI #Automation #BusinessTransformation
- Keep it professional and positive
- Do not mention specific client names without approval
"""
            elif item_type == 'message':
                content_text += """### Qwen AI Tasks:
1. Read the message carefully
2. Draft appropriate response
3. Save draft to /Plans/ folder
4. Create approval request (requires approval for new contacts)
"""
            else:
                content_text += """### Qwen AI Tasks:
1. Review the content
2. Determine appropriate action
3. Draft response/post if needed
4. Follow HITL workflow for approval
"""

            content_text += f"""
---

## Processing Notes

_Add your notes and actions taken here_

**Processed by:** Qwen AI
**Date:** _Will be filled after processing_
**Status:** Pending

"""
            filepath.write_text(content_text, encoding='utf-8')
            logger.info(f"✓ Created action file: {filepath.name} (Priority: {priority})")
            return filepath

        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None

    def run(self):
        """Run the LinkedIn watcher in a continuous loop."""
        logger.info(f"Starting LinkedInWatcher for vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info("Press Ctrl+C to stop")
        logger.info("")
        logger.info("=" * 70)
        logger.info("LINKEDIN WATCHER - QWEN AI EDITION")
        logger.info("=" * 70)
        logger.info("")
        logger.info("This watcher creates action files for Qwen AI to process.")
        logger.info("")
        logger.info("Workflow:")
        logger.info("  1. Watcher creates action files in /Needs_Action/")
        logger.info("  2. Qwen AI reads and processes items")
        logger.info("  3. Qwen drafts posts in /Plans/")
        logger.info("  4. Creates approval requests in /Pending_Approval/")
        logger.info("  5. You approve → Run: python scripts/linkedin_post.py")
        logger.info("")
        logger.info("To add LinkedIn items manually:")
        logger.info("  1. Create: personal-ai-employee/LinkedIn_Inbox.md")
        logger.info("  2. Add LinkedIn notifications/messages")
        logger.info("  3. Watcher will auto-process and create action files")
        logger.info("")

        while True:
            try:
                items = self.check_for_updates()

                if items:
                    logger.info(f"Found {len(items)} LinkedIn item(s)")
                    for item in items:
                        self.create_action_file(item)
                        self.processed_items.add(item.get('content', '')[:50])
                else:
                    logger.debug("No new LinkedIn activity")

            except Exception as e:
                logger.error(f"Error in LinkedIn watcher loop: {e}")

            time.sleep(self.check_interval)


def main():
    """Main entry point for LinkedIn watcher."""
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'

    logger.info(f"Vault path: {vault_path}")

    watcher = LinkedInWatcher(
        vault_path=str(vault_path),
        check_interval=300  # Check every 5 minutes
    )
    watcher.run()


if __name__ == '__main__':
    main()
