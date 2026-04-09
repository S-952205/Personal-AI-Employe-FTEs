# Gold Tier Implementation Plan - Personal AI Employee FTE

**Analysis Date:** 2026-04-05
**Current Tier:** ✅ Silver Tier (Complete & Verified)
**Target Tier:** 🎯 Gold Tier (Autonomous Employee)
**Analyst:** Qwen Code

---

## 📊 Current State Analysis

### ✅ What's Working (Silver Tier Complete)

Your implementation has **successfully delivered** all Silver Tier requirements:

| Component | Status | Details |
|-----------|--------|---------|
| **Watchers** | ✅ 3 Working | Gmail (OAuth2, 2min polling), LinkedIn (manual input + demo), File System (watchdog) |
| **MCP Servers** | ✅ 2 Working | Email MCP (4 tools), LinkedIn MCP (5 tools) |
| **HITL Workflow** | ✅ Complete | Pending_Approval → Approved → Execute → Done pipeline |
| **Orchestrator** | ✅ Working | Processes Needs_Action, creates plans, triggers Qwen, manages approvals |
| **Scheduling** | ✅ Complete | PM2 (4 processes), Windows Task Scheduler |
| **Agent Skills** | ✅ 4 Installed | browsing-with-playwright, email-operations, linkedin-operations, hitl-approval |
| **Audit Logging** | ✅ Gold-Ready | JSON daily logs, 90-day retention, summary reports |
| **LinkedIn Auto-Posting** | ✅ Working | Playwright-based with audience dialog handling |

### ⚠️ Known Issues & Technical Debt

| Issue | Severity | Impact |
|-------|----------|--------|
| Orchestrator `_send_email_via_mcp()` bypasses MCP | Medium | Uses direct Gmail API instead of MCP (works but inconsistent naming) |
| LinkedIn watcher is passive | Medium | Relies on manual `LinkedIn_Inbox.md` input, doesn't scrape notifications |
| All emails forced to approval | Medium | Contradicts Company_Handbook.md rules (promotional should auto-archive) |
| Dashboard.md stale | Low | Last updated 2026-03-10, shows outdated status |
| Qwen CLI dependency | Medium | `trigger_qwen()` method may not be reliably configured |

---

## 🎯 Gold Tier Requirements (from Hackathon Blueprint)

Based on the blueprint document `Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026.md`, here are the **11 Gold Tier requirements**:

| # | Requirement | Status | Priority |
|---|-------------|--------|----------|
| 1 | All Silver requirements | ✅ Complete | Foundation |
| 2 | Full cross-domain integration (Personal + Business) | ❌ Not Started | HIGH |
| 3 | Odoo Accounting integration (self-hosted, local) | ❌ Not Started | HIGH |
| 4 | Facebook/Instagram integration + posting + summary | ❌ Not Started | HIGH |
| 5 | Twitter (X) integration + posting + summary | ❌ Not Started | HIGH |
| 6 | Multiple MCP servers for different action types | ⚠️ Partial (2 exist, need more) | HIGH |
| 7 | Weekly Business & Accounting Audit + CEO Briefing | ❌ Not Started | HIGH |
| 8 | Error recovery and graceful degradation | ⚠️ Partial (basic try/except) | MEDIUM |
| 9 | Comprehensive audit logging | ✅ Already Complete | Done |
| 10 | Ralph Wiggum loop for autonomous multi-step completion | ❌ Not Started | HIGH |
| 11 | Documentation of architecture & lessons learned | ⚠️ Partial (Silver docs exist, need Gold update) | MEDIUM |

**Estimated Time:** 40+ hours

---

## 🚀 Gold Tier Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1 - 10 hours)

#### 1.1 Ralph Wiggum Loop Implementation
**What it is:** A Stop hook pattern that keeps Claude Code working autonomously until tasks are complete.

**Implementation Plan:**
1. Create `/scripts/ralph_wiggum.py` - Stop hook manager
2. Implement completion detection:
   - Check if task file exists in `/Done/`
   - Check for `<promise>TASK_COMPLETE</promise>` in output
3. Create re-injection mechanism:
   - Block Claude's exit attempt
   - Re-inject prompt with current state
   - Allow max iterations (configurable)
4. Integration with orchestrator:
   - Wrap email processing in Ralph loop
   - Wrap approval processing in Ralph loop
   - Wrap CEO briefing generation in Ralph loop

**Files to Create:**
- `scripts/ralph_wiggum.py` - Main Ralph Wiggum loop implementation
- `scripts/stop_hook.py` - Stop hook interceptor
- `.qwen/skills/ralph-wiggum/SKILL.md` - Skill documentation

**Acceptance Criteria:**
- ✅ Claude processes all `/Needs_Action` items without manual intervention
- ✅ Loop exits when all items in `/Done/`
- ✅ Max iterations respected (default: 10)
- ✅ Works with Qwen Code CLI

---

#### 1.2 Error Recovery & Graceful Degradation
**What it is:** System continues operating even when components fail.

**Implementation Plan:**
1. Create retry handler with exponential backoff:
   ```python
   @with_retry(max_attempts=3, base_delay=1, max_delay=60)
   def send_email(...):
       ...
   ```
2. Implement graceful degradation:
   - Gmail API down → Queue emails locally, process when restored
   - LinkedIn session expired → Save post draft, retry later
   - Odoo unavailable → Queue accounting entries, retry on next cycle
3. Create watchdog process monitor:
   - Check PM2 process health every 60s
   - Auto-restart failed processes
   - Alert user via log file if restart fails
4. Add circuit breaker pattern:
   - Track consecutive failures
   - Open circuit after 5 failures
   - Half-open after 5 minutes
   - Close on success

**Files to Create/Modify:**
- `scripts/retry_handler.py` - Retry logic with exponential backoff
- `scripts/circuit_breaker.py` - Circuit breaker pattern
- `scripts/watchdog_monitor.py` - Process health monitor
- `scripts/orchestrator.py` - Integrate retry/circuit breaker

**Acceptance Criteria:**
- ✅ Failed email send retries 3 times before giving up
- ✅ System queues items when external API unavailable
- ✅ Failed watchers auto-restart via PM2
- ✅ Circuit breaker prevents cascade failures

---

### Phase 2: Social Media Expansion (Week 2 - 12 hours)

#### 2.1 Facebook/Instagram Integration
**What it is:** MCP server + watcher for Meta platforms.

**Implementation Plan:**
1. Create Facebook/Instagram MCP server:
   - Use Facebook Graph API for posting
   - Support text posts, images, stories
   - Read page insights/analytics
   - Schedule posts
2. Create Facebook watcher:
   - Monitor page notifications
   - Detect messages/comments
   - Create action files in `/Needs_Action/`
3. Create agent skill:
   - `facebook-operations/SKILL.md`
   - Scripts for common operations
4. Implement HITL workflow:
   - All posts require approval
   - Analytics summary generated weekly

**Files to Create:**
- `mcp-servers/facebook-mcp/index.js` - Facebook/Instagram MCP server
- `scripts/facebook_watcher.py` - Monitor Facebook activity
- `.qwen/skills/facebook-operations/SKILL.md` - Skill documentation
- `scripts/facebook_post.py` - Standalone posting script (optional)

**Dependencies:**
- Facebook Developer Account
- Page Access Token
- Instagram Business Account linked to Facebook Page

**Acceptance Criteria:**
- ✅ Can post to Facebook Page via MCP
- ✅ Can post to Instagram Business account
- ✅ Watcher detects new notifications/messages
- ✅ Creates action files in `/Needs_Action/FACEBOOK_*.md`
- ✅ Requires approval before posting
- ✅ Weekly summary generated

---

#### 2.2 Twitter (X) Integration
**What it is:** MCP server + watcher for Twitter/X.

**Implementation Plan:**
1. Create Twitter MCP server:
   - Use Twitter API v2 for posting
   - Support tweets, replies, threads
   - Read notifications/mentions
   - Schedule tweets
2. Create Twitter watcher:
   - Monitor mentions/DMs
   - Detect keyword triggers
   - Create action files in `/Needs_Action/`
3. Create agent skill:
   - `twitter-operations/SKILL.md`
4. Implement HITL workflow:
   - All tweets require approval
   - Engagement summary generated weekly

**Files to Create:**
- `mcp-servers/twitter-mcp/index.js` - Twitter MCP server
- `scripts/twitter_watcher.py` - Monitor Twitter activity
- `.qwen/skills/twitter-operations/SKILL.md` - Skill documentation
- `scripts/twitter_post.py` - Standalone posting script (optional)

**Dependencies:**
- Twitter Developer Account (free tier available)
- API Key + Secret
- Bearer Token
- Access Token + Secret

**Acceptance Criteria:**
- ✅ Can post tweets via MCP
- ✅ Can reply to mentions
- ✅ Watcher detects new mentions/DMs
- ✅ Creates action files in `/Needs_Action/TWITTER_*.md`
- ✅ Requires approval before posting
- ✅ Weekly summary generated

---

### Phase 3: Odoo Accounting Integration (Week 3 - 12 hours)

#### 3.1 Odoo Community Setup
**What it is:** Self-hosted ERP for business accounting.

**Implementation Plan:**
1. Install Odoo Community Edition (local or cloud VM):
   - Option A: Docker container (recommended for local)
   - Option B: Direct installation on Windows
   - Option C: Cloud VM (Oracle Free Tier, AWS, etc.)
2. Configure basic accounting:
   - Chart of accounts
   - Products/services
   - Customer/vendor database
   - Invoice templates
3. Test manual operations:
   - Create invoice
   - Record payment
   - Generate report

**Setup Commands (Docker):**
```bash
docker run -d -p 8069:8069 --name odoo --mount source=odoo-data,target=/var/lib/odoo odoo:17
# Access: http://localhost:8069
```

**Acceptance Criteria:**
- ✅ Odoo accessible at `http://localhost:8069` or cloud URL
- ✅ Admin user created
- ✅ Basic accounting configured
- ✅ Can create invoices manually

---

#### 3.2 Odoo MCP Server
**What it is:** Bridge between AI Employee and Odoo via JSON-RPC API.

**Implementation Plan:**
1. Create Odoo MCP server:
   - Use Odoo's external JSON-RPC API
   - Implement key operations:
     - `create_invoice(customer, items, amount, due_date)`
     - `list_invoices(status, date_range)`
     - `record_payment(invoice_id, amount, date)`
     - `get_account_summary(date_range)`
     - `list_customers()`
     - `list_vendors()`
2. Authentication:
   - Store Odoo credentials securely (`.env`)
   - Use Odoo API key or session auth
3. Create agent skill:
   - `odoo-accounting/SKILL.md`
4. Implement HITL workflow:
   - Draft invoices require approval
   - Payments > $50 always require approval
   - Read-only operations (list/get) auto-approved

**Reference:** [Odoo 19 External API Docs](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
**Reference MCP:** [mcp-odoo-adv](https://github.com/AlanOgic/mcp-odoo-adv)

**Files to Create:**
- `mcp-servers/odoo-mcp/index.js` - Odoo MCP server
- `scripts/odoo_auth.py` - Odoo authentication helper
- `.qwen/skills/odoo-accounting/SKILL.md` - Skill documentation
- `scripts/finance_watcher.py` - Monitor bank transactions (optional Gold+)

**Acceptance Criteria:**
- ✅ MCP server connects to Odoo
- ✅ Can create invoice via MCP tool call
- ✅ Can list invoices by status
- ✅ Can record payment
- ✅ Can generate account summary
- ✅ Credentials stored securely (not in vault)
- ✅ Requires approval for sensitive actions

---

### Phase 4: CEO Briefing & Cross-Domain Integration (Week 4 - 8 hours)

#### 4.1 Weekly CEO Briefing Generator
**What it is:** Autonomous weekly business audit and report.

**Implementation Plan:**
1. Create briefing generator script:
   - Read `/Done/` folder for completed tasks
   - Read `/Accounting/` for financial data (from Odoo)
   - Read `/Briefings/` for historical data
   - Read `Business_Goals.md` for targets
2. Generate comprehensive report:
   ```markdown
   # Monday Morning CEO Briefing
   
   ## Executive Summary
   ## Revenue (This Week, MTD, Trend)
   ## Completed Tasks
   ## Bottlenecks
   ## Proactive Suggestions
     - Cost Optimization
     - Subscription Audit
     - Upcoming Deadlines
   ```
3. Schedule via Task Scheduler:
   - Run every Sunday at 10 PM
   - Save to `/Briefings/YYYY-MM-DD_Monday_Briefing.md`
   - Update `Dashboard.md` with key metrics
4. Add proactive suggestions:
   - Unused subscriptions (> 30 days no login)
   - Late payments from clients
   - Tasks taking longer than expected
   - Revenue trend analysis

**Files to Create:**
- `scripts/ceo_briefing.py` - Briefing generator
- `scripts/subscription_audit.py` - Subscription usage checker
- `scripts/revenue_tracker.py` - Revenue trend analysis

**Acceptance Criteria:**
- ✅ Generates briefing every Sunday night
- ✅ Includes revenue, tasks, bottlenecks
- ✅ Proactive suggestions actionable
- ✅ Saves to `/Briefings/` folder
- ✅ Updates `Dashboard.md`

---

#### 4.2 Full Cross-Domain Integration
**What it is:** Personal + Business domains working together.

**Implementation Plan:**
1. Enhance orchestrator to handle domains:
   - Personal: Gmail, WhatsApp, Calendar
   - Business: LinkedIn, Facebook, Twitter, Odoo
2. Create domain-specific processing rules:
   - Personal emails → Lower approval threshold
   - Business posts → Higher scrutiny, schedule during business hours
3. Create unified dashboard:
   - Personal metrics (emails, messages)
   - Business metrics (revenue, posts, invoices)
   - Combined health status
4. Implement inter-domain triggers:
   - Client email on Gmail → Create task in Business domain
   - LinkedIn message → Check calendar for meeting availability
   - Payment received → Update Odoo invoice status

**Files to Modify:**
- `scripts/orchestrator.py` - Add domain-aware processing
- `personal-ai-employee/Dashboard.md` - Add business metrics
- `personal-ai-employee/Company_Handbook.md` - Add domain rules

**Acceptance Criteria:**
- ✅ System processes both personal and business items
- ✅ Different approval thresholds per domain
- ✅ Dashboard shows unified metrics
- ✅ Cross-domain triggers work

---

### Phase 5: Documentation & Polish (Week 5 - 4 hours)

#### 5.1 Gold Tier Documentation
**What it is:** Comprehensive documentation of Gold tier implementation.

**Files to Create:**
- `docs/setup/GOLD_TIER_COMPLIANCE.md` - Compliance checklist
- `docs/setup/GOLD_TIER_VERIFICATION.md` - Verification report
- `docs/guides/ODOO_SETUP.md` - Odoo installation guide
- `docs/guides/SOCIAL_MEDIA_SETUP.md` - Facebook/Twitter setup
- `docs/guides/CEO_BRIEFING_GUIDE.md` - Briefing configuration
- `docs/guides/RALPH_WIGGUM_GUIDE.md` - Ralph loop setup
- `docs/architecture/GOLD_ARCHITECTURE.md` - Updated architecture diagram

**Update Existing Docs:**
- `README.md` - Add Gold tier features
- `QWEN.md` - Update with Gold context
- `personal-ai-employee/Company_Handbook.md` - Add new rules

**Acceptance Criteria:**
- ✅ All guides comprehensive and tested
- ✅ Architecture diagrams updated
- ✅ Setup instructions clear
- ✅ Troubleshooting section complete

---

## 📁 Proposed File Structure (Gold Tier)

```
Personal-AI-Employe-FTEs/
│
├── scripts/
│   ├── # Existing (Silver)
│   ├── orchestrator.py
│   ├── gmail_watcher.py
│   ├── linkedin_watcher.py
│   ├── filesystem_watcher.py
│   ├── audit_logger.py
│   ├── mcp-client.py
│   │
│   ├── # New (Gold)
│   ├── ralph_wiggum.py              # Ralph Wiggum loop
│   ├── stop_hook.py                 # Stop hook interceptor
│   ├── retry_handler.py             # Exponential backoff retry
│   ├── circuit_breaker.py           # Circuit breaker pattern
│   ├── watchdog_monitor.py          # Process health monitor
│   ├── facebook_watcher.py          # Facebook/Instagram monitor
│   ├── twitter_watcher.py           # Twitter monitor
│   ├── facebook_post.py             # Facebook posting script
│   ├── twitter_post.py              # Twitter posting script
│   ├── odoo_auth.py                 # Odoo authentication
│   ├── finance_watcher.py           # Bank transaction monitor
│   ├── ceo_briefing.py              # Weekly briefing generator
│   ├── subscription_audit.py        # Subscription usage checker
│   └── revenue_tracker.py           # Revenue trend analysis
│
├── mcp-servers/
│   ├── # Existing (Silver)
│   ├── email-mcp/
│   └── linkedin-mcp/
│   │
│   └── # New (Gold)
│   ├── facebook-mcp/
│   │   ├── index.js                 # Facebook/Instagram MCP
│   │   └── package.json
│   ├── twitter-mcp/
│   │   ├── index.js                 # Twitter MCP
│   │   └── package.json
│   └── odoo-mcp/
│       ├── index.js                 # Odoo accounting MCP
│       └── package.json
│
├── .qwen/skills/
│   ├── # Existing (Silver)
│   ├── browsing-with-playwright/
│   ├── email-operations/
│   ├── linkedin-operations/
│   └── hitl-approval/
│   │
│   └── # New (Gold)
│   ├── facebook-operations/
│   │   └── SKILL.md
│   ├── twitter-operations/
│   │   └── SKILL.md
│   ├── odoo-accounting/
│   │   └── SKILL.md
│   └── ralph-wiggum/
│       └── SKILL.md
│
├── docs/
│   ├── setup/
│   │   ├── GOLD_TIER_COMPLIANCE.md
│   │   ├── GOLD_TIER_VERIFICATION.md
│   │   └── ...
│   ├── guides/
│   │   ├── ODOO_SETUP.md
│   │   ├── SOCIAL_MEDIA_SETUP.md
│   │   ├── CEO_BRIEFING_GUIDE.md
│   │   ├── RALPH_WIGGUM_GUIDE.md
│   │   └── ...
│   └── architecture/
│       ├── GOLD_ARCHITECTURE.md
│       └── ...
│
└── personal-ai-employee/
    └── # Same structure, enhanced with:
        ├── Accounting/               # Odoo sync data
        ├── Briefings/                # CEO briefings
        └── Dashboard.md              # Updated with business metrics
```

---

## 🎯 Success Metrics (Gold Tier)

| Metric | Silver | Gold Target |
|--------|--------|-------------|
| **Watchers** | 3 | 5 (+ Facebook, Twitter) |
| **MCP Servers** | 2 | 5 (+ Facebook, Twitter, Odoo) |
| **Agent Skills** | 4 | 8 (+ Facebook, Twitter, Odoo, Ralph) |
| **Autonomous Loops** | 0 | 1 (Ralph Wiggum) |
| **CEO Briefings** | Manual | Auto-generated weekly |
| **Accounting** | None | Odoo integration |
| **Error Recovery** | Basic | Retry + Circuit Breaker |
| **Cross-Domain** | No | Yes (Personal + Business) |
| **Documentation** | Silver docs | Gold docs + architecture |

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Facebook/Twitter API access restricted | HIGH | Use official APIs with proper developer accounts, fallback to Playwright if needed |
| Odoo setup complex on Windows | MEDIUM | Recommend Docker or cloud VM, provide detailed setup guide |
| Ralph Wiggum loop infinite | HIGH | Implement max iterations, timeout, manual escape hatch |
| Too many approvals required | MEDIUM | Implement smart approval thresholds based on Company_Handbook rules |
| Social media API rate limits | MEDIUM | Implement rate limit handling, queue posts for off-peak times |

---

## 🚦 Recommended Implementation Order

1. ✅ **Start with Ralph Wiggum Loop** (Foundational, enables autonomy)
2. ✅ **Add Error Recovery** (Makes system robust before adding more integrations)
3. ✅ **Implement CEO Briefing** (Quick win, demonstrates value)
4. ✅ **Add Odoo Integration** (Most complex, requires external setup)
5. ✅ **Add Facebook/Instagram** (Social media expansion)
6. ✅ **Add Twitter/X** (Social media expansion)
7. ✅ **Cross-Domain Integration** (Ties everything together)
8. ✅ **Documentation** (Final polish)

---

## 📋 Pre-Gold Tier Checklist

Before starting implementation:

- [ ] Backup current codebase (`git commit -a`)
- [ ] Create `gold-tier` branch
- [ ] Review all Silver tier fixes applied
- [ ] Verify all Silver tests passing
- [ ] Set up development environment
- [ ] Gather API credentials:
  - [ ] Facebook Developer Account
  - [ ] Twitter Developer Account
  - [ ] Odoo instance (local Docker or cloud)
- [ ] Update `requirements.txt` with new dependencies
- [ ] Create Gold tier todo list (this document)

---

## 🎓 Key Learnings from Silver Tier

### What Worked Well
1. **Rule-based classification** over LLM-dependent (more reliable)
2. **Direct API calls** when MCP unreliable (pragmatic over perfect)
3. **HITL workflow** prevents AI accidents (critical for trust)
4. **Agent Skills** organize functionality well (reusable)
5. **Audit logging** provides visibility (Gold-tier compliant already)

### What to Improve
1. **MCP usage consistency** - Currently bypassing MCP for email
2. **Dashboard freshness** - Should auto-update on processing
3. **LinkedIn watcher** - Should actively monitor, not passive
4. **Approval intelligence** - Should follow Company_Handbook rules
5. **Process monitoring** - Need watchdog for auto-restart

---

## 📞 Next Steps

**Ready to begin Gold tier implementation?** 

I recommend we:
1. Create a `gold-tier` git branch
2. Start with **Ralph Wiggum Loop** (foundational feature)
3. Then add **Error Recovery** (makes system robust)
4. Then implement **CEO Briefing** (demonstrates value quickly)
5. Continue with **Odoo** and **Social Media** integrations

**Your decision:** Which Gold tier feature should we tackle first?

---

*Analysis Complete!* 🎉

**Summary:** Your Silver Tier implementation is solid and production-ready. The Gold tier will add significant autonomous capability, but requires careful planning for external integrations (Odoo, social media). The Ralph Wiggum loop is the most impactful foundational feature to start with.

---

*Last Updated: 2026-04-05*  
*Prepared for: Gold Tier Implementation*  
*Estimated Completion: 40+ hours across 5 phases*
