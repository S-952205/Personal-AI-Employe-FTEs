---
name: twitter-operations
description: Twitter/X operations via API v2
version: 1.0.0
---

# Twitter/X Operations

Manage Twitter/X account through API v2 integration.

## Setup Requirements

### Twitter Developer Setup

1. **Apply for Developer Account**
   - Go to https://developer.twitter.com/
   - Apply for Free tier (limited) or Basic tier
   - Wait for approval (can take 1-7 days)

2. **Create Project & App**
   - Create new Project
   - Create App within project
   - Note your credentials

3. **Generate Credentials**
   - API Key + Secret
   - Bearer Token
   - Access Token + Secret (with read/write permissions)

4. **Set Permissions**
   - App permissions: Read and Write
   - User authentication: Enabled

## MCP Server Tools

### Tweet Operations

#### `twitter_post`
Create a tweet.

```json
{
  "text": "Your tweet text (max 280 chars)",
  "mediaId": "MEDIA_ID",        // optional
  "replyToId": "TWEET_ID"       // optional for replies
}
```

#### `twitter_post_thread`
Create a thread of tweets.

```json
{
  "texts": [
    "First tweet in thread...",
    "Second tweet in thread...",
    "Third tweet in thread..."
  ]
}
```

### Reading Operations

#### `twitter_get_mentions`
Get recent mentions.

```json
{
  "limit": 20  // number of mentions
}
```

#### `twitter_get_tweet_analytics`
Get tweet engagement metrics.

```json
{
  "tweetId": "TWEET_ID"
}
```

#### `twitter_get_user_timeline`
Get tweets from any user.

```json
{
  "username": "elonmusk",  // without @
  "limit": 10
}
```

#### `twitter_get_recent_tweets`
Get your recent tweets.

```json
{
  "limit": 10
}
```

#### `twitter_weekly_summary`
Generate weekly Twitter summary with engagement metrics.

## Starting the MCP Server

```bash
# Install dependencies
cd mcp-servers/twitter-mcp
npm install

# Start server
npm start

# Or with PM2
pm2 start mcp-servers/twitter-mcp/index.js --name twitter-mcp
```

## Configuration Template

Edit `mcp-servers/twitter-mcp/index.js`:

```javascript
const CONFIG = {
  TWITTER_API_KEY: 'your_api_key',
  TWITTER_API_SECRET: 'your_api_secret',
  TWITTER_BEARER_TOKEN: 'your_bearer_token',
  TWITTER_ACCESS_TOKEN: 'your_access_token',
  TWITTER_ACCESS_TOKEN_SECRET: 'your_access_token_secret',
};
```

Also update `scripts/twitter_watcher.py`:

```python
TWITTER_CONFIG = {
    'BEARER_TOKEN': 'your_bearer_token',
    'USERNAME': 'your_twitter_handle',
}
```

## HITL Workflow

All tweets require human approval:

```
1. AI drafts tweet → Creates /Pending_Approval/TWITTER_POST_*.md
2. User reviews and moves to /Approved/
3. Orchestrator executes via MCP
4. Tweet published and logged
```

## Rate Limits (Free Tier)

- Posts: 1,500 tweets/month
- Reads: 10,000 tweets/month
- MCP server enforces: 15 tweets/day max, 5 min cooldown

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check Bearer Token is correct |
| Rate limited | Wait for reset, check tier limits |
| Tweet too long | Max 280 characters per tweet |
| App not authorized | Enable read/write in app settings |
