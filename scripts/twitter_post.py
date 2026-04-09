#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Twitter/X Posting Script - Gold Tier

Posts to Twitter/X via API v2 without going through orchestrator/MCP.
Reads credentials from the existing twitter-mcp/index.js config.

Usage:
    python scripts/twitter_post.py "Your tweet here"
    python scripts/twitter_post.py --test                          (runs a test tweet)
    python scripts/twitter_post.py --recent                        (show recent tweets)
    python scripts/twitter_post.py --mentions                      (show recent mentions)
    python scripts/twitter_post.py --analytics                     (show tweet analytics)
"""

import argparse
import base64
import hashlib
import hmac
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode

import requests

# ============================================================
# Configuration - Reads from twitter-mcp/index.js CONFIG
# ============================================================

MCP_CONFIG_PATH = Path(__file__).parent.parent / 'mcp-servers' / 'twitter-mcp' / 'index.js'
API_BASE = 'https://api.twitter.com/2'


def load_tw_config():
    """Extract Twitter credentials from the MCP server's index.js CONFIG object."""
    if not MCP_CONFIG_PATH.exists():
        print(f"❌ MCP config not found: {MCP_CONFIG_PATH}")
        sys.exit(1)

    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')

    config = {}
    patterns = {
        'TWITTER_API_KEY': r"TWITTER_API_KEY:\s*'([^']+)'",
        'TWITTER_API_SECRET': r"TWITTER_API_SECRET:\s*'([^']+)'",
        'TWITTER_BEARER_TOKEN': r"TWITTER_BEARER_TOKEN:\s*'([^']+)'",
        'TWITTER_ACCESS_TOKEN': r"TWITTER_ACCESS_TOKEN:\s*'([^']+)'",
        'TWITTER_ACCESS_TOKEN_SECRET': r"TWITTER_ACCESS_TOKEN_SECRET:\s*'([^']+)'",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        config[key] = match.group(1) if match else ''

    # Validate
    missing = [k for k in patterns.keys() if not config.get(k) or config[k].startswith('YOUR_')]
    if missing:
        print(f"❌ Missing Twitter config: {', '.join(missing)}")
        print(f"   Update CONFIG in mcp-servers/twitter-mcp/index.js")
        sys.exit(1)

    return config


# ============================================================
# OAuth 1.0a Signature (required for POST requests to Twitter API v2)
# ============================================================

def _oauth1_signature(method, url, params, consumer_secret, token_secret):
    """Generate OAuth 1.0a HMAC-SHA1 signature for Twitter API."""
    # Build parameter string
    param_str = '&'.join(
        f"{quote(k, safe='~')}={quote(v, safe='~')}"
        for k, v in sorted(params.items())
    )

    # Build signature base string
    base_string = f"{method.upper()}&{quote(url, safe='~')}&{quote(param_str, safe='~')}"

    # Build signing key
    signing_key = f"{quote(consumer_secret, safe='~')}&{quote(token_secret, safe='~')}"

    # HMAC-SHA1
    signature = hmac.new(
        signing_key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha1
    ).digest()

    return base64.b64encode(signature).decode('utf-8')


def _build_auth_header(method, url, params, config):
    """Build OAuth 1.0a Authorization header."""
    nonce = base64.b64encode(hashlib.md5(str(time.time()).encode()).digest()).decode('utf-8')[:32]
    timestamp = str(int(time.time()))

    oauth_params = {
        'oauth_consumer_key': config['TWITTER_API_KEY'],
        'oauth_nonce': nonce,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_token': config['TWITTER_ACCESS_TOKEN'],
        'oauth_version': '1.0',
    }

    # Combine all params for signature
    all_params = {**params, **oauth_params}

    # Generate signature
    signature = _oauth1_signature(method, url, all_params,
                                   config['TWITTER_API_SECRET'],
                                   config['TWITTER_ACCESS_TOKEN_SECRET'])

    oauth_params['oauth_signature'] = signature

    # Build header
    header = 'OAuth ' + ', '.join(
        f'{quote(k, safe="~")}="{quote(v, safe="~")}"'
        for k, v in sorted(oauth_params.items())
    )

    return header


# ============================================================
# Twitter API Client
# ============================================================

def _api_request(endpoint, method='GET', params=None, json_body=None, force_oauth=False):
    """Make a request to Twitter API v2."""
    config = load_tw_config()
    url = f"{API_BASE}{endpoint}"

    if method == 'GET' and not force_oauth:
        # Use Bearer Token for public read requests
        params = params or {}
        headers = {
            'Authorization': f"Bearer {config['TWITTER_BEARER_TOKEN']}",
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
    elif method == 'GET' and force_oauth:
        # Use OAuth 1.0a for GET requests that require user context
        headers = {
            'Authorization': _build_auth_header(method, url, params or {}, config),
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
    else:
        # Use OAuth 1.0a for POST/DELETE requests
        headers = {
            'Authorization': _build_auth_header(method, url, params or {}, config),
            'Content-Type': 'application/json',
        }
        if method == 'POST':
            response = requests.post(url, json=json_body, params=params, headers=headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, json=json_body, params=params, headers=headers, timeout=30)
        else:
            response = requests.post(url, json=json_body, params=params, headers=headers, timeout=30)

    if not response.ok:
        try:
            err_data = response.json()
            errors = err_data.get('errors', [])
            error_msg = '; '.join(e.get('message', str(e)) for e in errors) if errors else response.text
        except:
            error_msg = response.text
        raise Exception(f"Twitter API Error ({response.status_code}): {error_msg}")

    return response.json()


# ============================================================
# Twitter Operations
# ============================================================

def post_to_twitter(text, reply_to=None):
    """Post a tweet."""
    print(f"\n🐦 Posting to Twitter/X...")
    print(f"   Tweet: {text[:80]}{'...' if len(text) > 80 else ''}")

    payload = {'text': text}
    if reply_to:
        payload['reply'] = {'in_reply_to_tweet_id': reply_to}

    result = _api_request('/tweets', method='POST', json_body=payload)

    tweet_id = result.get('data', {}).get('id', 'unknown')
    print(f"\n✅ Tweet published successfully!")
    print(f"   Tweet ID: {tweet_id}")
    print(f"   URL: https://twitter.com/i/web/status/{tweet_id}")

    return {'success': True, 'tweet_id': tweet_id}


def get_recent_tweets(limit=5):
    """Get your recent tweets."""
    config = load_tw_config()

    # First get user ID
    user = _api_request('/users/me', params={'user.fields': 'id,username,name'}, force_oauth=True)
    user_id = user.get('data', {}).get('id')
    username = user.get('data', {}).get('username')

    if not user_id:
        print("   ❌ Could not fetch user info")
        return []

    print(f"\n📋 Fetching {limit} recent tweets from @{username}...")

    result = _api_request(f'/users/{user_id}/tweets', params={
        'max_results': str(limit),
        'tweet.fields': 'created_at,public_metrics,conversation_id',
        'exclude': 'retweets',
    }, force_oauth=True)

    tweets = result.get('data', [])
    if not tweets:
        print("   No tweets found.")
        return []

    print(f"\n📊 Found {len(tweets)} recent tweets:\n")
    for i, tweet in enumerate(tweets, 1):
        text = tweet.get('text', '(no text)')
        created = tweet.get('created_at', 'unknown')
        metrics = tweet.get('public_metrics', {})
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)

        print(f"  {i}. [{created}]")
        print(f"     {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"     ❤️ {likes} | 🔄 {retweets} | 💬 {replies}")
        print()

    return tweets


def get_recent_mentions(limit=5):
    """Get recent @mentions."""
    config = load_tw_config()

    # Get user ID
    user = _api_request('/users/me', params={'user.fields': 'id,username'}, force_oauth=True)
    user_id = user.get('data', {}).get('id')
    username = user.get('data', {}).get('username')

    if not user_id:
        print("   ❌ Could not fetch user info")
        return []

    print(f"\n📋 Fetching recent @mentions for @{username}...")

    result = _api_request(f'/users/{user_id}/mentions', params={
        'max_results': str(limit),
        'tweet.fields': 'created_at,public_metrics,author_id',
    }, force_oauth=True)

    mentions = result.get('data', [])
    if not mentions:
        print("   No mentions found.")
        return []

    print(f"\n📊 Found {len(mentions)} recent mentions:\n")
    for i, mention in enumerate(mentions, 1):
        text = mention.get('text', '(no text)')
        created = mention.get('created_at', 'unknown')
        metrics = mention.get('public_metrics', {})

        print(f"  {i}. [{created}]")
        print(f"     {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"     ❤️ {metrics.get('like_count', 0)} | 💬 {metrics.get('reply_count', 0)}")
        print()

    return mentions


def get_analytics(tweet_id=None):
    """Get tweet analytics."""
    config = load_tw_config()

    # Get user ID
    user = _api_request('/users/me', params={'user.fields': 'id,username'}, force_oauth=True)
    user_id = user.get('data', {}).get('id')
    username = user.get('data', {}).get('username')

    if not user_id:
        print("   ❌ Could not fetch user info")
        return []

    if tweet_id:
        print(f"\n📈 Fetching analytics for tweet {tweet_id}...")
        result = _api_request(f'/tweets/{tweet_id}', params={
            'tweet.fields': 'created_at,public_metrics,non_public_metrics,organic_metrics',
        })
        tweets = [result.get('data', {})]
    else:
        print(f"\n📈 Fetching analytics for recent tweets from @{username}...")
        result = _api_request(f'/users/{user_id}/tweets', params={
            'max_results': '5',
            'tweet.fields': 'created_at,public_metrics,organic_metrics',
            'exclude': 'retweets',
        }, force_oauth=True)
        tweets = result.get('data', [])

    if not tweets:
        print("   No analytics available.")
        return []

    print(f"\n📊 Analytics:\n")
    for i, tweet in enumerate(tweets, 1):
        text = tweet.get('text', '(no text)')[:60]
        metrics = tweet.get('public_metrics', {})
        organic = tweet.get('organic_metrics', {}) or {}

        print(f"  {i}. {text}...")
        print(f"     Impressions: {organic.get('impression_count', metrics.get('impression_count', 'N/A')):,}")
        print(f"     Likes: {metrics.get('like_count', 0):,} | Retweets: {metrics.get('retweet_count', 0):,}")
        print(f"     Replies: {metrics.get('reply_count', 0):,} | Bookmarks: {metrics.get('bookmark_count', 0):,}")
        print()

    return tweets


def delete_tweet(tweet_id):
    """Delete a tweet."""
    print(f"\n🗑️  Deleting tweet: {tweet_id}")

    result = _api_request(f'/tweets/{tweet_id}', method='DELETE')

    deleted = result.get('data', {}).get('deleted', False)
    if deleted:
        print(f"✅ Tweet deleted successfully")
    else:
        print(f"⚠️  Response: {result}")

    return {'success': deleted, 'tweet_id': tweet_id}


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Post to Twitter/X via API v2 (Gold Tier)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/twitter_post.py "Hello from AI Employee!"
  python scripts/twitter_post.py --test
  python scripts/twitter_post.py --recent
  python scripts/twitter_post.py --mentions
  python scripts/twitter_post.py --analytics
        """
    )
    parser.add_argument('message', nargs='?', default=None, help='Tweet text')
    parser.add_argument('--reply-to', type=str, default=None, help='Reply to tweet ID')
    parser.add_argument('--recent', action='store_true', help='Show recent tweets')
    parser.add_argument('--mentions', action='store_true', help='Show recent mentions')
    parser.add_argument('--analytics', action='store_true', help='Show tweet analytics')
    parser.add_argument('--delete', type=str, default=None, help='Delete tweet by ID')
    parser.add_argument('--test', action='store_true', help='Run a test tweet')

    args = parser.parse_args()

    # Show recent tweets
    if args.recent:
        get_recent_tweets()
        return

    # Show mentions
    if args.mentions:
        get_recent_mentions()
        return

    # Show analytics
    if args.analytics:
        get_analytics()
        return

    # Delete tweet
    if args.delete:
        delete_tweet(args.delete)
        return

    # Determine message content
    if args.test:
        message = "🚀 AI Employee Gold Tier Test — Automated Twitter posting via API v2 ({:%Y-%m-%d %H:%M})".format(
            datetime.now()
        )
        print(f"\n🧪 Running test tweet...")
    elif args.message:
        message = args.message
        if len(message) > 280:
            print(f"⚠️  Tweet truncated from {len(message)} to 280 chars")
            message = message[:280]
    else:
        parser.print_help()
        print("\n❌ Error: Provide a message, or use --test for a test tweet")
        sys.exit(1)

    # Post to Twitter
    try:
        post_to_twitter(message, reply_to=args.reply_to)
    except Exception as e:
        print(f"\n❌ Failed: {e}")

        # Diagnose common errors
        err = str(e).lower()
        if 'unauthorized' in err or 'authentic' in err:
            print("\n💡 Authentication failed.")
            print("   Check API Key/Secret and Access Token/Secret in mcp-servers/twitter-mcp/index.js")
        elif 'rate limit' in err:
            print("\n💡 Rate limited. Wait and try again later.")
            print("   Twitter API v2 free tier: 15 tweets/day")
        elif 'duplicate' in err:
            print("\n💡 Duplicate tweet. Content must be unique.")

        sys.exit(1)


if __name__ == '__main__':
    main()
