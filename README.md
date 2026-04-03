# Personal AI Employee FTE - Silver Tier ✅

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

A **production-ready Silver Tier** implementation of a Personal AI Employee - an autonomous agent that works 24/7 to manage your personal and business affairs using **Qwen Code** as the reasoning engine and **Obsidian** as the knowledge dashboard.

**Last Updated:** 2026-04-04 | **Status:** Fully Operational | **Tier Compliance:** Silver ✅ 100% | **Audit Logging:** Gold Compliant ✅

---

## 🎯 What You Get

### ✅ Silver Tier - Complete & Verified (100% Compliant)

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | **File System Watcher** | ✅ | Monitors `/Inbox` for new files (instant detection via watchdog) |
| 2 | **Gmail Watcher** | ✅ | Monitors Gmail for unread emails (every 2 min, OAuth2) |
| 3 | **LinkedIn Watcher** | ✅ | Monitors LinkedIn notifications (every 5 min, creates action files) |
| 4 | **LinkedIn Auto-Posting** | ✅ | `linkedin_post.py --auto` for autonomous posting with duplicate detection |
| 5 | **Email MCP Server** | ✅ | Send/draft emails via Gmail API (4 tools) |
| 6 | **LinkedIn MCP Server** | ✅ | Post updates, send messages, connect (5 tools) |
| 7 | **HITL Workflow** | ✅ | Full approval system for sensitive actions |
| 8 | **PM2 Background** | ✅ | 24/7 background processes with auto-restart |
| 9 | **Task Scheduler** | ✅ | Windows auto-start on boot |
| 10 | **Agent Skills** | ✅ | 4 reusable skills (browsing, email, linkedin, HITL) |
| 11 | **Audit Logging** | ✅ | Gold-tier JSON logging with 90-day retention |

---

## 🚀 Quick Start (5 Minutes)

### **Prerequisites**

| Software | Version | Purpose | Required |
|----------|---------|---------|----------|
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts | ✅ Yes |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers, PM2 | ✅ Yes |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge dashboard | ✅ Yes |
| [Qwen Code](https://claude.com/product/claude-code) | Active | AI reasoning engine | ⏳ Optional* |

*Qwen Code is used for AI processing. System works without it for basic monitoring.

### **Step 1: Install Dependencies**

```bash
cd C:\Projects\Personal-AI-Employe-FTEs

# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (MCP servers)
cd mcp-servers\email-mcp && npm install
cd ..\linkedin-mcp && npm install
cd ..\..

# Playwright browsers (for LinkedIn)
playwright install
```

### **Step 2: Start with PM2 (Recommended)**

```bash
# Install PM2 globally
npm install -g pm2

# Start all AI Employee processes
pm2 start ecosystem.config.cjs

# Save process list (auto-restart on reboot)
pm2 save

# Check status
pm2 status
```

**Expected Output:**
```
┌────┬────────────────────┬──────────┬──────┬───────────┬──────────┬──────────┐
│ id │ name               │ mode     │ ↺    │ status    │ cpu      │ memory   │
├────┼────────────────────┼──────────┼──────┼───────────┼──────────┼──────────┤
│ 0  │ gmail-watcher      │ fork     │ 0    │ online    │ 0%       │ 50mb     │
│ 1  │ linkedin-watcher   │ fork     │ 0    │ online    │ 0%       │ 30mb     │
│ 2  │ filesystem-watcher │ fork     │ 0    │ online    │ 0%       │ 20mb     │
│ 3  │ orchestrator       │ fork     │ 0    │ online    │ 0%       │ 40mb     │
└────┴────────────────────┴──────────┴──────┴───────────┴──────────┴──────────┘
```

✅ **Done! Your AI Employee is now working 24/7 in the background.**

---

## 📖 Essential Commands

### **Daily Management**

```bash
# Check if running
pm2 status

# View live logs
pm2 logs

# View specific process logs
pm2 logs gmail-watcher
pm2 logs orchestrator

# Restart everything
pm2 restart all

# Stop everything
pm2 stop all

# Start everything
pm2 start all
```

### **Manual Scripts (Alternative to PM2)**

```bash
# Start all watchers (opens 3 terminal windows)
scripts\start-all.bat

# Individual watchers
python scripts\filesystem_watcher.py
python scripts\gmail_watcher.py    # Requires credentials
python scripts\linkedin_watcher.py
python scripts\orchestrator.py
```

---

## 📁 Project Structure

```
Personal-AI-Employe-FTEs/
│
├── personal-ai-employee/       # 📖 Open THIS in Obsidian
│   ├── Dashboard.md            # Real-time status dashboard
│   ├── Company_Handbook.md     # Rules & guidelines
│   ├── Business_Goals.md       # Your business objectives
│   ├── Inbox/                  # Drop files here
│   ├── Needs_Action/           # Items awaiting processing
│   ├── Pending_Approval/       # Awaiting your approval
│   ├── Approved/               # Approved, ready to execute
│   ├── Rejected/               # Rejected items
│   ├── Done/                   # Completed items
│   ├── Plans/                  # AI-generated plans
│   ├── In_Progress/            # Currently processing
│   ├── Accounting/             # Financial records
│   └── Briefings/              # CEO briefings
│
├── scripts/                    # 🔧 Python Scripts
│   ├── filesystem_watcher.py   # Monitors Inbox folder
│   ├── gmail_watcher.py        # Monitors Gmail
│   ├── linkedin_watcher.py     # Monitors LinkedIn (creates action files)
│   ├── linkedin_post.py        # LinkedIn auto-posting (--auto mode)
│   ├── linkedin_login.py       # LinkedIn session setup
│   ├── orchestrator.py         # Main coordinator (HITL workflow)
│   ├── qwen_email_processor.py # AI email processing
│   ├── gmail_auth.py           # Gmail OAuth setup
│   ├── audit_logger.py         # Gold-tier audit logging
│   ├── setup-pm2.bat           # PM2 setup script
│   ├── setup-tasks.bat         # Task Scheduler setup
│   ├── pm2-manage.bat          # PM2 management helper
│   └── start-all.bat           # Start all watchers
│
├── mcp-servers/                # 🤖 MCP Servers
│   ├── email-mcp/              # Gmail operations
│   │   ├── index.js
│   │   └── package.json
│   └── linkedin-mcp/           # LinkedIn operations
│       ├── index.js
│       └── package.json
│
├── .qwen/skills/               # 🧠 Qwen Agent Skills
│   ├── browsing-with-playwright
│   ├── email-operations
│   ├── linkedin-operations
│   └── hitl-approval
│
├── logs/                       # 📝 System logs
├── ecosystem.config.cjs        # PM2 configuration
├── requirements.txt            # Python dependencies
├── mcp-config.json             # MCP server config
└── skills-lock.json            # Skill version tracking
```

**📖 Open `personal-ai-employee/` folder in Obsidian** for your knowledge dashboard.

---

## 🤖 MCP Servers

### Email MCP Server (`mcp-servers/email-mcp/`)

| Tool | Description |
|------|-------------|
| `send_email` | Send emails via Gmail API |
| `create_draft` | Create email drafts for review |
| `search_emails` | Search Gmail with queries |
| `get_email` | Retrieve email details |

### LinkedIn MCP Server (`mcp-servers/linkedin-mcp/`)

| Tool | Description |
|------|-------------|
| `create_post` | Create LinkedIn posts |
| `comment_on_post` | Comment on LinkedIn posts |
| `connect_with_person` | Send connection requests |
| `send_message` | Send direct messages |
| `get_notifications` | Get LinkedIn notifications |

---

## 🚀 LinkedIn Auto-Posting

### **Overview**

The LinkedIn auto-posting system allows autonomous posting with proper error handling, duplicate detection, and audience selection.

### **Usage**

```bash
# Auto mode (no confirmation required)
python scripts/linkedin_post.py --auto

# Interactive mode (asks for confirmation)
python scripts/linkedin_post.py
```

### **Features**

| Feature | Description |
|---------|-------------|
| **Auto Mode** | `--auto` flag skips confirmation prompt |
| **Duplicate Detection** | Adds timestamp and unique ID to avoid LinkedIn's duplicate filter |
| **Session Persistence** | Uses Playwright persistent session (login once) |
| **Error Recovery** | 4 fallback strategies for audience dialog |
| **Verification** | Takes screenshot and verifies post appeared on feed |
| **Draft Saving** | Saves post draft to `/Plans/` folder before posting |

### **First-Time Setup**

```bash
# 1. Login to LinkedIn (saves session)
python scripts/linkedin_login.py

# 2. Test auto-posting
python scripts/linkedin_post.py --auto
```

### **How It Works**

1. Opens browser with saved LinkedIn session
2. Navigates to LinkedIn feed
3. Opens post creation dialog
4. Enters content with unique timestamp/ID
5. Handles audience selection ("Anyone", "Connections", etc.)
6. Clicks Post button with proper waiting
7. Verifies post submission
8. Saves result to `/Done/` folder

---

## 🧠 Agent Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| **Browsing with Playwright** | `.qwen/skills/browsing-with-playwright/` | Browser automation, form filling, data extraction |
| **Email Operations** | `.qwen/skills/email-operations/SKILL.md` | Email sending, drafting, searching via Gmail MCP |
| **LinkedIn Operations** | `.qwen/skills/linkedin-operations/SKILL.md` | LinkedIn posting, messaging, connections |
| **HITL Approval** | `.qwen/skills/hitl-approval/SKILL.md` | Human-in-the-Loop approval workflow management |

---

## 🎬 How It Works

### **Architecture Overview**

```
┌─────────────────┐     ┌─────────────────┐
│   Gmail         │────▶│   Gmail         │
│   (External)    │     │   Watcher       │  ✅ Running
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│   LinkedIn      │────▶│   LinkedIn      │
│   (External)    │     │   Watcher       │  ✅ Running
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│   File Drop     │────▶│   File System   │
│   (Inbox)       │     │   Watcher       │  ✅ Running
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Needs_Action         │
                    │    (Action Files)       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Orchestrator         │
                    │    (Processes 30s)      │  ✅ Running
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Qwen Code AI         │
                    │    (Processing)         │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌────────▼────────┐
│   Pending         │  │   Approved        │  │   Done          │
│   Approval        │  │   (Execute)       │  │   (Complete)    │
└───────────────────┘  └───────────────────┘  └─────────────────┘
```

### **Processing Flow**

1. **Input Detection** (Watchers)
   - Gmail: New unread email
   - LinkedIn: New notification/message
   - File System: File dropped in `/Inbox`

2. **Action File Creation**
   - Creates `EMAIL_*.md`, `LINKEDIN_*.md`, or `FILE_*.md`
   - Saved in `/Needs_Action/` folder

3. **AI Processing** (Orchestrator + Qwen)
   - Runs every 30 seconds
   - Reads action files
   - Applies Company Handbook rules
   - Classifies and drafts responses

4. **Human-in-the-Loop Decision**
   - **Normal actions**: Auto-process
   - **Sensitive actions**: Create approval request in `/Pending_Approval/`

5. **Human Review** (You)
   - Review `/Pending_Approval/` files
   - **Approve**: Move to `/Approved/` → Auto-executes
   - **Reject**: Move to `/Rejected/` → Add reason

6. **Execution & Logging**
   - Execute approved actions via MCP servers
   - Move completed items to `/Done/`
   - Full audit trail maintained

---

## 🛡️ Human-in-the-Loop (HITL) Workflow

### **When Approval is Required**

Per `Company_Handbook.md`:

| Action Type | Approval Required? |
|-------------|-------------------|
| Email responses | ✅ Always |
| LinkedIn posts | ✅ Always (draft only) |
| Payments > $50 | ✅ Always |
| Connection requests to VIPs | ✅ Always |
| Subscription cancellations | ✅ Always |
| Promotional emails | ❌ No (auto-archive) |

### **Approval Process**

1. **AI creates approval request:**
   ```
   /Pending_Approval/APPROVAL_email_20260327_210000.md
   ```

2. **You review** (in Obsidian or file explorer)

3. **You decide:**
   - ✅ **Approve:** Move to `/Approved/` → Auto-executes within 30 seconds
   - ❌ **Reject:** Move to `/Rejected/` → Add reason
   - ✏️ **Modify:** Edit draft → Move to `/Approved/`

---

## 🔧 Optional Setup

### **Gmail Integration** (Optional)

#### Step 1: Get Gmail Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID credentials
3. Download `credentials.json`
4. Place in project root: `C:\Projects\Personal-AI-Employe-FTEs\credentials.json`

#### Step 2: Authenticate

```bash
python scripts\gmail_auth.py
```

Follow prompts to authorize. Token saved to `token.pickle`.

#### Step 3: Restart Gmail Watcher

```bash
pm2 restart gmail-watcher
```

---

### **LinkedIn Integration** (Optional)

#### First Run Setup

```bash
python scripts\linkedin_login.py
```

1. Browser opens
2. Log in to LinkedIn manually
3. Session saved to `linkedin_session/`
4. Close browser

#### Start LinkedIn Watcher

```bash
pm2 restart linkedin-watcher
```

#### Auto-Post to LinkedIn

```bash
# Autonomous posting (no confirmation)
python scripts\linkedin_post.py --auto

# Interactive posting (asks first)
python scripts\linkedin_post.py
```

**⚠️ Note:** Be aware of LinkedIn's Terms of Service. Use responsibly.

---

### **Windows Task Scheduler** (Optional - Auto-Start on Boot)

**Alternative to PM2.** Run as Administrator:

```batch
cd C:\Projects\Personal-AI-Employe-FTEs
scripts\setup-tasks.bat
```

Creates 3 scheduled tasks:
- `AI_Employee_Gmail_Watcher`
- `AI_Employee_LinkedIn_Watcher`
- `AI_Employee_Orchestrator`

**⚠️ Important:** Use **either PM2 OR Task Scheduler, not both** (creates conflicts).

---

## 📋 Configuration

### **Company Handbook** (`Company_Handbook.md`)

Customize rules for:
- Communication guidelines (email, LinkedIn)
- Financial thresholds (payment approvals)
- Task priority classifications
- VIP contacts and known clients
- Subscription audit rules

### **Business Goals** (`Business_Goals.md`)

Set your:
- Revenue targets
- Key metrics and alert thresholds
- Active projects and deadlines
- Subscription patterns to detect

### **MCP Configuration** (`mcp-config.json`)

Configure MCP servers:

```json
{
  "servers": {
    "email": {
      "command": "node",
      "args": ["mcp-servers/email-mcp/index.js"],
      "disabled": false
    },
    "linkedin": {
      "command": "node",
      "args": ["mcp-servers/linkedin-mcp/index.js"],
      "disabled": false
    }
  },
  "settings": {
    "email": {
      "require_approval_for_send": true,
      "require_approval_for_new_contacts": true
    },
    "linkedin": {
      "require_approval_for_posts": true,
      "require_approval_for_connection_requests": true
    }
  }
}
```

---

## 🔍 Daily Usage

### **Morning Check (30 seconds)**

```bash
# 1. Check status
pm2 status

# 2. Check for approvals
dir personal-ai-employee\Pending_Approval

# 3. Quick log review
pm2 logs --lines 20
```

### **Evening Check (1 minute)**

```bash
# Check what was processed today
dir personal-ai-employee\Done
```

### **Test the System**

Drop a test file:
1. Create text file: `personal-ai-employee\Inbox\test.txt`
2. Wait 10 seconds
3. Check logs: `pm2 logs filesystem-watcher`
4. Should see: "New file detected: test.txt"

---

## 🔧 Troubleshooting

### **PM2 Issues**

| Problem | Solution |
|---------|----------|
| Processes show "errored" | `pm2 restart all` |
| Can't find PM2 | `npm install -g pm2` |
| Want to view errors | `pm2 logs --err` |
| Need fresh start | `pm2 delete all && pm2 start ecosystem.config.cjs` |

### **Gmail Watcher Issues**

| Problem | Solution |
|---------|----------|
| `credentials.json` not found | Download from Google Cloud Console |
| Authentication failed | Run `python scripts\gmail_auth.py` |
| No emails detected | Check if emails are unread |
| Duplicate detection | Check `.gmail_processed_ids.json` exists |

### **LinkedIn Watcher Issues**

| Problem | Solution |
|---------|----------|
| Not logged in | Run `python scripts\linkedin_login.py` |
| Session expired | Delete `linkedin_session/` and re-login |
| Element not found | LinkedIn UI changed - update selectors |

### **Orchestrator Issues**

| Problem | Solution |
|---------|----------|
| Not processing | Check logs: `pm2 logs orchestrator` |
| Duplicate approvals | Already fixed! Restart orchestrator |
| Files not moving | Check folder permissions |

---

## 📚 Documentation

All task-specific and historical documentation is organized in the `docs/` folder:

### 📖 Quick Reference (Root Level)

| File | Purpose |
|------|---------|
| **`README.md`** | This file - Project overview and quick start |
| **`Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`** | Full architectural blueprint and hackathon guide |

### 📂 Detailed Documentation (`docs/` folder)

| Category | Files | Description |
|----------|-------|-------------|
| **Guides** | `docs/guides/` | Setup, usage, and troubleshooting guides |
| **Fixes** | `docs/fixes/` | Bug fixes, patches, and testing guides |
| **Setup** | `docs/setup/` | Setup completion reports and compliance checklists |
| **Architecture** | `docs/architecture/` | Codebase analysis and architectural decisions |

**See [docs/README.md](docs/README.md) for complete documentation index.**

---

## 🏆 Tier Compliance Summary

### Silver Tier Requirements (100% Complete)

| # | Requirement | Implementation | Verified |
|---|-------------|----------------|----------|
| 1 | **2+ Watcher Scripts** | Gmail, LinkedIn, FileSystem watchers | ✅ |
| 2 | **Auto Post on LinkedIn** | Watcher → Qwen → Approval → LinkedIn MCP | ✅ |
| 3 | **Plan.md Creation** | Orchestrator creates PLAN_*.md files | ✅ |
| 4 | **Working MCP Server** | Email MCP (4 tools) + LinkedIn MCP (5 tools) | ✅ |
| 5 | **HITL Workflow** | Pending_Approval → Approved → Execute | ✅ |
| 6 | **Scheduling** | PM2 + Windows Task Scheduler | ✅ |
| 7 | **Agent Skills** | 4 skills (browsing, email, linkedin, HITL) | ✅ |

---

## 📝 License

This project is part of the Personal AI Employee Hackathon. Feel free to use, modify, and share.

---

## 🤝 Contributing

Join the Wednesday Research Meeting:
- **When:** Wednesdays at 10:00 PM PKT
- **Zoom:** [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **YouTube:** [@panaversity](https://www.youtube.com/@panaversity)

---

## 📞 Support Resources

- [Qwen Code Documentation](https://claude.com/product/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Gmail API](https://developers.google.com/gmail/api)
- [Playwright Documentation](https://playwright.dev/)
- [PM2 Documentation](https://pm2.keymetrics.io/)
- [Obsidian Help](https://help.obsidian.md/)

---

**Last Updated:** 2026-04-04
**Version:** Silver Tier v1.1 (Production Ready ✅)
**Status:** Fully Operational - 4 PM2 processes running 24/7
**Audit Logging:** Gold Tier Compliant ✅
**LinkedIn Auto-Posting:** Production Ready with --auto flag ✅

*Built with ❤️ for the Personal AI Employee Hackathon 2026*
