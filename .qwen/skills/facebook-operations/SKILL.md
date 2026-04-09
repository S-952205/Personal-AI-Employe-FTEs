---
name: facebook-operations
description: Facebook Page and Instagram Business operations via Graph API
version: 1.0.0
---

# Facebook & Instagram Operations

Manage Facebook Page and Instagram Business account through Graph API integration.

## Setup Requirements

### Facebook Developer Setup

1. **Create Facebook Developer Account**
   - Go to https://developers.facebook.com/
   - Complete developer verification

2. **Create App**
   - Create new app (Business type)
   - Note your App ID and App Secret

3. **Add Products**
   - Add "Facebook Login" product
   - Add "Instagram Basic Display" product

4. **Configure Permissions**
   Required permissions:
   - `pages_manage_posts` - Create posts
   - `pages_read_engagement` - Read comments/insights
   - `pages_manage_engagement` - Respond to comments
   - `instagram_basic` - Instagram access
   - `instagram_content_publish` - Publish Instagram posts

5. **Generate Page Access Token**
   - Use Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your app
   - Generate token with required permissions
   - Copy token for configuration

6. **Find Page ID**
   - Go to your Facebook Page
   - Settings → Page Info → Facebook Page ID

7. **Link Instagram Business Account**
   - Instagram must be converted to Business account
   - Link to Facebook Page in Instagram settings

## MCP Server Tools

### Facebook Operations

#### `facebook_post`
Create a post on Facebook Page.

```json
{
  "message": "Your post text here",
  "imageUrl": "https://example.com/image.jpg",  // optional
  "link": "https://example.com",                // optional
  "scheduledTime": "2026-04-06T10:00:00Z"       // optional
}
```

#### `facebook_get_insights`
Get Page analytics.

```json
{
  "dateRange": "last_7_days"  // today, yesterday, last_7_days, last_30_days
}
```

#### `facebook_get_posts`
Get recent posts.

```json
{
  "limit": 10  // number of posts
}
```

#### `facebook_delete_post`
Delete a post.

```json
{
  "postId": "PAGEID_POSTID"
}
```

### Instagram Operations

#### `instagram_post`
Post to Instagram (requires image).

```json
{
  "caption": "Your caption here",
  "imageUrl": "https://example.com/image.jpg",  // required
  "scheduledTime": "2026-04-06T10:00:00Z"       // optional
}
```

#### `instagram_get_insights`
Get Instagram analytics.

```json
{
  "dateRange": "last_7_days"
}
```

#### `instagram_get_comments`
Get comments on a post.

```json
{
  "mediaId": "MEDIA_ID",
  "limit": 20
}
```

#### `social_weekly_summary`
Generate combined Facebook + Instagram weekly summary.

## Starting the MCP Server

```bash
# Install dependencies
cd mcp-servers/facebook-mcp
npm install

# Start server
npm start

# Or with PM2
pm2 start mcp-servers/facebook-mcp/index.js --name facebook-mcp
```

## Configuration Template

Edit `mcp-servers/facebook-mcp/index.js`:

```javascript
const CONFIG = {
  FACEBOOK_APP_ID: 'your_app_id',
  FACEBOOK_APP_SECRET: 'your_app_secret',
  FACEBOOK_PAGE_ACCESS_TOKEN: 'your_page_token',
  FACEBOOK_PAGE_ID: 'your_page_id',
  INSTAGRAM_BUSINESS_ACCOUNT_ID: 'your_ig_account_id',
};
```

Also update `scripts/facebook_watcher.py`:

```python
FACEBOOK_CONFIG = {
    'PAGE_ACCESS_TOKEN': 'your_page_token',
    'PAGE_ID': 'your_page_id',
    'INSTAGRAM_ACCOUNT_ID': 'your_ig_account_id',
}
```

## HITL Workflow

All social media posts require human approval:

```
1. AI drafts post → Creates /Pending_Approval/FACEBOOK_POST_*.md
2. User reviews and moves to /Approved/
3. Orchestrator executes via MCP
4. Post published and logged
```

## Rate Limits

- Facebook: ~200 posts/hour per page
- Instagram: ~25 posts/day per account
- MCP server enforces: 10 posts/day max, 5 min cooldown

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Token expired | Regenerate from Graph API Explorer |
| Permission error | Check app has required permissions |
| Instagram post fails | Ensure image URL is publicly accessible |
| Rate limited | Wait for cooldown, reduce posting frequency |
