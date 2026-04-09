#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Facebook Page Posting Script - Gold Tier

Posts to Facebook Page via Graph API without going through orchestrator/MCP.
Reads credentials from the existing facebook-mcp/index.js config.

Usage:
    python scripts/facebook_post.py "Your post message here"
    python scripts/facebook_post.py "Your message" --image "https://example.com/photo.jpg"
    python scripts/facebook_post.py "Your message" --link "https://your-site.com"
    python scripts/facebook_post.py --test                          (runs a test post)
    python scripts/facebook_post.py --recent                        (show recent posts)
    python scripts/facebook_post.py --insights                      (show page analytics)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests

# ============================================================
# Configuration - Reads from facebook-mcp/index.js CONFIG
# ============================================================

MCP_CONFIG_PATH = Path(__file__).parent.parent / 'mcp-servers' / 'facebook-mcp' / 'index.js'
GRAPH_API_BASE = 'https://graph.facebook.com/v19.0'


def load_fb_config():
    """Extract Facebook credentials from the MCP server's index.js CONFIG object."""
    if not MCP_CONFIG_PATH.exists():
        print(f"❌ MCP config not found: {MCP_CONFIG_PATH}")
        sys.exit(1)

    content = MCP_CONFIG_PATH.read_text(encoding='utf-8')

    config = {}
    patterns = {
        'FACEBOOK_PAGE_ACCESS_TOKEN': r"FACEBOOK_PAGE_ACCESS_TOKEN:\s*'([^']+)'",
        'FACEBOOK_PAGE_ID': r"FACEBOOK_PAGE_ID:\s*'([^']+)'",
        'INSTAGRAM_BUSINESS_ACCOUNT_ID': r"INSTAGRAM_BUSINESS_ACCOUNT_ID:\s*'([^']+)'",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        config[key] = match.group(1) if match else ''

    # Validate
    missing = [k for k in ['FACEBOOK_PAGE_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID']
               if not config.get(k) or config[k].startswith('YOUR_') or config[k] == 'DUMMY']

    if missing:
        print(f"❌ Missing Facebook config: {', '.join(missing)}")
        print(f"   Update CONFIG in mcp-servers/facebook-mcp/index.js")
        sys.exit(1)

    return config


# ============================================================
# Graph API Client
# ============================================================

def _api_request(endpoint, method='GET', params=None, data=None):
    """Make a request to Facebook Graph API."""
    config = load_fb_config()
    url = f"{GRAPH_API_BASE}{endpoint}"

    headers = {'Content-Type': 'application/json'}

    if method == 'GET':
        params = params or {}
        params['access_token'] = config['FACEBOOK_PAGE_ACCESS_TOKEN']
        response = requests.get(url, params=params, timeout=30)
    else:
        body = data or {}
        body['access_token'] = config['FACEBOOK_PAGE_ACCESS_TOKEN']
        response = requests.post(url, json=body, params=params, headers=headers, timeout=30)

    result = response.json()

    if not response.ok:
        error_msg = result.get('error', {}).get('message', response.text)
        raise Exception(f"Graph API Error ({response.status_code}): {error_msg}")

    return result


# ============================================================
# Facebook Operations
# ============================================================

def post_to_facebook(message, image_url=None, link=None, scheduled_time=None):
    """Post a message to Facebook Page."""
    config = load_fb_config()
    page_id = config['FACEBOOK_PAGE_ID']

    print(f"\n📝 Posting to Facebook Page (ID: {page_id})...")
    print(f"   Message: {message[:80]}{'...' if len(message) > 80 else ''}")
    if image_url:
        print(f"   Image: {image_url}")
    if link:
        print(f"   Link: {link}")
    if scheduled_time:
        print(f"   Scheduled: {scheduled_time}")

    # Build POST request
    post_data = {'message': message}

    if image_url:
        post_data['url'] = image_url

    if link:
        post_data['link'] = link

    if scheduled_time:
        post_data['published'] = False
        dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        post_data['scheduled_publish_time'] = int(dt.timestamp())
    else:
        post_data['published'] = True

    result = _api_request(f"/{page_id}/feed", method='POST', data=post_data)

    post_id = result.get('id', 'unknown')
    print(f"\n✅ Post published successfully!")
    print(f"   Post ID: {post_id}")
    print(f"   URL: https://facebook.com/{post_id}")

    return {'success': True, 'post_id': post_id, 'url': f"https://facebook.com/{post_id}"}


def get_recent_posts(limit=5):
    """Get recent posts from Facebook Page."""
    config = load_fb_config()
    page_id = config['FACEBOOK_PAGE_ID']

    print(f"\n📋 Fetching {limit} recent posts from Page {page_id}...")

    result = _api_request(f"/{page_id}/posts", params={
        'limit': str(limit),
        'fields': 'id,message,created_time,shares,likes.summary(true)',
    })

    posts = result.get('data', [])
    if not posts:
        print("   No posts found.")
        return []

    print(f"\n📊 Found {len(posts)} recent posts:\n")
    for i, post in enumerate(posts, 1):
        message = post.get('message', '(no message)')
        created = post.get('created_time', 'unknown')
        likes = post.get('likes', {}).get('summary', {}).get('total_count', 0)
        shares = post.get('shares', {}).get('count', 0)

        print(f"  {i}. [{created}]")
        print(f"     {message[:100]}{'...' if len(message) > 100 else ''}")
        print(f"     👍 {likes} likes | 🔄 {shares} shares")
        print()

    return posts


def get_page_insights():
    """Get Facebook Page analytics for the last 7 days."""
    config = load_fb_config()
    page_id = config['FACEBOOK_PAGE_ID']

    print(f"\n📈 Fetching Page insights for {page_id} (last 7 days)...")

    result = _api_request(f"/{page_id}/insights", params={
        'metric': 'page_posts,page_engaged_users,page_impressions,page_reach',
        'date_preset': 'last_7_days',
    })

    insights = result.get('data', [])
    if not insights:
        print("   No insights available.")
        return []

    print(f"\n📊 Page Insights (Last 7 Days):\n")
    for insight in insights:
        name = insight.get('name', 'unknown').replace('page_', '').replace('_', ' ').title()
        values = insight.get('values', [])
        if values:
            total = sum(v.get('value', 0) for v in values)
            print(f"  • {name}: {total:,}")

    print()
    return insights


def delete_post(post_id):
    """Delete a Facebook post."""
    print(f"\n🗑️  Deleting post: {post_id}")

    result = _api_request(f"/{post_id}", method='POST', data={'method': 'delete'})

    # Graph API returns True on successful delete
    print(f"✅ Post deleted successfully")
    return {'success': True, 'post_id': post_id}


def get_insights_page():
    """Get basic page info."""
    config = load_fb_config()
    page_id = config['FACEBOOK_PAGE_ID']

    result = _api_request(f"/{page_id}", params={
        'fields': 'name,followers_count,likes,about',
    })

    print(f"\n📘 Page: {result.get('name', 'Unknown')}")
    print(f"   Followers: {result.get('followers_count', 'N/A'):,}")
    print(f"   Likes: {result.get('likes', 'N/A'):,}")
    if result.get('about'):
        print(f"   About: {result.get('about', '')}")
    print()

    return result


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Post to Facebook Page via Graph API (Gold Tier)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/facebook_post.py "Hello from AI Employee!"
  python scripts/facebook_post.py "Check this out" --image "https://example.com/img.jpg"
  python scripts/facebook_post.py --test
  python scripts/facebook_post.py --recent
  python scripts/facebook_post.py --insights
        """
    )
    parser.add_argument('message', nargs='?', default=None, help='Post message text')
    parser.add_argument('--image', type=str, default=None, help='Image URL to include')
    parser.add_argument('--link', type=str, default=None, help='Link URL to include')
    parser.add_argument('--schedule', type=str, default=None, help='Schedule time (ISO format, e.g., 2026-04-09T10:00:00Z)')
    parser.add_argument('--recent', action='store_true', help='Show recent posts')
    parser.add_argument('--insights', action='store_true', help='Show page insights')
    parser.add_argument('--page-info', action='store_true', help='Show page info')
    parser.add_argument('--delete', type=str, default=None, help='Delete post by ID')
    parser.add_argument('--test', action='store_true', help='Run a test post')

    args = parser.parse_args()

    # Show page info
    if args.page_info:
        get_insights_page()
        return

    # Show recent posts
    if args.recent:
        get_recent_posts()
        return

    # Show insights
    if args.insights:
        get_page_insights()
        return

    # Delete post
    if args.delete:
        delete_post(args.delete)
        return

    # Determine message content
    if args.test:
        message = "🚀 AI Employee Gold Tier Test — Automated posting via Graph API ({:%Y-%m-%d %H:%M})".format(
            datetime.now()
        )
        print(f"\n🧪 Running test post...")
    elif args.message:
        message = args.message
    else:
        parser.print_help()
        print("\n❌ Error: Provide a message, or use --test for a test post")
        sys.exit(1)

    # Post to Facebook
    try:
        post_to_facebook(message, image_url=args.image, link=args.link, scheduled_time=args.schedule)
    except Exception as e:
        print(f"\n❌ Failed: {e}")

        # Diagnose common errors
        err = str(e).lower()
        if 'token' in err and ('expired' in err or 'invalid' in err):
            print("\n💡 Token expired or invalid.")
            print("   Regenerate from: https://developers.facebook.com/tools/explorer/")
        elif 'permission' in err or 'access' in err:
            print("\n💡 Check app has 'pages_manage_posts' permission.")
        elif 'network' in err or 'connection' in err:
            print("\n💡 Check your internet connection.")

        sys.exit(1)


if __name__ == '__main__':
    main()
