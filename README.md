# Personal AI Employee FTE - Bronze Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This is a **Bronze Tier** implementation of a Personal AI Employee - an autonomous agent that works 24/7 to manage your personal and business affairs using **Claude Code** as the reasoning engine and **Obsidian** as the knowledge dashboard.

---

## 🎯 Bronze Tier Deliverables

- ✅ Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- ✅ One working Watcher script (File System monitoring)
- ✅ Claude Code integration for reading/writing to the vault
- ✅ Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- ✅ All AI functionality implemented as Agent Skills

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
│   ├── Accounting/
│   ├── Briefings/
│   └── Pending_Approval/
│
├── scripts/                # 🔧 Python scripts (don't open in Obsidian)
│   ├── filesystem_watcher.py
│   ├── orchestrator.py
│   └── test_bronze.py
├── logs/                   # 📝 System logs
├── requirements.txt
└── README.md
```

**📖 Open `personal-ai-employee/` folder in Obsidian** - This dedicated vault contains only the Markdown files and working folders you need to interact with.

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Active subscription | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers (future) |

### Installation

1. **Clone or download this repository**

   ```bash
   cd Personal-AI-Employe-FTEs
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Claude Code is installed**

   ```bash
   claude --version
   ```

4. **Create logs directory**

   ```bash
   mkdir logs
   ```

---

## 📖 Usage

### Step 1: Start the File System Watcher

The watcher monitors the `/Inbox` folder for new files:

```bash
python scripts/filesystem_watcher.py
```

**What it does:**
- Watches `/Inbox` for new files
- Creates action files in `/Needs_Action` with metadata
- Logs all activity to `logs/filesystem_watcher.log`

### Step 2: Start the Orchestrator

In a **separate terminal**, start the orchestrator:

```bash
python scripts/orchestrator.py
```

**What it does:**
- Monitors `/Needs_Action` for pending items
- Creates processing plans in `/Plans`
- Triggers Claude Code to process items
- Updates `Dashboard.md` with status
- Processes approved items from `/Approved`

### Step 3: Test the System

1. **Drop a file in the Inbox**
   
   Create a test file:
   ```bash
   echo "Test content" > Inbox/test_file.txt
   ```

2. **Watch the magic happen:**
   - File System Watcher detects the new file
   - Creates `FILE_*.md` in `/Needs_Action`
   - Orchestrator picks it up and creates a plan
   - Claude Code processes the item
   - Item moves to `/Done` when complete

### Step 4: Open in Obsidian

Open the `personal-ai-employee` folder in Obsidian:

```bash
obsidian personal-ai-employee
```

Or manually:
1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to `Personal-AI-Employe-FTEs/personal-ai-employee`
4. Click "Open"

This vault contains only the Markdown files and working folders - no code files cluttering your view!

---

## 🎬 How It Works

### Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   File Drop     │ ──▶ │   File System   │ ──▶ │  Needs_Action   │
│   (Inbox)       │     │    Watcher      │     │   (Action Files)│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Done          │ ◀── │   Claude Code   │ ◀── │   Orchestrator  │
│   (Completed)   │     │   (Processing)  │     │   (Triggers)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Processing Flow

1. **Input:** File dropped in `/Inbox`
2. **Detection:** Watcher creates action file in `/Needs_Action`
3. **Planning:** Orchestrator creates plan in `/Plans`
4. **Processing:** Claude Code reads plan + handbook + business goals
5. **Action:** Claude processes item according to rules
6. **Output:** Item moved to `/Done` with processing notes

---

## 📋 Configuration

### Company Handbook

Edit `Company_Handbook.md` to customize:

- Communication rules (email, WhatsApp, social media)
- Financial rules (payment thresholds, invoicing)
- Task priority classifications
- Subscription management rules
- VIP contacts and known clients

### Business Goals

Edit `Business_Goals.md` to set:

- Revenue targets
- Key metrics and alert thresholds
- Active projects
- Subscription patterns to detect

### Dashboard

The `Dashboard.md` is auto-updated by the orchestrator. Manual edits are preserved.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Watcher not detecting files | Ensure `logs/` directory exists |
| Claude Code not found | Add to PATH: `export PATH="$PATH:$(which claude)"` |
| Orchestrator not triggering Claude | Check Claude subscription is active |
| Files not moving to Done | Check file permissions |

### View Logs

```bash
# Watch watcher logs
tail -f logs/filesystem_watcher.log

# Watch orchestrator logs
tail -f logs/orchestrator.log
```

---

## 🛡️ Security Notes

- **Never commit credentials** - Use environment variables
- **Review before approving** - Check `/Pending_Approval` before moving to `/Approved`
- **Audit trail** - All actions are logged in `/Logs`
- **Local-first** - All data stays in your Obsidian vault

---

## 📈 Next Steps (Silver Tier)

To upgrade to Silver Tier, add:

1. **Gmail Watcher** - Monitor Gmail for urgent emails
2. **WhatsApp Watcher** - Monitor WhatsApp for keywords
3. **MCP Server** - Send emails automatically
4. **HITL Workflow** - Human-in-the-loop approval for sensitive actions
5. **Scheduling** - Cron/Task Scheduler for automated runs

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
- [Obsidian Help](https://help.obsidian.md/)
- [Watchdog Documentation](https://pypi.org/project/watchdog/)

---

*Built with ❤️ for the Personal AI Employee Hackathon 2026*
