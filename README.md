# Personal AI Employee FTE - Silver Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This is a **Silver Tier** implementation of a Personal AI Employee - an autonomous agent that works 24/7 to manage your personal and business affairs using **Claude Code** as the reasoning engine and **Obsidian** as the knowledge dashboard.

---

## 🎯 Silver Tier Deliverables

- ✅ All Bronze requirements plus:
- ✅ Gmail Watcher - Monitor Gmail for urgent emails
- ✅ LinkedIn Watcher - Monitor LinkedIn for messages, notifications, connections
- ✅ Email MCP Server - Send and draft emails via Gmail API
- ✅ LinkedIn MCP Server - Post updates, send messages, connect with people
- ✅ Human-in-the-Loop (HITL) approval workflow for sensitive actions
- ✅ Windows Task Scheduler integration for automated startup
- ✅ Enhanced Orchestrator with multi-watcher support

---

## 📁 Project Structure

```
Personal-AI-Employe-FTEs/
├── personal-ai-employee/   # 📖 Open THIS folder in Obsidian
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Business_Goals.md
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Done/
│   ├── Plans/
│   ├── Approved/
│   ├── Rejected/
│   ├── Pending_Approval/
│   ├── In_Progress/
│   ├── Accounting/
│   └── Briefings/
│
├── scripts/                # 🔧 Python scripts
│   ├── filesystem_watcher.py
│   ├── gmail_watcher.py       # NEW: Silver Tier
│   ├── linkedin_watcher.py    # NEW: Silver Tier
│   ├── orchestrator.py
│   ├── gmail_auth.py          # NEW: Gmail authentication
│   ├── start-all.bat          # NEW: Start all watchers
│   ├── setup-tasks.bat        # NEW: Windows Task Scheduler setup
│   ├── test_silver.py         # NEW: Silver tier verification
│   └── test_bronze.py
│
├── mcp-servers/              # 🤖 MCP Servers (NEW: Silver Tier)
│   ├── email-mcp/
│   │   ├── package.json
│   │   └── index.js
│   └── linkedin-mcp/
│       ├── package.json
│       └── index.js
│
├── logs/                     # 📝 System logs
├── requirements.txt
├── mcp-config.json           # NEW: MCP configuration
└── README.md
```

**📖 Open `personal-ai-employee/` folder in Obsidian** - This dedicated vault contains only the Markdown files and working folders.

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Active subscription | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers |

### Installation

#### Step 1: Install Python Dependencies

```bash
cd Personal-AI-Employe-FTEs
pip install -r requirements.txt
```

#### Step 2: Install Node.js Dependencies (for MCP servers)

```bash
# Email MCP Server
cd mcp-servers/email-mcp
npm install

# LinkedIn MCP Server
cd ../linkedin-mcp
npm install
```

#### Step 3: Install Playwright Browsers

```bash
playwright install
```

#### Step 4: Verify Installation

```bash
python scripts/test_silver.py
```

This will check all components and report any missing dependencies.

---

## 📖 Usage

### Option 1: Manual Start (Recommended for Testing)

Start all watchers and orchestrator:

```bash
scripts/start-all.bat
```

This opens three terminal windows:
- **Gmail Watcher** - Checks every 2 minutes
- **LinkedIn Watcher** - Checks every 5 minutes  
- **Orchestrator** - Processes every 30 seconds

### Option 2: Windows Task Scheduler (Auto-start on Boot)

Run as Administrator:

```bash
scripts/setup-tasks.bat
```

This creates scheduled tasks that start automatically when Windows boots.

### Option 3: Individual Watchers

Start specific watchers:

```bash
# File System Watcher only
python scripts/filesystem_watcher.py

# Gmail Watcher only (requires credentials)
python scripts/gmail_watcher.py

# LinkedIn Watcher only
python scripts/linkedin_watcher.py

# Orchestrator only
python scripts/orchestrator.py
```

---

## 🔧 Gmail Setup (Optional)

To enable Gmail monitoring:

### Step 1: Get Gmail Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create or select a project
3. Enable Gmail API
4. Create OAuth 2.0 Client ID credentials
5. Download the `credentials.json` file
6. Place it in the project root: `Personal-AI-Employe-FTEs/credentials.json`

### Step 2: Authenticate

```bash
python scripts/gmail_auth.py
```

Follow the prompts to authorize. A `token.pickle` file will be created for future use.

### Step 3: Start Gmail Watcher

```bash
python scripts/gmail_watcher.py
```

---

## 🔗 LinkedIn Setup (Optional)

LinkedIn watcher uses browser automation with persistent sessions.

### First Run Setup

1. Start the LinkedIn watcher:
   ```bash
   python scripts/linkedin_watcher.py
   ```

2. On first run, manually log in to LinkedIn in the browser window that opens

3. The session is saved to `linkedin_session/` folder for future runs

### Notes

- ⚠️ **Be aware of LinkedIn's Terms of Service** - Use responsibly
- ⚠️ The watcher runs in headless mode by default
- ⚠️ Session cookies are stored locally for persistent login

---

## 🎬 How It Works

### Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│   Gmail         │────▶│   Gmail         │
│   (External)    │     │   Watcher       │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│   LinkedIn      │────▶│   LinkedIn      │
│   (External)    │     │   Watcher       │
└─────────────────┘     └────────┬────────┘
                                 │
┌─────────────────┐     ┌────────▼────────┐
│   File Drop     │────▶│   File System   │
│   (Inbox)       │     │   Watcher       │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Needs_Action         │
                    │    (Action Files)       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Orchestrator         │
                    │    (Creates Plans)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Claude Code          │
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

### Processing Flow

1. **Input Sources:**
   - File dropped in `/Inbox`
   - New Gmail received
   - LinkedIn notification/message

2. **Detection:** Watchers create action files in `/Needs_Action`

3. **Planning:** Orchestrator creates plan in `/Plans`

4. **Processing:** Claude Code reads plan + handbook + business goals

5. **HITL Decision:**
   - Normal action → Execute directly
   - Sensitive action → Create approval request in `/Pending_Approval/`

6. **Human Approval:**
   - User reviews `/Pending_Approval/` files
   - Move to `/Approved/` to execute
   - Move to `/Rejected/` to discard

7. **Output:** Item moved to `/Done` with processing notes

---

## 🛡️ Human-in-the-Loop (HITL) Workflow

### When Approval is Required

Per `Company_Handbook.md`, approval is required for:

| Action Type | Threshold |
|-------------|-----------|
| Payments | > $50 |
| Emails to new contacts | Always |
| LinkedIn posts | Always (draft only) |
| Connection requests to VIPs | Always |
| Subscription cancellations | Always |

### Approval Process

1. **Claude creates approval request:**
   ```
   /Pending_Approval/APPROVAL_email_20260310_143022.md
   ```

2. **User reviews the file** (in Obsidian or file explorer)

3. **User decides:**
   - ✅ **Approve:** Move to `/Approved/` → Auto-executes
   - ❌ **Reject:** Move to `/Rejected/` → Add reason
   - ✏️ **Modify:** Edit file → Move to `/Approved/`

---

## 📋 Configuration

### Company Handbook

Edit `Company_Handbook.md` to customize:

- Communication rules (email, LinkedIn)
- Financial rules (payment thresholds, invoicing)
- Task priority classifications
- VIP contacts and known clients

### Business Goals

Edit `Business_Goals.md` to set:

- Revenue targets
- Key metrics and alert thresholds
- Active projects
- Subscription patterns to detect

### MCP Configuration

Edit `mcp-config.json` to configure MCP servers:

```json
{
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

## 🔧 Troubleshooting

### Gmail Watcher Issues

| Issue | Solution |
|-------|----------|
| credentials.json not found | Download from Google Cloud Console |
| Authentication failed | Run `python scripts/gmail_auth.py` |
| No new emails detected | Check Gmail API scopes in auth |

### LinkedIn Watcher Issues

| Issue | Solution |
|-------|----------|
| Not logged in | Manually log in on first run |
| Session expired | Delete `linkedin_session/` and re-authenticate |
| Element not found | LinkedIn may have changed UI - update selectors |

### Orchestrator Issues

| Issue | Solution |
|-------|----------|
| Claude Code not found | Add to PATH or check subscription |
| Files not moving to Done | Check file permissions |
| Approval not triggering | Check `/Pending_Approval/` folder |

### View Logs

```bash
# Watch all logs
cd logs

# Gmail watcher
type gmail_watcher.log

# LinkedIn watcher
type linkedin_watcher.log

# Orchestrator
type orchestrator.log
```

---

## 📈 Silver Tier Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| File System Watcher | ✅ | Monitors `/Inbox` for new files |
| Gmail Watcher | ✅ | Monitors Gmail for unread emails |
| LinkedIn Watcher | ✅ | Monitors LinkedIn notifications/messages |
| Email MCP Server | ✅ | Send/draft emails via Gmail API |
| LinkedIn MCP Server | ✅ | Post updates, send messages, connect |
| HITL Workflow | ✅ | Approval system for sensitive actions |
| Windows Scheduler | ✅ | Auto-start on boot |
| Ralph Wiggum Loop | ✅ | Autonomous multi-step processing |

---

## 🚀 Next Steps (Gold Tier)

To upgrade to Gold Tier, add:

1. **Odoo Accounting Integration** - Self-hosted accounting via MCP
2. **Facebook/Instagram Integration** - Social media posting
3. **Twitter (X) Integration** - Tweet scheduling
4. **Weekly CEO Briefing** - Automated business audit
5. **Cloud Deployment** - 24/7 always-on operation
6. **Multi-Agent A2A** - Agent-to-agent communication

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

## 📚 Resources

- [Claude Code Documentation](https://claude.com/product/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Gmail API](https://developers.google.com/gmail/api)
- [Playwright Documentation](https://playwright.dev/)
- [Obsidian Help](https://help.obsidian.md/)

---

*Built with ❤️ for the Personal AI Employee Hackathon 2026*
