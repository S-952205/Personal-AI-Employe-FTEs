#!/usr/bin/env python3
"""
Facebook Token Diagnostic & Page Token Generator

This script:
1. Tests your current User Token
2. Lists all your Pages
3. Extracts the correct Page Access Token for posting
4. Optionally updates your config files

Usage:
    python scripts/fb_token_diagnostic.py
    python scripts/fb_token_diagnostic.py --update  (updates both config files)
"""

import re
import json
import sys
from pathlib import Path
import requests

# Use the token from your MCP config
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

def load_page_id():
    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')
    match = re.search(r"FACEBOOK_PAGE_ID:\s*'([^']+)'", content)
    if not match:
        print("❌ Page ID not found in config")
        sys.exit(1)
    return match.group(1)

def main():
    token = load_current_token()
    page_id = load_page_id()

    print("=" * 60)
    print("FACEBOOK TOKEN DIAGNOSTIC")
    print("=" * 60)

    # Step 1: Debug token info
    print("\n1️⃣  Debugging current token...")
    r = requests.get('https://graph.facebook.com/v19.0/me', params={
        'access_token': token,
        'fields': 'id,name'
    })
    
    if r.ok:
        data = r.json()
        print(f"   ✅ Token is valid")
        print(f"   Owner: {data.get('name')} (ID: {data.get('id')})")
    else:
        err = r.json().get('error', {})
        print(f"   ❌ Token INVALID: {err.get('message')}")
        print("   → You need to generate a NEW token first")
        print("   → Go to: https://developers.facebook.com/tools/explorer/")
        sys.exit(1)

    # Step 2: Debug token permissions
    print("\n2️⃣  Checking token permissions...")
    r = requests.get('https://graph.facebook.com/v19.0/oauth/access_token_info', params={
        'access_token': token,
    })
    
    if r.ok:
        data = r.json()
        token_type = data.get('type', 'unknown')
        scopes = data.get('scopes', [])
        print(f"   Token Type: {token_type}")
        print(f"   Permissions: {', '.join(scopes) if scopes else '(none shown)'}")
        
        has_pages_manage = 'pages_manage_posts' in scopes
        has_pages_read = 'pages_read_engagement' in scopes
        
        if not has_pages_manage:
            print(f"   ⚠️  MISSING: pages_manage_posts")
        if not has_pages_read:
            print(f"   ⚠️  MISSING: pages_read_engagement")
    else:
        print(f"   ⚠️  Could not check permissions (this is OK for some tokens)")

    # Step 3: Get User's Pages and extract Page Token
    print(f"\n3️⃣  Fetching your Pages (to extract Page Access Token)...")
    r = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={
        'access_token': token,
        'fields': 'id,name,access_token,tasks'
    })
    
    if not r.ok:
        err = r.json().get('error', {})
        print(f"   ❌ Failed: {err.get('message')}")
        print("   → Make sure your token has 'pages_show_list' permission")
        sys.exit(1)

    pages = r.json().get('data', [])
    
    if not pages:
        print("   ❌ No pages found. You must be an admin of a Facebook Page.")
        print("   → Create a Page first: https://www.facebook.com/pages/create")
        sys.exit(1)

    print(f"   Found {len(pages)} Page(s):\n")
    
    target_page_token = None
    target_page = None

    for i, page in enumerate(pages, 1):
        pid = page.get('id')
        pname = page.get('name')
        ptasks = page.get('tasks', [])
        ptoken = page.get('access_token', '')
        
        print(f"  {i}. {pname}")
        print(f"     Page ID: {pid}")
        print(f"     Tasks: {', '.join(ptasks) if ptasks else '(none listed)'}")
        print(f"     Token preview: {ptoken[:40]}...")
        print()
        
        if pid == page_id:
            target_page_token = ptoken
            target_page = page
            print(f"   ✅ This is your configured Page!")

    if not target_page_token:
        print(f"\n   ⚠️  Page ID {page_id} not found in your pages.")
        print(f"   Available Page IDs: {[p.get('id') for p in pages]}")
        print(f"   → Update FACEBOOK_PAGE_ID in mcp-servers/facebook-mcp/index.js")
        
        # Offer to use first available page
        if pages:
            use_first = input(f"\n   Use '{pages[0].get('name')}' instead? (y/n): ").strip().lower()
            if use_first == 'y':
                target_page_token = pages[0].get('access_token')
                target_page = pages[0]
                page_id = target_page.get('id')
            else:
                sys.exit(1)
        else:
            sys.exit(1)

    # Step 4: Test the Page Token
    print(f"\n4️⃣  Testing Page Access Token...")
    r = requests.get(f'https://graph.facebook.com/v19.0/{page_id}', params={
        'access_token': target_page_token,
        'fields': 'name,link'
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

    # Step 5: Test posting with Page Token
    print(f"\n5️⃣  Test posting with Page Token...")
    test_message = "🔧 Token diagnostic test post ({})".format(
        __import__('datetime').datetime.now().strftime('%H:%M:%S')
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
        print(f"   URL: https://facebook.com/{post_id}")
        
        # Clean up test post
        print(f"\n   Deleting test post...")
        r2 = requests.delete(f'https://graph.facebook.com/v19.0/{post_id}', params={
            'access_token': target_page_token,
        })
        if r2.ok:
            print(f"   ✅ Deleted")
        else:
            print(f"   ⚠️  Could not delete (manual cleanup needed)")
    else:
        err = r.json().get('error', {})
        print(f"   ❌ Post failed: {err.get('message')}")
        print(f"\n   This Page Token cannot post. Possible causes:")
        print(f"   • Your app is in Development mode and needs App Review")
        print(f"   • You need admin role on this Page")
        print(f"   • pages_manage_posts permission wasn't approved")

    # Step 6: Offer to update config
    print(f"\n6️⃣  Update config files with this Page Token?")
    
    update = input("   Update config? (y/n): ").strip().lower()
    if update == 'y':
        # Update MCP config
        mcp_path = MCP_CONFIG_PATH
        content = mcp_path.read_text(encoding='utf-8')
        content = re.sub(
            r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'[^']+'",
            f"FACEBOOK_PAGE_ACCESS_TOKEN: '{target_page_token}'",
            content
        )
        mcp_path.write_text(content, encoding='utf-8')
        print(f"   ✅ Updated: {mcp_path}")
        
        # Update watcher config
        watcher_path = Path(__file__).parent.parent / 'scripts' / 'facebook_watcher.py'
        if watcher_path.exists():
            wcontent = watcher_path.read_text(encoding='utf-8')
            wcontent = re.sub(
                r"'PAGE_ACCESS_TOKEN':\s*'[^']+'",
                f"'PAGE_ACCESS_TOKEN': '{target_page_token}'",
                wcontent
            )
            watcher_path.write_text(wcontent, encoding='utf-8')
            print(f"   ✅ Updated: {watcher_path}")
        
        print(f"\n🎉 Done! Now run: python scripts/facebook_post.py --test")
    else:
        print(f"\n   Page Token (copy this if needed):")
        print(f"   {target_page_token}")
        print(f"\n   Manually update these files:")
        print(f"   • mcp-servers/facebook-mcp/index.js → FACEBOOK_PAGE_ACCESS_TOKEN")
        print(f"   • scripts/facebook_watcher.py → PAGE_ACCESS_TOKEN")


if __name__ == '__main__':
    main()
