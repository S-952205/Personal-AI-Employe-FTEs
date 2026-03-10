"""
LinkedIn Watcher for AI Employee - Silver Tier

Monitors LinkedIn for new notifications, messages, and connection requests.
Uses Playwright for browser automation with persistent session.

Note: Be aware of LinkedIn's Terms of Service. Use responsibly and at your own risk.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext

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
    """Watches LinkedIn for new notifications, messages, and opportunities."""

    def __init__(self, vault_path: str, session_path: str = None, check_interval: int = 300):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.session_path = Path(session_path) if session_path else self.vault_path.parent / 'linkedin_session'
        self.check_interval = check_interval
        self.processed_items = set()
        
        # Keywords for opportunity detection
        self.opportunity_keywords = [
            'job opportunity', 'hiring', 'position', 'role',
            'project', 'freelance', 'contract', 'consulting',
            'investment', 'partnership', 'collaboration',
            'interview', 'application', 'candidate'
        ]
        
        self.business_keywords = [
            'meeting', 'call', 'introduction', 'networking',
            'recommendation', 'endorsement', 'skill',
            'post', 'article', 'comment', 'mention'
        ]

        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        # Ensure session directory exists
        self.session_path.mkdir(parents=True, exist_ok=True)

    def _create_browser_context(self, playwright) -> BrowserContext:
        """Create a persistent browser context."""
        return playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path),
            headless=True,
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

    def check_for_updates(self) -> List[Dict]:
        """Check LinkedIn for new notifications and messages."""
        items = []
        
        try:
            with sync_playwright() as p:
                context = self._create_browser_context(p)
                page = context.pages[0] if context.pages else context.new_page()
                
                # Navigate to LinkedIn
                logger.info("Navigating to LinkedIn...")
                page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)
                
                # Wait for page to load
                page.wait_for_timeout(5000)
                
                # Check if logged in
                if 'login' in page.url.lower():
                    logger.warning("Not logged in to LinkedIn. Please log in manually in the browser session.")
                    logger.info(f"Session stored at: {self.session_path}")
                    logger.info("Next run will use saved session cookies.")
                    context.close()
                    return items
                
                # Check notifications
                try:
                    notifications = self._check_notifications(page)
                    items.extend(notifications)
                except Exception as e:
                    logger.error(f"Error checking notifications: {e}")
                
                # Check messages
                try:
                    messages = self._check_messages(page)
                    items.extend(messages)
                except Exception as e:
                    logger.error(f"Error checking messages: {e}")
                
                # Check connection requests
                try:
                    connections = self._check_connections(page)
                    items.extend(connections)
                except Exception as e:
                    logger.error(f"Error checking connections: {e}")
                
                context.close()
                
        except Exception as e:
            logger.error(f"Error in LinkedIn check: {e}")
        
        return items

    def _check_notifications(self, page: Page) -> List[Dict]:
        """Check for new notifications."""
        notifications = []
        
        try:
            # Click on notifications bell
            notification_btn = page.locator('button[id="global-nav-notification-icon"]').first
            if notification_btn.is_visible(timeout=5000):
                notification_btn.click()
                page.wait_for_timeout(2000)
                
                # Get notification items
                notification_items = page.locator('ul.mn-notification-list > li').all()
                
                for idx, item in enumerate(notification_items[:10]):  # Limit to 10
                    if idx >= 5:  # Only get first 5 for performance
                        break
                    
                    try:
                        text = item.inner_text(timeout=2000)
                        item_id = f"notif_{hash(text) % 10000}"
                        
                        if item_id not in self.processed_items:
                            # Determine notification type
                            notif_type = self._classify_notification(text)
                            
                            notifications.append({
                                'type': 'notification',
                                'id': item_id,
                                'content': text.strip(),
                                'category': notif_type,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.processed_items.add(item_id)
                    except Exception as e:
                        logger.debug(f"Error processing notification: {e}")
                        continue
                
                # Close notifications dropdown
                page.keyboard.press('Escape')
                page.wait_for_timeout(500)
                
        except Exception as e:
            logger.debug(f"Notifications check failed: {e}")
        
        return notifications

    def _check_messages(self, page: Page) -> List[Dict]:
        """Check for new messages."""
        messages = []
        
        try:
            # Navigate to messaging page
            page.goto('https://www.linkedin.com/messaging/', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Look for unread conversations
            unread_items = page.locator('div.msg-s-conversation-list-item--unread').all()
            
            for item in unread_items[:5]:  # Limit to 5
                try:
                    text = item.inner_text(timeout=2000)
                    msg_id = f"msg_{hash(text) % 10000}"
                    
                    if msg_id not in self.processed_items:
                        messages.append({
                            'type': 'message',
                            'id': msg_id,
                            'content': text.strip(),
                            'category': 'message',
                            'timestamp': datetime.now().isoformat()
                        })
                        self.processed_items.add(msg_id)
                except Exception as e:
                    logger.debug(f"Error processing message: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Messages check failed: {e}")
        
        return messages

    def _check_connections(self, page: Page) -> List[Dict]:
        """Check for new connection requests."""
        connections = []
        
        try:
            # Navigate to My Network page
            page.goto('https://www.linkedin.com/mynetwork/', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Look for connection requests
            connection_items = page.locator('div.request-card').all()
            
            for item in connection_items[:5]:  # Limit to 5
                try:
                    text = item.inner_text(timeout=2000)
                    conn_id = f"conn_{hash(text) % 10000}"
                    
                    if conn_id not in self.processed_items:
                        connections.append({
                            'type': 'connection',
                            'id': conn_id,
                            'content': text.strip(),
                            'category': 'connection_request',
                            'timestamp': datetime.now().isoformat()
                        })
                        self.processed_items.add(conn_id)
                except Exception as e:
                    logger.debug(f"Error processing connection: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Connections check failed: {e}")
        
        return connections

    def _classify_notification(self, text: str) -> str:
        """Classify notification by type."""
        text_lower = text.lower()
        
        # Check for opportunities
        for keyword in self.opportunity_keywords:
            if keyword in text_lower:
                return 'opportunity'
        
        # Check for business-related
        for keyword in self.business_keywords:
            if keyword in text_lower:
                return 'business'
        
        # Check for job-related
        if any(word in text_lower for word in ['job', 'career', 'hiring', 'recruiter']):
            return 'job'
        
        # Check for social engagement
        if any(word in text_lower for word in ['liked', 'commented', 'shared', 'viewed']):
            return 'engagement'
        
        return 'general'

    def determine_priority(self, item: Dict) -> str:
        """Determine item priority."""
        category = item.get('category', 'general')
        content = item.get('content', '').lower()
        
        # High priority categories
        if category in ['opportunity', 'job', 'message']:
            return 'high'
        
        # Check for urgent keywords
        urgent_words = ['urgent', 'asap', 'interview', 'offer', 'deadline']
        if any(word in content for word in urgent_words):
            return 'urgent'
        
        # Business-related is high priority
        if category == 'business':
            return 'high'
        
        return 'normal'

    def create_action_file(self, item: Dict) -> Optional[Path]:
        """Create an action file in Needs_Action folder."""
        try:
            item_type = item.get('type', 'unknown')
            item_id = item.get('id', 'unknown')
            content = item.get('content', '')
            category = item.get('category', 'general')
            priority = self.determine_priority(item)
            
            # Generate filename
            file_id = item_id.split('_')[1] if '_' in item_id else item_id
            
            # Create action file content
            content_text = f"""---
type: linkedin_{item_type}
item_id: {item_id}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
category: {category}
---

# LinkedIn {item_type.title()}

**Type:** {item_type.title()}

**Category:** {category.title()}

**Priority:** {priority.upper()}

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Content

{content}

---

## Suggested Actions

"""
            # Add specific actions based on type
            if item_type == 'message':
                content_text += """- [ ] Read the message carefully
- [ ] Draft appropriate response
- [ ] Send response (requires approval)
- [ ] Follow up if needed
"""
            elif item_type == 'connection':
                content_text += """- [ ] Review the connection request
- [ ] Check person's profile
- [ ] Accept or decline (requires approval)
- [ ] Send welcome message if accepted
"""
            elif item_type == 'notification':
                if category == 'opportunity' or category == 'job':
                    content_text += """- [ ] Review the opportunity details
- [ ] Assess fit and interest
- [ ] Prepare application/response
- [ ] Take action or archive
"""
                else:
                    content_text += """- [ ] Review notification
- [ ] Take action if needed
- [ ] Archive if not actionable
"""
            
            content_text += """
---

## Processing Notes

_Add your notes and actions taken here_

"""
            filepath = self.needs_action / f'LINKEDIN_{file_id}.md'
            filepath.write_text(content_text, encoding='utf-8')
            logger.info(f"Created action file: {filepath.name} (Priority: {priority})")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None

    def run(self):
        """Run the LinkedIn watcher in a continuous loop."""
        logger.info(f"Starting LinkedInWatcher for vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Session path: {self.session_path}")
        logger.info("Press Ctrl+C to stop")
        logger.info("\n=== First Run Instructions ===")
        logger.info("On first run, you may need to manually log in to LinkedIn.")
        logger.info("The session will be saved for subsequent runs.")

        while True:
            try:
                items = self.check_for_updates()
                
                if items:
                    logger.info(f"Found {len(items)} new LinkedIn item(s)")
                    for item in items:
                        self.create_action_file(item)
                else:
                    logger.debug("No new LinkedIn activity")
                    
            except Exception as e:
                logger.error(f"Error in LinkedIn watcher loop: {e}")
            
            time.sleep(self.check_interval)


def main():
    """Main entry point for LinkedIn watcher."""
    # Get paths
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'
    
    logger.info(f"Vault path: {vault_path}")
    
    # Create and run watcher
    watcher = LinkedInWatcher(
        vault_path=str(vault_path),
        check_interval=300  # Check every 5 minutes
    )
    watcher.run()


if __name__ == '__main__':
    main()
