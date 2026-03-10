---
name: linkedin-operations
description: |
  LinkedIn operations via Playwright MCP. Create posts, send messages, connect with people,
  and manage LinkedIn presence. Use for business networking, content sharing, and lead generation.
  Requires LinkedIn session authentication.
---

# LinkedIn Operations

Manage LinkedIn presence via browser automation MCP server.

## Prerequisites

1. Playwright installed: `playwright install`
2. LinkedIn session (first run requires manual login)
3. LinkedIn MCP server running

## Server Lifecycle

### Start LinkedIn MCP Server

```bash
cd mcp-servers/linkedin-mcp
npm start
```

### Stop LinkedIn MCP Server

```bash
# Close the terminal running the server
```

## Quick Reference

### Create Post

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool create_post \
  --params '{"content": "Business update text", "hashtags": ["business", "growth"]}'
```

### Comment on Post

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool comment_on_post \
  --params '{"postUrl": "https://linkedin.com/posts/...", "comment": "Great insights!"}'
```

### Connect with Person

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool connect_with_person \
  --params '{"profileUrl": "https://linkedin.com/in/...", "message": "Hi, lets connect"}'
```

### Send Message

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool send_message \
  --params '{"recipientName": "John Doe", "message": "Hello John"}'
```

### Get Notifications

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool get_notifications \
  --params '{"maxResults": 10}'
```

## Workflow: Auto-Post Business Update

1. Read business goals from Business_Goals.md
2. Draft post content based on milestones/achievements
3. **Create approval request** (posts require approval)
4. When approved, execute `create_post`
5. Log action in processing notes

## Workflow: Respond to Messages

1. Check LinkedIn messages from watcher
2. Read message content from action file
3. Draft appropriate response
4. **Create approval request** for new contacts
5. Send via `send_message` when approved

## Workflow: Connection Requests

1. Identify relevant professionals from notifications
2. Review profile for business relevance
3. **Create approval request** for VIP connections
4. Send via `connect_with_person` with personalized message

## Human-in-the-Loop

**Require approval before action:**
- All LinkedIn posts (draft first, then approve)
- Connection requests to VIPs or decision makers
- Messages to new contacts
- Comments on sensitive topics

**Can do directly:**
- Responding to existing connections
- General networking comments
- Connection requests from relevant industries

## Content Guidelines

### Post Types
- Business milestones
- Project completions
- Industry insights
- Thought leadership
- Client success stories (with permission)

### Posting Frequency
- 2-3 times per week (configure in Company Handbook)
- Avoid weekends unless urgent
- Best times: 9-11 AM, 2-4 PM weekdays

## Tool Reference

| Tool | Purpose | Approval Required |
|------|---------|-------------------|
| `create_post` | Create LinkedIn post | Always (draft first) |
| `comment_on_post` | Comment on posts | For sensitive topics |
| `connect_with_person` | Send connection request | For VIPs |
| `send_message` | Send direct message | For new contacts |
| `get_notifications` | Get notifications | Never |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Not logged in | Manually login on first run, session saves |
| Session expired | Delete `linkedin_session/` and re-login |
| Element not found | LinkedIn UI changed, update selectors in MCP |
| Rate limited | Wait 24 hours, reduce automation frequency |

## ⚠️ Terms of Service Notice

Use LinkedIn automation responsibly:
- Respect LinkedIn's Terms of Service
- Don't spam or send bulk unsolicited messages
- Maintain human-like behavior patterns
- Monitor for any account warnings
