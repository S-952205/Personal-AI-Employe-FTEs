"""
Gmail Authentication Helper for AI Employee

Run this script once to authenticate with Gmail API and generate the token file.
The token will be saved for future use by the Gmail watcher.
"""

import os
import sys
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Gmail API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
]

def authenticate():
    """Authenticate with Gmail API and save token."""
    print("=" * 60)
    print("Gmail Authentication for AI Employee")
    print("=" * 60)
    print()
    
    # Get paths
    project_root = Path(__file__).parent.parent.absolute()
    credentials_path = project_root / 'credentials.json'
    token_path = project_root / 'token.pickle'
    
    # Check for credentials file
    if not credentials_path.exists():
        print("ERROR: credentials.json not found!")
        print()
        print("Please download your Gmail API credentials:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create or select a project")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 Client ID credentials")
        print("5. Download the credentials.json file")
        print(f"6. Place it at: {credentials_path}")
        return False
    
    print(f"✓ Found credentials: {credentials_path}")
    
    creds = None
    
    # Load existing token
    if token_path.exists():
        print(f"✓ Found existing token: {token_path}")
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✓ Token refreshed successfully")
            except Exception as e:
                print(f"✗ Token refresh failed: {e}")
                creds = None
        
        if not creds:
            print("\n" + "=" * 60)
            print("AUTHORIZATION REQUIRED")
            print("=" * 60)
            print()
            print("Starting OAuth flow...")
            print()
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                
                # Try to open browser automatically
                print("Opening browser for authorization...")
                print("If browser doesn't open, copy the URL below manually.")
                print()
                
                creds = flow.run_local_server(port=0, open_browser=True)
                
                if creds:
                    print("✓ Authorization successful!")
                    
            except Exception as e:
                print(f"✗ Browser authorization failed: {e}")
                print()
                print("Manual authorization:")
                print("-" * 60)
                
                # Manual flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print(f"\n1. Open this URL in your browser:")
                print(f"   {auth_url}")
                print()
                print("2. Sign in with your Google account")
                print("3. Grant the requested permissions")
                print("4. Copy the authorization code from the redirect URL")
                print()
                
                code = input("5. Paste authorization code here: ").strip()
                
                if code:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    print("✓ Authorization successful!")
                else:
                    print("✗ No authorization code provided")
                    return False
    
    # Save token
    print(f"\nSaving token to: {token_path}")
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
    
    print("✓ Token saved successfully!")
    print()
    print("=" * 60)
    print("AUTHENTICATION COMPLETE")
    print("=" * 60)
    print()
    print("You can now run the Gmail watcher:")
    print(f"  python scripts/gmail_watcher.py")
    print()
    
    # Show account info
    try:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"Authenticated as: {profile['emailAddress']}")
    except Exception as e:
        print(f"Could not get profile info: {e}")
    
    print()
    return True


if __name__ == '__main__':
    success = authenticate()
    sys.exit(0 if success else 1)
