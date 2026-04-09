# Gold Tier Architecture - Personal AI Employee FTE

**Last Updated:** 2026-04-05  
**Version:** 1.0.0 (Gold)

---

## 📐 System Architecture

### Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PERSONAL AI EMPLOYEE - GOLD TIER                 │
│                          SYSTEM ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SOURCES                                │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Gmail   │ LinkedIn │ Facebook │ Twitter  │  Odoo    │  File System    │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬────────────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PERCEPTION LAYER (Watchers)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Gmail   │ │ LinkedIn │ │ Facebook │ │ Twitter  │ │   File   │      │
│  │ Watcher  │ │ Watcher  │ │ Watcher  │ │ Watcher  │ │ Watcher  │      │
│  │(Python)  │ │(Python)  │ │(Python)  │ │(Python)  │ │(watchdog)│      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         OBSIDIAN VAULT (Local Memory)                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ /Needs_Action/  │ /Plans/  │ /Done/  │ /Briefings/  │ /Logs/    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Dashboard.md (Gold) │ Company_Handbook.md │ Business_Goals.md   │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ /Pending_Approval/ │ /Approved/ │ /Rejected/ │ /Accounting/     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CROSS-DOMAIN INTEGRATION                        │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ Domain         │  │ Approval         │  │ Cross-Domain           │  │
│  │ Classifier     │  │ Threshold Mgr    │  │ Trigger Detector       │  │
│  │                │  │                  │  │                        │  │
│  │ Personal vs    │  │ Per-domain       │  │ Gmail → Business       │  │
│  │ Business       │  │ approval rules   │  │ Payment → Odoo         │  │
│  └───────┬────────┘  └────────┬─────────┘  └───────────┬────────────┘  │
└──────────┼────────────────────┼────────────────────────┼────────────────┘
           │                    │                        │
           ▼                    ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         REASONING LAYER                                 │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      CLAUDE CODE / QWEN                           │ │
│  │   Read → Classify → Think → Plan → Write → Request Approval       │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │              Ralph Wiggum Loop (Autonomous)                       │ │
│  │   Create State → Run AI → Check Complete → Re-inject → Loop       │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
              ┌──────────────────┼───────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
┌────────────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│    HUMAN-IN-THE-LOOP   │ │  ERROR RECOVERY  │ │    CEO BRIEFING        │
│  ┌──────────────────┐  │ │  ┌────────────┐  │ │  ┌──────────────────┐  │
│  │ Review Approval  │──┼─┤  │ Retry      │  │ │  │ Weekly Report    │  │
│  │ Move to Approved │  │ │  │ Handler    │  │ │  │ Revenue Analysis │  │
│  └────────┬─────────┘  │ │  └────────────┘  │ │  │ Bottlenecks      │  │
└───────────┼────────────┘ │  ┌────────────┐  │ │  │ Subscriptions    │  │
            │              │  │ Circuit    │  │ │  │ Social Metrics   │  │
            │              │  │ Breaker    │  │ │  └────────┬─────────┘  │
            │              │  └────────────┘  │ │           │            │
            ▼              └────────┬─────────┘ └───────────┼────────────┘
                                   │                       │
              ┌────────────────────┼───────────────────────┤
              ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ACTION LAYER (MCP Servers)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Email   │ │ LinkedIn │ │ Facebook │ │ Twitter  │ │  Odoo    │      │
│  │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │      │
│  │ (4 tools)│ │(5 tools) │ │(8 tools) │ │(7 tools) │ │(10 tools)│      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL ACTIONS                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Send     │ │ Post/    │ │ Post to  │ │ Tweet/   │ │ Invoice/ │      │
│  │ Email    │ │ Message  │ │ FB/IG    │ │ Reply    │ │ Payment  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                             │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │              Orchestrator.py (Master Process)                     │ │
│  │   Domain Classification │ HITL Workflow │ Dashboard Updates       │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │              PM2 / Task Scheduler (Background)                    │ │
│  │   5 Watchers │ Orchestrator │ Health Monitoring                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure (Gold Tier)

```
Personal-AI-Employe-FTEs/
│
├── scripts/                              # Python Automation (24 files)
│   ├── # Silver Tier (Existing)
│   ├── orchestrator.py                   # Main coordinator (enhanced)
│   ├── gmail_watcher.py                  # Gmail monitor
│   ├── linkedin_watcher.py               # LinkedIn monitor
│   ├── filesystem_watcher.py             # File system monitor
│   ├── audit_logger.py                   # Audit logging
│   ├── qwen_email_processor.py           # Email AI processing
│   ├── linkedin_post.py                  # LinkedIn posting
│   ├── mcp-client.py                     # Universal MCP client
│   │
│   └── # Gold Tier (New)
│   ├── ralph_wiggum.py                   # Autonomous task loop
│   ├── retry_handler.py                  # Exponential backoff retry
│   ├── circuit_breaker.py                # Circuit breaker pattern
│   ├── facebook_watcher.py               # Facebook/Instagram monitor
│   ├── twitter_watcher.py                # Twitter monitor
│   ├── ceo_briefing.py                   # Weekly briefing generator
│   └── cross_domain_integration.py       # Domain integration logic
│
├── mcp-servers/                          # External Action Handlers (5 servers)
│   ├── # Silver Tier
│   ├── email-mcp/                        # Gmail operations
│   └── linkedin-mcp/                     # LinkedIn operations
│   │
│   └── # Gold Tier (New)
│   ├── facebook-mcp/                     # Facebook + Instagram
│   │   ├── index.js                      # Graph API integration
│   │   └── package.json
│   ├── twitter-mcp/                      # Twitter/X
│   │   ├── index.js                      # API v2 integration
│   │   └── package.json
│   └── odoo-mcp/                         # Odoo Accounting
│       ├── index.js                      # JSON-RPC integration
│       └── package.json
│
├── odoo/                                 # Odoo Docker Setup
│   └── docker-compose.yml                # Odoo + PostgreSQL
│
├── .qwen/skills/                         # Agent Skills (8 skills)
│   ├── # Silver Tier
│   ├── browsing-with-playwright/
│   ├── email-operations/
│   ├── linkedin-operations/
│   └── hitl-approval/
│   │
│   └── # Gold Tier (New)
│   ├── facebook-operations/
│   │   └── SKILL.md
│   ├── twitter-operations/
│   │   └── SKILL.md
│   ├── odoo-accounting/
│   │   └── SKILL.md
│   └── ralph-wiggum/
│       └── SKILL.md
│
├── docs/                                 # Documentation
│   ├── planning/
│   │   └── GOLD_TIER_IMPLEMENTATION_PLAN.md
│   ├── setup/
│   │   ├── GOLD_TIER_COMPLIANCE.md
│   │   └── ...
│   ├── guides/
│   │   ├── ODOO_SETUP.md
│   │   └── ...
│   └── architecture/
│       └── GOLD_ARCHITECTURE.md
│
├── personal-ai-employee/                 # Obsidian Vault
│   ├── Dashboard.md                      # Enhanced (Gold metrics)
│   ├── Company_Handbook.md
│   ├── Business_Goals.md
│   ├── Inbox/
│   ├── Needs_Action/                     # All domains
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Rejected/
│   ├── Done/
│   ├── Plans/
│   ├── In_Progress/
│   ├── Briefings/                        # CEO briefings
│   ├── Accounting/                       # Odoo sync
│   └── Logs/                             # Audit logs
│
├── logs/                                 # Runtime logs
│   ├── orchestrator.log
│   ├── gmail_watcher.log
│   ├── facebook_watcher.log
│   ├── twitter_watcher.log
│   ├── ceo_briefing.log
│   └── ...
│
├── mcp-config.json                       # MCP server config (5 servers)
├── requirements.txt                      # Python dependencies
├── ecosystem.config.cjs                  # PM2 configuration
└── README.md
```

---

## 🔄 Data Flow

### 1. Email Processing Flow (Personal Domain)

```
Gmail API → Gmail Watcher
  → Creates EMAIL_*.md in /Needs_Action/
    → Orchestrator detects new item
      → Domain Classifier: "personal"
        → Approval Manager: Check threshold
          → If approval needed → /Pending_Approval/
            → User moves to /Approved/
              → Email MCP sends email
                → Move to /Done/
                  → Audit Logger logs action
                    → Dashboard updates
```

### 2. Social Media Flow (Business Domain)

```
Facebook Watcher polls Graph API
  → Detects comment/mention
    → Creates FACEBOOK_COMMENT_*.md in /Needs_Action/
      → Orchestrator processes
        → Domain Classifier: "business"
          → Cross-Domain Trigger Detector
            → If triggers business action → Create task
              → Ralph Wiggum Loop processes task
                → AI drafts response
                  → Creates /Pending_Approval/FACEBOOK_REPLY_*.md
                    → User approves
                      → Facebook MCP posts reply
                        → Move to /Done/
```

### 3. Accounting Flow (Business Domain)

```
Client email requests invoice
  → Orchestrator classifies as "business"
    → Creates invoice task
      → Odoo MCP:
        1. Create customer (if new)
        2. Create invoice with line items
        3. Creates /Pending_Approval/INVOICE_*.md
          → User approves
            → Odoo MCP: Validate invoice
              → Invoice posted in Odoo
                → Email MCP: Send invoice to client
                  → Audit Logger logs
                    → Dashboard updates revenue
```

### 4. CEO Briefing Flow (Weekly)

```
Task Scheduler (Sunday 10 PM)
  → Triggers ceo_briefing.py
    → Gathers data from:
      - /Done/ (completed tasks)
      - /Accounting/ (revenue data)
      - /Logs/ (audit logs)
      - /Plans/ (bottlenecks)
      - Odoo (via MCP, if available)
      - Social media (via MCP, if available)
    → Generates briefing:
      - Revenue summary
      - Completed tasks
      - Bottlenecks
      - Proactive suggestions
      - Subscription audit
      - Social metrics
    → Saves to /Briefings/YYYY-MM-DD_Monday_Briefing.md
    → Updates Dashboard.md
```

---

## 🛡️ Error Handling Architecture

### Retry Pattern

```python
@with_retry(max_attempts=3, base_delay=2, max_delay=30)
def send_email_via_gmail(to, subject, body):
    # May fail transiently, will retry automatically
    gmail_api.send(to, subject, body)
```

**Behavior:**
- Attempt 1: Fail → wait 2s (±jitter)
- Attempt 2: Fail → wait 4s (±jitter)
- Attempt 3: Fail → wait 8s (±jitter)
- Attempt 4: Fail → raise exception

### Circuit Breaker Pattern

```
State: CLOSED (normal)
  ↓ 5 consecutive failures
State: OPEN (failing fast, reject immediately)
  ↓ 5 minutes timeout
State: HALF_OPEN (test recovery)
  ↓ Success
State: CLOSED (recovered)
```

**Pre-configured Breakers:**
- `gmail_breaker` - 5 failures, 5 min recovery
- `linkedin_breaker` - 3 failures, 10 min recovery
- `facebook_breaker` - 5 failures, 5 min recovery
- `twitter_breaker` - 5 failures, 5 min recovery
- `odoo_breaker` - 3 failures, 10 min recovery
- `mcp_breaker` - 5 failures, 2 min recovery

---

## 🔐 Security Architecture

### Credential Management

```
Never stored in vault or git:
  ❌ personal-ai-employee/*.md
  ❌ Git repository

Stored securely:
  ✅ .env files (gitignored)
  ✅ MCP server CONFIG objects (update manually)
  ✅ Docker secrets (for Odoo)
```

### HITL Safeguards

| Action | Threshold | Approval |
|--------|-----------|----------|
| Email to known contact | Personal domain | Auto-send (optional) |
| Email to new contact | Any domain | ✅ Required |
| Social media post | Any platform | ✅ Required |
| Invoice creation | < $500 | ✅ Required |
| Invoice creation | >= $500 | ✅ Required |
| Payment recording | Any amount | ✅ Required |
| Subscription cancellation | Any | ✅ Required |

---

## 📊 Dashboard Architecture

### Gold Tier Dashboard Metrics

| Section | Metrics |
|---------|---------|
| **Executive Summary** | Personal pending, Business pending, Revenue MTD |
| **Personal Domain** | Emails, Messages, Tasks |
| **Business Domain** | Revenue (week/MTD), Invoices, Social Media |
| **Watcher Status** | 5 watchers with health status |
| **MCP Server Status** | 5 servers with circuit breaker state |
| **Recent Activity** | Last 10 actions |
| **System Health** | Orchestrator, Ralph Loop, Circuit Breakers |

---

## 🚀 Deployment Options

### Local Development (Current)
- All watchers run on local machine
- PM2 manages processes
- Windows Task Scheduler for CEO Briefing

### Future: Cloud Deployment (Platinum Tier)
- Cloud VM (Oracle Free Tier, AWS, etc.)
- Docker Compose for all services
- Local owns: approvals, WhatsApp, payments
- Cloud owns: email triage, social drafts

---

*Last Updated: 2026-04-05*  
*Architecture Version: Gold 1.0*
