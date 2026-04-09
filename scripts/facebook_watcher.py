"""
Facebook Watcher - Gold Tier

Monitors Facebook Page for new comments, messages, and notifications.
Creates action files in /Needs_Action/ for the orchestrator to process.

Uses Facebook Graph API to poll for new activity.

Setup Required:
1. Facebook Developer Account
2. Page Access Token with permissions
3. Update FACEBOOK_PAGE_ACCESS_TOKEN in this file
"""

import time
import logging
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/facebook_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FacebookWatcher')


# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================

FACEBOOK_CONFIG = {
    'PAGE_ACCESS_TOKEN': 'EAANqfnwKehYBRBpyqranxfNQvEXQS1LGilUHASZCjvjXh8OOhvgO5mxOIKNznUFN0z9c5fZB13Y1QovHKad40yubCcVMKu53hLs6kEm7s4rHtZA3lyONKT6dceXJXifeJKdO0hn0a4J6F6FpHaDVCZArvy99tOGcagmvZASbqvxrAsc6EkXdEfG0u8rTZBcgvhT4fHePny',  # Replace with your token
    'PAGE_ID': '1045279958668364',              # Replace with your Page ID
    'INSTAGRAM_ACCOUNT_ID': 'DUMMY',  # Replace with IG account ID
    'GRAPH_API_BASE': 'https://graph.facebook.com/v19.0',
    'CHECK_INTERVAL': 300,  # 5 minutes
}


class FacebookGraphAPI:
    """Helper for Facebook Graph API operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config['GRAPH_API_BASE']
        self.access_token = config['PAGE_ACCESS_TOKEN']
        self.page_id = config['PAGE_ID']
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to Graph API."""
        url = f"{self.base_url}{endpoint}"
        all_params = {
            'access_token': self.access_token,
            **(params or {})
        }
        
        try:
            response = requests.get(url, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {e}")
            raise
    
    def get_recent_comments(self, since: Optional[int] = None, limit: int = 10) -> List[Dict]:
        """Get recent comments on page posts."""
        params = {
            'fields': 'id,message,from,created_time,parent',
            'limit': str(limit),
            'filter': 'stream',
        }
        
        if since:
            params['since'] = str(since)  # Convert int to string for URL
        
        # Get page feed with comments
        endpoint = f"/{self.page_id}/feed"
        result = self._make_request(endpoint, params)
        
        comments = []
        for post in result.get('data', []):
            if 'comments' in post:
                comments.extend(post['comments'].get('data', []))
        
        return comments
    
    def get_page_messages(self, since: Optional[int] = None, limit: int = 10) -> List[Dict]:
        """Get recent messages/conversations."""
        endpoint = f"/{self.page_id}/conversations"
        params = {
            'fields': 'id,updated_time,link,senders',
            'limit': str(limit),
        }
        
        if since:
            params['updated_time'] = f'>{since}'
        
        result = self._make_request(endpoint, params)
        return result.get('data', [])
    
    def get_page_notifications(self, limit: int = 20) -> List[Dict]:
        """Get page notifications."""
        endpoint = f"/{self.page_id}/notifications"
        params = {
            'limit': str(limit),
        }
        
        result = self._make_request(endpoint, params)
        return result.get('data', [])


class FacebookWatcher:
    """
    Monitors Facebook Page for activity and creates action files.
    
    Watches for:
    - New comments on posts
    - Messages to the page
    - Page notifications (likes, shares, mentions)
    """
    
    def __init__(self, vault_path: Path, config: Dict = None):
        self.vault_path = vault_path
        self.config = config or FACEBOOK_CONFIG
        self.check_interval = self.config['CHECK_INTERVAL']
        self.needs_action_path = vault_path / 'Needs_Action'
        self.processed_ids_file = vault_path / '.facebook_processed_ids.json'
        
        # Initialize API
        self.graph_api = FacebookGraphAPI(self.config)
        
        # Load processed IDs
        self.processed_ids = self._load_processed_ids()
        
        # Track last check time
        self.last_check_time = self._get_last_check_time()
    
    def _load_processed_ids(self) -> set:
        """Load previously processed item IDs."""
        if self.processed_ids_file.exists():
            try:
                data = json.loads(self.processed_ids_file.read_text(encoding='utf-8'))
                return set(data)
            except Exception as e:
                logger.warning(f"Failed to load processed IDs: {e}")
        return set()
    
    def _save_processed_ids(self):
        """Save processed item IDs to prevent duplicates."""
        # Keep only last 1000 IDs to prevent file growth
        ids_list = list(self.processed_ids)[-1000:]
        self.processed_ids_file.write_text(
            json.dumps(ids_list, indent=2),
            encoding='utf-8'
        )
    
    def _get_last_check_time(self) -> int:
        """Get last check time as Unix timestamp."""
        return int((datetime.now() - timedelta(minutes=10)).timestamp())
    
    def check_for_new_comments(self) -> List[Dict]:
        """Check for new comments on page posts."""
        try:
            comments = self.graph_api.get_recent_comments(since=self.last_check_time)
            new_comments = [c for c in comments if c['id'] not in self.processed_ids]
            return new_comments
        except Exception as e:
            logger.error(f"Error checking comments: {e}")
            return []
    
    def check_for_messages(self) -> List[Dict]:
        """Check for new page messages."""
        try:
            messages = self.graph_api.get_page_messages(since=self.last_check_time)
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            return new_messages
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
            return []
    
    def check_for_notifications(self) -> List[Dict]:
        """Check for page notifications."""
        try:
            notifications = self.graph_api.get_page_notifications()
            new_notifications = [n for n in notifications if n.get('id') not in self.processed_ids]
            return new_notifications
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
            return []
    
    def create_comment_action_file(self, comment: Dict) -> Path:
        """Create action file for new comment."""
        comment_id = comment.get('id', 'unknown')
        from_name = comment.get('from', {}).get('name', 'Unknown User')
        message = comment.get('message', '')
        created_time = comment.get('created_time', datetime.now().isoformat())
        
        # Check for keywords that need attention
        keywords = ['complaint', 'issue', 'problem', 'help', 'urgent', 'refund']
        priority = 'high' if any(kw in message.lower() for kw in keywords) else 'normal'
        
        content = f"""---
type: facebook_comment
platform: facebook
comment_id: {comment_id}
from: {from_name}
created: {created_time}
priority: {priority}
status: pending
---

# Facebook Comment

## From
{from_name}

## Comment
{message}

## Details
- **Comment ID:** {comment_id}
- **Created:** {created_time}
- **Priority:** {priority}

## Suggested Actions
- [ ] Respond to comment
- [ ] Like comment (if positive)
- [ ] Escalate if complaint
"""
        filepath = self.needs_action_path / f'FACEBOOK_COMMENT_{comment_id[:12]}.md'
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"📝 Created action file for comment from {from_name}")
        return filepath
    
    def create_message_action_file(self, message: Dict) -> Path:
        """Create action file for page message."""
        message_id = message.get('id', 'unknown')
        updated_time = message.get('updated_time', datetime.now().isoformat())
        
        content = f"""---
type: facebook_message
platform: facebook
message_id: {message_id}
updated: {updated_time}
priority: high
status: pending
---

# Facebook Message

## Details
- **Message ID:** {message_id}
- **Updated:** {updated_time}
- **Link:** {message.get('link', 'N/A')}

## Suggested Actions
- [ ] Check and respond to message
- [ ] Mark as read after response
"""
        filepath = self.needs_action_path / f'FACEBOOK_MESSAGE_{message_id[:12]}.md'
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"📝 Created action file for message")
        return filepath
    
    def create_notification_action_file(self, notification: Dict) -> Path:
        """Create action file for page notification."""
        notif_id = notification.get('id', 'unknown')
        notif_type = notification.get('type', 'unknown')
        title = notification.get('title_text', '')
        
        content = f"""---
type: facebook_notification
platform: facebook
notification_id: {notif_id}
notification_type: {notif_type}
priority: normal
status: pending
---

# Facebook Notification

## {title}

- **Type:** {notif_type}
- **ID:** {notif_id}

## Suggested Actions
- [ ] Review notification
- [ ] Take action if needed
"""
        filepath = self.needs_action_path / f'FACEBOOK_NOTIF_{notif_id[:12]}.md'
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"📝 Created action file for notification")
        return filepath
    
    def run_once(self) -> int:
        """Run one check cycle. Returns number of new items found."""
        logger.info("🔍 Checking Facebook for new activity...")
        
        items_found = 0
        
        # Check comments
        new_comments = self.check_for_new_comments()
        for comment in new_comments:
            self.create_comment_action_file(comment)
            self.processed_ids.add(comment['id'])
            items_found += 1
        
        # Check messages
        new_messages = self.check_for_messages()
        for message in new_messages:
            self.create_message_action_file(message)
            self.processed_ids.add(message['id'])
            items_found += 1
        
        # Check notifications
        new_notifications = self.check_for_notifications()
        for notification in new_notifications:
            if notification.get('id'):
                self.create_notification_action_file(notification)
                self.processed_ids.add(notification['id'])
                items_found += 1
        
        # Update state
        self.last_check_time = int(datetime.now().timestamp())
        self._save_processed_ids()
        
        if items_found > 0:
            logger.info(f"✅ Found {items_found} new Facebook items")
        else:
            logger.debug("ℹ️ No new Facebook items")
        
        return items_found
    
    def run(self):
        """Main loop - continuously monitor Facebook."""
        logger.info(f"🚀 Starting Facebook Watcher (check interval: {self.check_interval}s)")
        logger.info(f"   Page ID: {self.config['PAGE_ID']}")
        
        # Ensure Needs_Action directory exists
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"❌ Error in Facebook watcher loop: {e}")
            
            time.sleep(self.check_interval)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Page Watcher')
    parser.add_argument(
        '--vault-path',
        type=str,
        default=str(Path(__file__).parent.parent / 'personal-ai-employee'),
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit'
    )
    
    args = parser.parse_args()
    
    vault = Path(args.vault_path)
    if not vault.exists():
        logger.error(f"Vault path does not exist: {vault}")
        return 1
    
    config = FACEBOOK_CONFIG.copy()
    config['CHECK_INTERVAL'] = args.check_interval
    
    watcher = FacebookWatcher(vault_path=vault, config=config)
    
    if args.once:
        items = watcher.run_once()
        return 0 if items >= 0 else 1
    else:
        watcher.run()


if __name__ == '__main__':
    main()
