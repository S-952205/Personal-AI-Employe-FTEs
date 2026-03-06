# Personal AI Employee FTEs - Project Context

## Project Overview

This project is a **hackathon-style blueprint** for building autonomous "Digital FTEs" (Full-Time Equivalent AI employees). The core concept is creating AI agents that work 24/7 to manage personal and business affairs using **Claude Code** as the reasoning engine and **Obsidian** as the knowledge dashboard.

**Key Vision:** Transform AI from a chatbot into a proactive business partner that:
- Monitors communications (Gmail, WhatsApp, LinkedIn)
- Manages business tasks and accounting
- Generates "Monday Morning CEO Briefings" with revenue, bottlenecks, and proactive suggestions
- Operates autonomously with human-in-the-loop approval for sensitive actions

## Architecture

### Core Components

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine for multi-step task completion |
| **Memory/GUI** | Obsidian (Markdown vault) | Dashboard, long-term memory, task tracking |
| **Senses** | Python Watcher scripts | Monitor Gmail, WhatsApp, filesystems for triggers |
| **Hands** | MCP Servers | External actions (email, browser automation, payments) |
| **Persistence** | Ralph Wiggum Loop | Keep agent working until task completion |

### Folder Structure

```
Personal-AI-Employe-FTEs/
├── .qwen/skills/           # Reusable agent skill modules
│   └── browsing-with-playwright/
│       ├── SKILL.md          # Skill documentation & usage
│       ├── scripts/
│       │   ├── mcp-client.py # Universal MCP client (HTTP/stdio)
│       │   ├── start-server.sh
│       │   ├── stop-server.sh
│       │   └── verify.py
│       └── references/
│           └── playwright-tools.md
├── skills-lock.json          # Skill version tracking
└── QWEN.md                   # This file
```

### Skill System

The project uses a **skill-based architecture** where each skill is a self-contained module with:
- `SKILL.md` - Documentation with usage examples
- `scripts/` - Helper scripts for server lifecycle and tool invocation
- `references/` - Auto-generated tool documentation

**Current Skill:** `browsing-with-playwright` - Browser automation via Playwright MCP for web scraping, form filling, and UI testing.

## Key Concepts

### Watcher Pattern

Lightweight Python scripts that continuously monitor inputs and create actionable `.md` files in `/Needs_Action`:

```python
# All watchers follow this pattern
class BaseWatcher:
    def check_for_updates() -> list  # Return new items to process
    def create_action_file(item)     # Create .md in Needs_Action/
    def run()                        # Main loop with check_interval
```

### Human-in-the-Loop (HITL)

For sensitive actions (payments, sending emails), Claude writes an approval request file instead of acting directly:

```
/Pending_Approval/PAYMENT_Client_A.md → User moves to /Approved → MCP executes
```

### Ralph Wiggum Loop

A Stop hook pattern that keeps Claude Code working autonomously until tasks are complete:
1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task file in `/Done`?
5. If NO → Block exit, re-inject prompt (loop continues)

## Building & Running

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers |
| GitHub Desktop | Latest | Version control |

### Playwright MCP Skill Setup

```bash
# Start the browser automation server
bash .agents/skills/browsing-with-playwright/scripts/start-server.sh

# Verify it's running
python .agents/skills/browsing-with-playwright/scripts/verify.py

# Use the MCP client
python .agents/skills/browsing-with-playwright/scripts/mcp-client.py list -u http://localhost:8808

# Stop when done
bash .agents/skills/browsing-with-playwright/scripts/stop-server.sh
```

### MCP Client Usage

```bash
# List tools from HTTP server
python mcp-client.py list --url http://localhost:8808

# Call a tool
python mcp-client.py call --url http://localhost:8808 --tool browser_navigate \
  --params '{"url": "https://example.com"}'

# List tools from stdio server
python mcp-client.py list --stdio "npx -y @modelcontextprotocol/server-github"

# Emit tool schemas as markdown
python mcp-client.py emit --url http://localhost:8808
```

## Development Conventions

### Skill Structure

Each skill should follow this convention:
1. `SKILL.md` - Main documentation with:
   - Server lifecycle commands (start/stop)
   - Quick reference for common operations
   - Workflow examples
   - Troubleshooting table
2. `scripts/` - Executable helpers for common operations
3. `references/` - Auto-generated tool documentation (use `mcp-client.py emit`)

### File Naming

- Watcher scripts: `*_watcher.py` (e.g., `gmail_watcher.py`)
- Action files: `<TYPE>_<identifier>.md` (e.g., `EMAIL_abc123.md`)
- Approval files: `APPROVAL_<description>.md`

### Markdown Frontmatter

All actionable files use YAML frontmatter:

```yaml
---
type: email
from: user@example.com
subject: Urgent Meeting
priority: high
status: pending
---
```

## Hackathon Tiers

| Tier | Requirements | Estimated Time |
|------|--------------|----------------|
| **Bronze** | Obsidian vault, 1 watcher, basic folder structure | 8-12 hours |
| **Silver** | 2+ watchers, MCP server, HITL workflow, scheduling | 20-30 hours |
| **Gold** | Full integration, Odoo accounting, social media, audit logging | 40+ hours |
| **Platinum** | Cloud deployment, domain specialization, A2A upgrades | 60+ hours |

## Recommended MCP Servers

| Server | Capabilities | Use Case |
|--------|--------------|----------|
| `filesystem` | Read/write/list files | Built-in vault access |
| `email-mcp` | Send/draft/search emails | Gmail integration |
| `browser-mcp` | Navigate, click, fill forms | Payment portals, web automation |
| `calendar-mcp` | Create/update events | Scheduling |
| `@playwright/mcp` | Full browser automation | Web scraping, UI testing |

## Key Files Reference

| File | Purpose |
|------|---------|
| `Personal AI Employee Hackathon 0_...md` | Full architectural blueprint and hackathon guide |
| `skills-lock.json` | Tracks installed skills and versions |
| `.agents/skills/browsing-with-playwright/SKILL.md` | Browser automation skill documentation |
| `.agents/skills/browsing-with-playwright/scripts/mcp-client.py` | Universal MCP client (HTTP + stdio) |

## Common Workflows

### Browser Form Submission
1. Navigate to page (`browser_navigate`)
2. Get snapshot (`browser_snapshot`) to find element refs
3. Fill form fields (`browser_fill_form` or `browser_type`)
4. Click submit (`browser_click`)
5. Wait for confirmation (`browser_wait_for`)
6. Screenshot result (`browser_take_screenshot`)

### Data Extraction
1. Navigate to page
2. Get snapshot (contains text content with refs)
3. Use `browser_evaluate` for complex extraction
4. Process results

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright server not responding | Run `bash scripts/stop-server.sh && bash scripts/start-server.sh` |
| Element not found | Run `browser_snapshot` first to get current refs |
| Click fails | Try `browser_hover` first, then click |
| Form not submitting | Use `"submit": true` with `browser_type` |
| MCP client connection error | Check server is running: `pgrep -f "@playwright/mcp"` |

## Resources

- [Claude Code Documentation](https://claude.com/product/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
