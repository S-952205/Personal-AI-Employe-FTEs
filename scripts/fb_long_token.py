#!/usr/bin/env python3
"""
Facebook Token Exchange - Get Long-Lived Token (60 days)

Usage:
    python scripts/fb_long_token.py
"""

import requests
import json
from pathlib import Path

# CONFIG - Update these with your values
APP_ID = "961516409616918"  # From credentials or Facebook Dev portal
APP_SECRET = "fd281bbe539d1db1adb240691cea4181"  # From Facebook Dev portal

def exchange_for_long_lived(short_token: str) -> str:
    """Exchange short-lived token for long-lived (60 days)"""
    
    url = f"https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_token
    }
    
    print(f"Exchanging token for long-lived...")
    print(f"App ID: {APP_ID}")
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        long_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)  # seconds
        days = expires_in / 86400
        print(f"[OK] Success! Long-lived token expires in {days} days")
        return long_token
    else:
        print(f"[ERROR] {response.text}")
        return None

def debug_token(token: str) -> dict:
    """Debug/validate a token"""
    url = f"https://graph.facebook.com/v19.0/debug_token"
    params = {
        "input_token": token,
        "access_token": token  # Use same token to debug
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json().get("data", {})
        print(f"\n[Token Debug Info]")
        print(f"   Expires at: {data.get('expires_at', 'N/A')}")
        print(f"   Valid: {data.get('is_valid', 'N/A')}")
        print(f"   Scopes: {data.get('scopes', [])}")
        return data
    return {}

def main():
    print("=" * 60)
    print("Facebook Long-Lived Token Generator")
    print("=" * 60)
    
    # Check if there's an existing token to refresh
    index_path = Path(__file__).parent.parent / "mcp-servers" / "facebook-mcp" / "index.js"
    
    if index_path.exists():
        content = index_path.read_text(encoding='utf-8')
        
        # Try to find existing token
        import re
        match = re.search(r'FACEBOOK_PAGE_ACCESS_TOKEN:\s*[\'"]([^\'"]+)', content)
        
        if match:
            current_token = match.group(1)
            print(f"\nFound current token: {current_token[:30]}...")
            
            print("\nDebugging current token...")
            debug_token(current_token)
            
            print("\nExchanging for long-lived token...")
            long_token = exchange_for_long_lived(current_token)
            
            if long_token:
                # Update the file
                print(f"\nUpdating index.js with new token...")
                new_content = content.replace(
                    f"FACEBOOK_PAGE_ACCESS_TOKEN: '{current_token}'",
                    f"FACEBOOK_PAGE_ACCESS_TOKEN: '{long_token}'"
                )
                new_content = new_content.replace(
                    f"FACEBOOK_PAGE_ACCESS_TOKEN: \"{current_token}\"",
                    f"FACEBOOK_PAGE_ACCESS_TOKEN: \"{long_token}\""
                )
                index_path.write_text(new_content, encoding='utf-8')
                print("[OK] Token updated! Should work for 60 days.")
            else:
                print("[ERROR] Could not exchange token.")
                print("\nTo get a new token manually:")
                print("1. Go to: https://developers.facebook.com/tools/explorer/")
                print("2. Get Page Access Token for your Page")
                print("3. Run this script with the new token")
    else:
        print("index.js not found")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()