# LinkedIn Automation - Silver Tier

## Quick Start Flow

### Step 1: Login to LinkedIn (One-time setup)

```bash
python scripts/linkedin_login.py
```

**What happens:**
1. Browser opens (visible mode)
2. Login to LinkedIn with your credentials
3. Wait until you see your feed
4. Session is saved automatically
5. Close browser

### Step 2: Post to LinkedIn

```bash
python scripts/linkedin_post.py
```

**What happens:**
1. Qwen AI generates a business post
2. Browser opens with your saved session
3. Post content is entered in LinkedIn editor
4. You review and click "Post" button
5. Result saved to `/Done/` folder

---

## File Overview

| File | Purpose |
|------|---------|
| `scripts/linkedin_login.py` | One-time LinkedIn login, saves session |
| `scripts/linkedin_post.py` | Generate post with Qwen AI and post to LinkedIn |
| `scripts/linkedin_watcher.py` | Monitors LinkedIn and creates action files |
| `mcp-servers/linkedin-mcp/index.js` | MCP server for LinkedIn operations |

---

## Workflow

```
┌─────────────────────┐
│  1. Login Script    │
│  (One-time setup)   │
└──────────┬──────────┘
           │
           ▼
  Session saved in linkedin_session/
           │
           ▼
┌─────────────────────┐
│  2. Post Script     │
│  (Run when posting) │
└──────────┬──────────┘
           │
           ▼
  Qwen AI generates content
           │
           ▼
  Browser opens (with saved session)
           │
           ▼
  Content entered in LinkedIn
           │
           ▼
  You review and click "Post"
           │
           ▼
  Result saved to /Done/
```

---

## Human-in-the-Loop (HITL)

All posts require **human review** before posting:

1. AI generates draft
2. You see the content in terminal
3. Browser opens with content pre-filled
4. **You click "Post" button** (manual approval)
5. This ensures no unwanted content is posted

---

## Session Management

### Session Location
```
C:\Projects\Personal-AI-Employe-FTEs\linkedin_session\
```

### If Session Expires
```bash
# Delete old session
rmdir /s linkedin_session

# Login again
python scripts/linkedin_login.py
```

---

## Using with Qwen Code

To integrate with Qwen Code for automated posting:

1. Start LinkedIn MCP server:
```bash
cd mcp-servers/linkedin-mcp
npm start
```

2. Call from Qwen Code:
```bash
python scripts/mcp-client.py call --stdio "node mcp-servers/linkedin-mcp/index.js" \
  --tool create_post \
  --params '{"content": "Your post content", "hashtags": ["AI", "Business"]}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not logged in" error | Run `python scripts/linkedin_login.py` again |
| Browser closes immediately | Check if session folder exists and has files |
| Post button not found | LinkedIn UI may have changed, update selectors in `linkedin_post.py` |
| Google login blocked | Use regular Chrome for login, script uses saved cookies |

---

## Terms of Service Notice

⚠️ **Use responsibly:**
- This tool is for personal/educational use
- Be aware of LinkedIn's Terms of Service
- Don't spam or post excessive content
- Maintain human oversight (HITL) for all posts
- Monitor your account for any warnings

---

## Silver Tier Compliance

✅ **Requirement:** "Automatically Post on LinkedIn about business to generate sales"

**Implementation:**
- ✅ Qwen AI generates business posts
- ✅ Browser automation posts to LinkedIn
- ✅ Human-in-the-loop approval
- ✅ Session persistence
- ✅ Audit logging in `/Done/` folder
