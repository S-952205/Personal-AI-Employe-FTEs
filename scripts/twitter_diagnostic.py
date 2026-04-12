#!/usr/bin/env python3
"""
Twitter Credential Diagnostic Script

Tests your Twitter API credentials and OAuth 1.0a implementation.
Shows exactly what's wrong and how to fix it.

Usage:
    python scripts/twitter_diagnostic.py
"""

import re
import sys
import time
import hmac
import hashlib
import base64
from urllib.parse import quote
from pathlib import Path

import requests

# ============================================================
# Load Config
# ============================================================

MCP_CONFIG_PATH = Path(__file__).parent.parent / 'mcp-servers' / 'twitter-mcp' / 'index.js'

def load_config():
    if not MCP_CONFIG_PATH.exists():
        print(f"❌ Config not found: {MCP_CONFIG_PATH}")
        sys.exit(1)
    
    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')
    config = {}
    
    for key in ['TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_BEARER_TOKEN', 
                'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_TOKEN_SECRET']:
        m = re.search(rf"{key}:\s*'([^']+)'", content)
        config[key] = m.group(1) if m else ''
    
    return config

def mask(s):
    if len(s) <= 8:
        return '****'
    return s[:4] + '...' + s[-4:]

# ============================================================
# OAuth 1.0a Implementation (same as orchestrator)
# ============================================================

def build_oauth_header(method, url, config, extra_params=None):
    """Build OAuth 1.0a Authorization header."""
    nonce = base64.b64encode(hashlib.md5(str(time.time()).encode()).digest()).decode()[:32]
    timestamp = str(int(time.time()))
    
    oauth_params = {
        'oauth_consumer_key': config['TWITTER_API_KEY'],
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_token': config['TWITTER_ACCESS_TOKEN'],
        'oauth_version': '1.0',
    }
    
    if extra_params:
        oauth_params.update(extra_params)
    
    # Build parameter string (sorted, encoded)
    param_str = '&'.join(
        f"{quote(k, safe='~')}={quote(v, safe='~')}"
        for k, v in sorted(oauth_params.items())
    )
    
    # Build signature base string
    encoded_url = quote(url, safe='~')
    base_string = f"{method.upper()}&{encoded_url}&{quote(param_str, safe='~')}"
    
    # Build signing key
    signing_key = f"{quote(config['TWITTER_API_SECRET'], safe='~')}&{quote(config['TWITTER_ACCESS_TOKEN_SECRET'], safe='~')}"
    
    # HMAC-SHA1 signature
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    oauth_params['oauth_signature'] = signature
    
    # Build header
    header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="~")}="{quote(v, safe="~")}"'
        for k, v in sorted(oauth_params.items())
    )
    
    return header

# ============================================================
# Tests
# ============================================================

def main():
    config = load_config()
    
    print("="*60)
    print("TWITTER CREDENTIAL DIAGNOSTIC")
    print("="*60)
    
    # Show credentials (masked)
    print(f"\n1️⃣  Credentials loaded from {MCP_CONFIG_PATH.name}")
    print(f"   API Key:           {mask(config['TWITTER_API_KEY'])}")
    print(f"   API Secret:        {mask(config['TWITTER_API_SECRET'])}")
    print(f"   Bearer Token:      {mask(config['TWITTER_BEARER_TOKEN'])}")
    print(f"   Access Token:      {mask(config['TWITTER_ACCESS_TOKEN'])}")
    print(f"   Access Token Sec:  {mask(config['TWITTER_ACCESS_TOKEN_SECRET'])}")
    
    missing = [k for k in config.keys() if not config[k] or config[k].startswith('YOUR_')]
    if missing:
        print(f"\n❌ Missing credentials: {', '.join(missing)}")
        print("   Update mcp-servers/twitter-mcp/index.js")
        sys.exit(1)
    
    # Test 1: Bearer Token (read-only)
    print(f"\n2️⃣  Testing Bearer Token (read-only access)...")
    r = requests.get('https://api.twitter.com/2/tweets/search/recent', params={
        'query': 'test',
        'max_results': '1'
    }, headers={
        'Authorization': f"Bearer {config['TWITTER_BEARER_TOKEN']}"
    }, timeout=10)
    
    if r.status_code == 200:
        print(f"   ✅ Bearer Token is valid (can read public data)")
    elif r.status_code == 403:
        print(f"   ⚠️  Bearer Token valid but rate limited or restricted")
    else:
        err = r.json() if r.text.startswith('{') else {}
        print(f"   ❌ Bearer Token failed: {err.get('title', r.text[:100])}")
        print("   → Regenerate Bearer Token at https://developer.twitter.com/en/portal/")
    
    # Test 2: OAuth 1.0a - Get user info (read)
    print(f"\n3️⃣  Testing OAuth 1.0a - Get user info (/users/me)...")
    url = 'https://api.twitter.com/2/users/me'
    auth_header = build_oauth_header('GET', url, config, {'user.fields': 'id,username,name'})
    
    r = requests.get(url, params={'user.fields': 'id,username,name'}, headers={
        'Authorization': auth_header,
    }, timeout=10)
    
    if r.status_code == 200:
        user = r.json().get('data', {})
        print(f"   ✅ OAuth 1.0a works! User: @{user.get('username')} ({user.get('name')})")
        print(f"   User ID: {user.get('id')}")
    else:
        err = r.json() if r.text.startswith('{') else {}
        print(f"   ❌ OAuth 1.0a failed ({r.status_code}): {err.get('detail', err.get('title', r.text[:100]))}")
        
        if r.status_code == 401:
            print(f"\n   🔍 DIAGNOSIS: Access Token doesn't match App Key/Secret")
            print(f"   This usually happens when:")
            print(f"   • You regenerated Access Token but API Key/Secret are old")
            print(f"   • You regenerated API Key/Secret but Access Token is old")
            print(f"   • The token was revoked")
            print(f"\n   ✅ FIX: Go to https://developer.twitter.com/en/portal/")
            print(f"   → Go to your App → 'Keys and tokens'")
            print(f"   → Regenerate ALL 5 credentials (API Key, Secret, Access Token, Secret)")
            print(f"   → Update mcp-servers/twitter-mcp/index.js with ALL new values")
        elif r.status_code == 403:
            print(f"   → App doesn't have required permissions")
            print(f"   → Change app to 'Read and Write' at developer portal")
        elif 'oauth' in r.text.lower() or 'signature' in r.text.lower():
            print(f"   → OAuth signature calculation may be incorrect")
        
        # Try alternative: use oauth library if available
        try:
            print(f"\n   🔄 Trying alternative OAuth library (requests-oauthlib)...")
            from requests_oauthlib import OAuth1
            
            oauth = OAuth1(
                config['TWITTER_API_KEY'],
                config['TWITTER_API_SECRET'],
                config['TWITTER_ACCESS_TOKEN'],
                config['TWITTER_ACCESS_TOKEN_SECRET'],
                signature_method='HMAC-SHA1'
            )
            
            r = requests.get('https://api.twitter.com/2/users/me', params={
                'user.fields': 'id,username'
            }, auth=oauth, timeout=10)
            
            if r.status_code == 200:
                user = r.json().get('data', {})
                print(f"   ✅ Library OAuth works! User: @{user.get('username')}")
                print(f"   → Our custom OAuth has a bug. Use requests-oauthlib instead.")
                print(f"   → Run: pip install requests-oauthlib")
            else:
                print(f"   ❌ Library also failed: {r.status_code}")
                print(f"   → Credentials are definitely wrong")
        except ImportError:
            print(f"\n   💡 Install requests-oauthlib for better OAuth:")
            print(f"   pip install requests-oauthlib")
    
    # Test 3: Try posting with requests-oauthlib
    print(f"\n4️⃣  Testing POST to /2/tweets...")
    try:
        from requests_oauthlib import OAuth1
        
        oauth = OAuth1(
            config['TWITTER_API_KEY'],
            config['TWITTER_API_SECRET'],
            config['TWITTER_ACCESS_TOKEN'],
            config['TWITTER_ACCESS_TOKEN_SECRET'],
            signature_method='HMAC-SHA1'
        )
        
        test_text = f"🔧 Twitter diagnostic test ({time.strftime('%H:%M:%S')})"
        
        r = requests.post(
            'https://api.twitter.com/2/tweets',
            json={'text': test_text},
            auth=oauth,
            timeout=10
        )
        
        if r.status_code == 201:
            tweet_id = r.json().get('data', {}).get('id')
            print(f"   ✅ POST SUCCESSFUL!")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   URL: https://twitter.com/i/web/status/{tweet_id}")
            
            # Clean up test tweet
            print(f"\n   Deleting test tweet...")
            r2 = requests.delete(
                f'https://api.twitter.com/2/tweets/{tweet_id}',
                auth=oauth,
                timeout=10
            )
            if r2.status_code == 200:
                print(f"   ✅ Deleted")
        else:
            err = r.json() if r.text.startswith('{') else {}
            print(f"   ❌ POST failed ({r.status_code}): {err.get('detail', err.get('title', r.text[:100]))}")
            
            if r.status_code == 403:
                print(f"   → App still doesn't have Write permission")
                print(f"   → Check: https://developer.twitter.com/en/portal/")
                print(f"   → Project → App settings → App permissions → 'Read and Write'")
            elif r.status_code == 401:
                print(f"   → Credentials mismatch or token revoked")
    except ImportError:
        print(f"   ⚠️  requests-oauthlib not installed")
        print(f"   → pip install requests-oauthlib")
        print(f"   → Then run this script again")

    print(f"\n{'='*60}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
