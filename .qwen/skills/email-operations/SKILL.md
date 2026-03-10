---
name: email-operations
description: |
  Email operations via Gmail MCP. Send emails, create drafts, search emails,
  and manage email communications. Use for replying to messages, sending notifications,
  and business communications. Requires Gmail credentials setup.
---

# Email Operations

Send, draft, and search emails via Gmail MCP server.

## Prerequisites

1. Gmail credentials.json in project root
2. Run authentication: `python scripts/gmail_auth.py`
3. Email MCP server running

## Server Lifecycle

### Start Email MCP Server

```bash
cd mcp-servers/email-mcp
npm start
```

### Stop Email MCP Server

```bash
# The server runs on stdio, close the terminal to stop
```

## Quick Reference

### Send Email

```bash
# Via MCP client
python scripts/mcp-client.py call --stdio "node mcp-servers/email-mcp/index.js" \
  --tool send_email \
  --params '{"to": "user@example.com", "subject": "Hello", "body": "Message content"}'
```

### Create Draft

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/email-mcp/index.js" \
  --tool create_draft \
  --params '{"to": "user@example.com", "subject": "Proposal", "body": "Draft content"}'
```

### Search Emails

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/email-mcp/index.js" \
  --tool search_emails \
  --params '{"query": "is:unread", "maxResults": 10}'
```

### Get Email Details

```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/email-mcp/index.js" \
  --tool get_email \
  --params '{"messageId": "abc123"}'
```

## Workflow: Reply to Email

1. Read email from Needs_Action folder
2. Draft reply using `create_draft` (safer) or `send_email` (direct)
3. For new contacts, create approval request first
4. Log action in processing notes

## Workflow: Send Notification

1. Determine recipients from Company Handbook
2. Check if approval is needed (new contacts, bulk emails)
3. Send via `send_email` or create approval request
4. Update Dashboard with results

## Human-in-the-Loop

**Require approval before sending:**
- Emails to new contacts (not in known clients list)
- Bulk emails (> 5 recipients)
- Emails with attachments
- Payment-related emails

**Can send directly:**
- Replies to known contacts
- Internal notifications
- Scheduled/automated responses

## Tool Reference

| Tool | Purpose | Approval Required |
|------|---------|-------------------|
| `send_email` | Send email immediately | For new contacts |
| `create_draft` | Create draft for review | Never |
| `search_emails` | Search Gmail | Never |
| `get_email` | Get email details | Never |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Run `python scripts/gmail_auth.py` |
| Token expired | Delete `token.pickle` and re-authenticate |
| MCP server not found | Check Node.js is installed, run `npm install` |
| Email not sent | Check Gmail API quotas and permissions |
