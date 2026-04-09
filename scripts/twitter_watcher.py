"""
Twitter/X Watcher - Gold Tier

Monitors Twitter/X for mentions, DMs, and notifications.
Creates action files in /Needs_Action/ for the orchestrator to process.

Uses Twitter API v2 to poll for new activity.

Setup Required:
1. Twitter Developer Account
2. API Key + Secret
3. Bearer Token
4. Access Token + Secret
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
        logging.FileHandler('logs/twitter_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TwitterWatcher')


# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================

TWITTER_CONFIG = {
    'BEARER_TOKEN': 'YOUR_BEARER_TOKEN',  # Replace with your Bearer Token
    'USERNAME': 'YOUR_TWITTER_HANDLE',     # Replace with your username (without @)
    'API_BASE': 'https://api.twitter.com/2',
    'CHECK_INTERVAL': 300,  # 5 minutes
}


class TwitterAPI:
    """Helper for Twitter API v2 operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config['API_BASE']
        self.bearer_token = config['BEARER_TOKEN']
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to Twitter API v2."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Twitter API request failed: {e}")
            raise
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username."""
        endpoint = f"/users/by/username/{username}"
        result = self._make_request(endpoint, {
            'user.fields': 'id,name,username'
        })
        return result.get('data', {}).get('id')
    
    def get_mentions(self, username: str, since_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get recent mentions of a user."""
        # Search for mentions using recent search
        endpoint = "/tweets/search/recent"
        params = {
            'query': f'@{username}',
            'max_results': str(min(limit, 100)),
            'tweet.fields': 'created_at,author_id,public_metrics,referenced_tweets,context_annotations',
            'user.fields': 'name,username,profile_image_url,verified',
            'expansions': 'author_id',
        }
        
        if since_id:
            params['since_id'] = since_id
        
        result = self._make_request(endpoint, params)
        return result.get('data', []), result.get('includes', {}).get('users', [])
    
    def get_user_tweets(self, user_id: str, since_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent tweets from a user."""
        endpoint = f"/users/{user_id}/tweets"
        params = {
            'max_results': str(min(limit, 100)),
            'tweet.fields': 'created_at,public_metrics,context_annotations',
        }
        
        if since_id:
            params['since_id'] = since_id
        
        result = self._make_request(endpoint, params)
        return result.get('data', [])
    
    def get_tweet_metrics(self, tweet_id: str) -> Dict:
        """Get engagement metrics for a tweet."""
        endpoint = f"/tweets/{tweet_id}"
        result = self._make_request(endpoint, {
            'tweet.fields': 'public_metrics,created_at'
        })
        return result.get('data', {}).get('public_metrics', {})


class TwitterWatcher:
    """
    Monitors Twitter/X for activity and creates action files.
    
    Watches for:
    - Mentions (@username)
    - High-engagement notifications
    - Important DMs (if API access allows)
    """
    
    def __init__(self, vault_path: Path, config: Dict = None):
        self.vault_path = vault_path
        self.config = config or TWITTER_CONFIG
        self.check_interval = self.config['CHECK_INTERVAL']
        self.needs_action_path = vault_path / 'Needs_Action'
        self.processed_ids_file = vault_path / '.twitter_processed_ids.json'
        
        # Initialize API
        self.twitter_api = TwitterAPI(self.config)
        
        # Load processed IDs
        self.processed_ids = self._load_processed_ids()
        self.last_tweet_id = None
    
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
        ids_list = list(self.processed_ids)[-1000:]
        self.processed_ids_file.write_text(
            json.dumps(ids_list, indent=2),
            encoding='utf-8'
        )
    
    def check_for_mentions(self) -> tuple:
        """Check for new mentions."""
        try:
            mentions, users = self.twitter_api.get_mentions(
                self.config['USERNAME'],
                since_id=self.last_tweet_id,
                limit=20
            )
            return mentions, users
        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            return [], []
    
    def create_mention_action_file(self, mention: Dict, users: List[Dict]) -> Path:
        """Create action file for mention."""
        mention_id = mention.get('id', 'unknown')
        text = mention.get('text', '')
        created = mention.get('created_at', datetime.now().isoformat())
        
        # Find author info
        author_id = mention.get('author_id')
        author = next((u for u in users if u['id'] == author_id), {})
        author_name = author.get('name', 'Unknown User')
        author_username = author.get('username', 'unknown')
        verified = author.get('verified', False)
        
        # Get metrics
        metrics = mention.get('public_metrics', {})
        engagement_score = (
            metrics.get('like_count', 0) +
            metrics.get('retweet_count', 0) * 2 +
            metrics.get('reply_count', 0)
        )
        
        # Determine priority
        keywords = ['complaint', 'issue', 'problem', 'help', 'urgent', 'refund', 'scam']
        has_urgent_keyword = any(kw in text.lower() for kw in keywords)
        
        if verified or has_urgent_keyword:
            priority = 'high'
        elif engagement_score > 10:
            priority = 'high'
        else:
            priority = 'normal'
        
        content = f"""---
type: twitter_mention
platform: twitter
mention_id: {mention_id}
from: {author_name}
username: @{author_username}
verified: {verified}
created: {created}
priority: {priority}
status: pending
---

# Twitter Mention

## From
{author_name} (@{author_username}) {'✅' if verified else ''}

## Tweet
{text}

## Details
- **Tweet ID:** {mention_id}
- **Created:** {created}
- **Priority:** {priority}
- **Engagement Score:** {engagement_score}

## Metrics
- **Likes:** {metrics.get('like_count', 0)}
- **Retweets:** {metrics.get('retweet_count', 0)}
- **Replies:** {metrics.get('reply_count', 0)}
- **Quotes:** {metrics.get('quote_count', 0)}

## Suggested Actions
- [ ] Respond to mention
- [ ] Like the tweet
- [ ] Retweet if positive
- [ ] Escalate if complaint
"""
        filepath = self.needs_action_path / f'TWITTER_MENTION_{mention_id[:12]}.md'
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"📝 Created action file for mention from @{author_username}")
        return filepath
    
    def run_once(self) -> int:
        """Run one check cycle. Returns number of new items found."""
        logger.info("🔍 Checking Twitter for new mentions...")
        
        items_found = 0
        
        # Check mentions
        mentions, users = self.check_for_mentions()
        for mention in mentions:
            if mention['id'] not in self.processed_ids:
                self.create_mention_action_file(mention, users)
                self.processed_ids.add(mention['id'])
                items_found += 1
        
        # Update last tweet ID for next check
        if mentions:
            # Get the most recent tweet ID
            most_recent = max(mentions, key=lambda m: m.get('created_at', ''))
            self.last_tweet_id = most_recent['id']
        
        # Save state
        self._save_processed_ids()
        
        if items_found > 0:
            logger.info(f"✅ Found {items_found} new Twitter mentions")
        else:
            logger.debug("ℹ️ No new Twitter mentions")
        
        return items_found
    
    def run(self):
        """Main loop - continuously monitor Twitter."""
        logger.info(f"🚀 Starting Twitter Watcher (check interval: {self.check_interval}s)")
        logger.info(f"   Monitoring: @{self.config['USERNAME']}")
        
        # Ensure Needs_Action directory exists
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"❌ Error in Twitter watcher loop: {e}")
            
            time.sleep(self.check_interval)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter/X Watcher')
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
    
    config = TWITTER_CONFIG.copy()
    config['CHECK_INTERVAL'] = args.check_interval
    
    watcher = TwitterWatcher(vault_path=vault, config=config)
    
    if args.once:
        items = watcher.run_once()
        return 0 if items >= 0 else 1
    else:
        watcher.run()


if __name__ == '__main__':
    main()
