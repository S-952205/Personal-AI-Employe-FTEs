"""
Gmail Watcher for AI Employee - Silver Tier

Monitors Gmail for unread/important emails and creates action files in Needs_Action.
Uses Google Gmail API with OAuth2 credentials.
"""

import time
import logging
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gmail_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GmailWatcher')

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send']

class GmailWatcher:
    """Watches Gmail for new important/unread messages."""

    def __init__(self, vault_path: str, credentials_path: str, token_path: str = None, check_interval: int = 120):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else self.vault_path.parent / 'token.pickle'
        self.check_interval = check_interval
        self.processed_ids = set()
        self.processed_ids_file = self.vault_path.parent / '.gmail_processed_ids.json'
        self.service = None
        
        # Load previously processed IDs from file
        self._load_processed_ids()
        
        # Keywords for priority detection
        self.urgent_keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'deadline', 'emergency']
        self.business_keywords = ['project', 'client', 'meeting', 'proposal', 'contract', 'budget']

        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def _load_processed_ids(self):
        """Load previously processed email IDs from file."""
        if self.processed_ids_file.exists():
            try:
                import json
                with open(self.processed_ids_file, 'r') as f:
                    self.processed_ids = set(json.load(f))
                logger.info(f"Loaded {len(self.processed_ids)} previously processed email IDs")
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")
                self.processed_ids = set()

    def _save_processed_ids(self):
        """Save processed email IDs to file."""
        try:
            import json
            # Keep only last 1000 IDs to prevent file from growing too large
            if len(self.processed_ids) > 1000:
                self.processed_ids = set(list(self.processed_ids)[-1000:])
            with open(self.processed_ids_file, 'w') as f:
                json.dump(list(self.processed_ids), f)
            logger.debug(f"Saved {len(self.processed_ids)} processed email IDs")
        except Exception as e:
            logger.warning(f"Could not save processed IDs: {e}")

    def authenticate(self) -> bool:
        """Authenticate with Gmail API and build service."""
        try:
            creds = None
            
            # Load existing token
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        logger.error(f"Credentials file not found: {self.credentials_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0, open_browser=False)
                    print("\n=== Gmail Authentication Required ===")
                    print("Please visit the URL below and authorize the application:")
                    print("Then paste the authorization code here:")
                    
                    # Manual authorization code flow
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print(f"\nAuthorization URL: {auth_url}")
                    code = input("Enter authorization code: ").strip()
                    if code:
                        flow.fetch_token(code=code)
                        creds = flow.credentials
            
            # Save token for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def check_for_updates(self) -> List[Dict]:
        """Check for new unread/important emails."""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []

            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    # Get full message details
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    new_messages.append(message)
                    self.processed_ids.add(msg['id'])
            
            # Save processed IDs to persist between runs
            if new_messages:
                self._save_processed_ids()

            return new_messages
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
            return []

    def determine_priority(self, headers: Dict, snippet: str) -> str:
        """Determine email priority based on content."""
        subject = headers.get('Subject', '').lower()
        from_email = headers.get('From', '').lower()
        snippet_lower = snippet.lower()
        
        # Check for urgent keywords
        for keyword in self.urgent_keywords:
            if keyword in subject or keyword in snippet_lower:
                return 'urgent'
        
        # Check for business keywords
        for keyword in self.business_keywords:
            if keyword in subject or keyword in snippet_lower:
                return 'high'
        
        # Check if from known domain (customize as needed)
        business_domains = ['company.com', 'client.com']  # Add your business domains
        for domain in business_domains:
            if domain in from_email:
                return 'high'
        
        return 'normal'

    def create_action_file(self, message: Dict) -> Optional[Path]:
        """Create an action file in Needs_Action folder."""
        try:
            # Extract headers
            headers = {}
            for header in message['payload']['headers']:
                headers[header['name']] = header['value']
            
            from_email = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', datetime.now().isoformat())
            message_id = message['id']
            snippet = message.get('snippet', '')
            
            # Determine priority
            priority = self.determine_priority(headers, snippet)
            
            # Decode email body if available
            body = self._get_email_body(message)
            
            # Generate unique file ID
            file_id = message_id[:8]
            
            # Create action file content
            content = f"""---
type: email
from: {from_email}
subject: {subject}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
message_id: {message_id}
---

# Email Received

**From:** {from_email}

**Subject:** {subject}

**Date:** {date}

**Priority:** {priority.upper()}

---

## Email Content

{body if body else snippet}

---

## Suggested Actions

- [ ] Read and understand the email
- [ ] Determine required response
- [ ] Draft reply (if needed)
- [ ] Take any requested action
- [ ] Archive after processing

---

## Processing Notes

_Add your notes and actions taken here_

"""
            filepath = self.needs_action / f'EMAIL_{file_id}.md'
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created action file: {filepath.name} (Priority: {priority})")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None

    def _get_email_body(self, message: Dict) -> str:
        """Extract and decode email body."""
        try:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        data = part['body']['data']
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                data = message['payload']['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8')
            
            return ""
        except Exception as e:
            logger.error(f"Error decoding email body: {e}")
            return ""

    def mark_as_read(self, message_id: str):
        """Mark an email as read."""
        try:
            if self.service:
                self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                logger.info(f"Marked message {message_id} as read")
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")

    def run(self):
        """Run the Gmail watcher in a continuous loop."""
        logger.info(f"Starting GmailWatcher for vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info("Press Ctrl+C to stop")

        # Initial authentication
        if not self.authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return

        while True:
            try:
                items = self.check_for_updates()
                
                if items:
                    logger.info(f"Found {len(items)} new email(s)")
                    for item in items:
                        self.create_action_file(item)
                        # Optionally mark as read after processing
                        # self.mark_as_read(item['id'])
                else:
                    logger.debug("No new emails")
                    
            except Exception as e:
                logger.error(f"Error in Gmail watcher loop: {e}")
            
            time.sleep(self.check_interval)


def main():
    """Main entry point for Gmail watcher."""
    # Get paths
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'
    
    # Look for credentials.json in project root
    credentials_path = project_root / 'credentials.json'
    
    if not credentials_path.exists():
        logger.error(f"Credentials file not found: {credentials_path}")
        print("\n=== Gmail Credentials Required ===")
        print("Please place your Gmail credentials.json file in the project root:")
        print(f"  {credentials_path}")
        print("\nYou can get credentials from Google Cloud Console:")
        print("  https://console.cloud.google.com/apis/credentials")
        return
    
    logger.info(f"Vault path: {vault_path}")
    logger.info(f"Credentials path: {credentials_path}")
    
    # Create and run watcher
    watcher = GmailWatcher(
        vault_path=str(vault_path),
        credentials_path=str(credentials_path),
        check_interval=120  # Check every 2 minutes
    )
    watcher.run()


if __name__ == '__main__':
    main()
