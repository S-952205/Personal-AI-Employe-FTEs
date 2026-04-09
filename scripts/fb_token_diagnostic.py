#!/usr/bin/env python3
"""
Facebook Token Manager - Generates long-lived (60 day) Page Access Tokens

This script:
1. Exchanges your short-lived user token for a long-lived one (60 days)
2. Extracts the Page Access Token from the long-lived user token
3. Tests posting with the token
4. Updates both config files automatically

Usage:
    python scripts/fb_token_manager.py          (interactive, auto-updates)
    python scripts/fb_token_manager.py --no-update  (shows token but doesn't update files)
"""

import re
import sys
from pathlib import Path
import requests

MCP_CONFIG_PATH = Path(__file__).parent.parent / 'mcp-servers' / 'facebook-mcp' / 'index.js'

def load_current_token():
    if not MCP_CONFIG_PATH.exists():
        print("❌ MCP config not found")
        sys.exit(1)
    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')
    match = re.search(r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'([^']+)'", content)
    if not match:
        print("❌ Token not found in config")
        sys.exit(1)
    return match.group(1)

def load_app_config():
    """Extract App ID and Secret for token exchange."""
    if not MCP_CONFIG_PATH.exists():
        return None, None
    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')
    app_id_match = re.search(r"FACEBOOK_APP_ID:\s*'([^']+)'", content)
    app_secret_match = re.search(r"FACEBOOK_APP_SECRET:\s*'([^']+)'", content)
    page_id_match = re.search(r"FACEBOOK_PAGE_ID:\s*'([^']+)'", content)

    app_id = app_id_match.group(1) if app_id_match else None
    app_secret = app_secret_match.group(1) if app_secret_match else None
    page_id = page_id_match.group(1) if page_id_match else None

    return app_id, app_secret, page_id

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Facebook Token Manager')
    parser.add_argument('--no-update', action='store_true', help='Show token but do not update files')
    args = parser.parse_args()

    app_id, app_secret, page_id = load_app_config()
    short_token = load_current_token()

    print("=" * 60)
    print("FACEBOOK LONG-LIVED TOKEN GENERATOR (60 days)")
    print("=" * 60)

    # Step 1: Exchange short-lived user token for long-lived user token
    print("\n1️⃣  Exchanging short-lived token for long-lived (60 days)...")

    r = requests.get('https://graph.facebook.com/v19.0/oauth/access_token', params={
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_token,
    })

    if not r.ok:
        err = r.json().get('error', {})
        print(f"   ❌ Token exchange failed: {err.get('message')}")
        print(f"\n   Possible causes:")
        print(f"   • Your App Secret is incorrect")
        print(f"   • The short-lived token is already expired")
        print(f"   • Your app is not properly configured")
        print(f"\n   Go to: https://developers.facebook.com/tools/explorer/")
        print(f"   → Generate a FRESH token with pages_manage_posts permission")
        print(f"   → Then immediately run this script (before it expires)")
        sys.exit(1)

    data = r.json()
    long_user_token = data.get('access_token')
    expires_in = data.get('expires_in', 0)
    expires_days = expires_in // 86400

    print(f"   ✅ Long-lived user token obtained!")
    print(f"   ⏰ Expires in: {expires_days} days ({expires_in:,} seconds)")

    # Step 2: Get Page Token from long-lived user token
    print(f"\n2️⃣  Fetching your Pages (extracting Page Access Token)...")

    r = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={
        'access_token': long_user_token,
        'fields': 'id,name,access_token',
    })

    if not r.ok:
        err = r.json().get('error', {})
        print(f"   ❌ Failed: {err.get('message')}")
        sys.exit(1)

    pages = r.json().get('data', [])
    if not pages:
        print("   ❌ No pages found")
        sys.exit(1)

    print(f"   Found {len(pages)} Page(s):\n")

    target_page_token = None
    for i, page in enumerate(pages, 1):
        pid = page.get('id')
        pname = page.get('name')
        ptoken = page.get('access_token', '')

        print(f"  {i}. {pname} (ID: {pid})")
        print(f"     Token preview: {ptoken[:40]}...")
        print()

        if pid == page_id:
            target_page_token = ptoken
            print(f"   ✅ This is your configured Page!")

    if not target_page_token:
        print(f"   ⚠️  Page ID {page_id} not found in your pages")
        print(f"   Using first available page instead")
        target_page_token = pages[0].get('access_token', '')
        page_id = pages[0].get('id')

    # Step 3: Test the Page Token
    print(f"\n3️⃣  Testing Page Access Token...")
    r = requests.get(f'https://graph.facebook.com/v19.0/{page_id}', params={
        'access_token': target_page_token,
        'fields': 'name,link',
    })

    if r.ok:
        data = r.json()
        print(f"   ✅ Page token is valid!")
        print(f"   Page: {data.get('name')}")
        print(f"   URL: {data.get('link')}")
    else:
        err = r.json().get('error', {})
        print(f"   ❌ Page token failed: {err.get('message')}")
        sys.exit(1)

    # Step 4: Test posting
    print(f"\n4️⃣  Test posting with Page Token...")
    import datetime
    test_message = "🔧 Token test post ({})".format(
        datetime.datetime.now().strftime('%H:%M:%S')
    )

    r = requests.post(f'https://graph.facebook.com/v19.0/{page_id}/feed', json={
        'message': test_message,
        'published': True,
        'access_token': target_page_token,
    })

    if r.ok:
        result = r.json()
        post_id = result.get('id')
        print(f"   ✅ POST SUCCESSFUL!")
        print(f"   Post ID: {post_id}")

        # Delete test post
        print(f"\n   Cleaning up test post...")
        r2 = requests.delete(f'https://graph.facebook.com/v19.0/{post_id}', params={
            'access_token': target_page_token,
        })
        if r2.ok:
            print(f"   ✅ Deleted")
    else:
        err = r.json().get('error', {})
        print(f"   ❌ Post failed: {err.get('message')}")
        print(f"\n   This token cannot post. Check your app permissions.")
        sys.exit(1)

    # Step 5: Update config files
    print(f"\n5️⃣  Updating config files...")

    if args.no_update:
        print(f"\n   Page Token (copy manually):")
        print(f"   {target_page_token}")
    else:
        # Update MCP config
        content = MCP_CONFIG_PATH.read_text(encoding='utf-8')
        content = re.sub(
            r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'[^']+'",
            f"FACEBOOK_PAGE_ACCESS_TOKEN: '{target_page_token}'",
            content
        )
        MCP_CONFIG_PATH.write_text(content, encoding='utf-8')
        print(f"   ✅ Updated: {MCP_CONFIG_PATH}")

        # Update watcher config
        watcher_path = Path(__file__).parent / 'facebook_watcher.py'
        if watcher_path.exists():
            wcontent = watcher_path.read_text(encoding='utf-8')
            wcontent = re.sub(
                r"'PAGE_ACCESS_TOKEN':\s*'[^']+'",
                f"'PAGE_ACCESS_TOKEN': '{target_page_token}'",
                wcontent
            )
            watcher_path.write_text(wcontent, encoding='utf-8')
            print(f"   ✅ Updated: {watcher_path}")

        print(f"\n🎉 Done! Token valid for ~60 days.")
        print(f"   Now run: python scripts/facebook_post.py --test")


if __name__ == '__main__':
    main()
