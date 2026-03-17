# Gmail Integration - Complete Setup & Testing Guide

## ✅ What Was Fixed

1. **Gmail detecting 10 emails every time** → Fixed by persisting `processed_ids` to `.gmail_processed_ids.json`
2. **No approval requests created** → Replaced unreliable Qwen parsing with `simple_email_processor.py` (rule-based)
3. **Emails going straight to Done** → Now properly creates approval requests in `Pending_Approval/` folder

---

## 🚀 Quick Start

### Step 1: Reset Gmail Processed IDs (First Time Only)

This allows Gmail watcher to re-detect all unread emails:

```bash
cd C:\Projects\Personal-AI-Employe-FTEs
del .gmail_processed_ids.json
```

### Step 2: Test Email Processor Directly

Create a test email and process it:

```bash
# Test email is already created at:
# personal-ai-employee/Needs_Action/EMAIL_TEST_APPROVAL.md

# Run the processor
python scripts\simple_email_processor.py
```

**Expected Output:**
```
Approval requests created: 1
Emails archived: 0

✓ Check Pending_Approval/ folder for approval requests
```

### Step 3: Check Approval Request

```bash
# List approval requests
dir personal-ai-employee\Pending_Approval\*.md

# View the approval request
type personal-ai-employee\Pending_Approval\APPROVAL_*.md
```

You'll see a file with:
- Email classification (business/urgent/promotional)
- Draft response ready to send
- Instructions to approve/reject

---

## 📋 Complete Workflow

### Full Flow: Gmail → Approval → Send

```
1. Gmail Watcher detects new email
   ↓
2. Creates EMAIL_*.md in Needs_Action/
   ↓
3. Orchestrator runs Simple Email Processor
   ↓
4. Processor classifies email:
   - Business/Urgent → Creates approval request
   - Promotional → Archives to Done/
   - Unknown → Moves to In_Progress/
   ↓
5. Approval request created in Pending_Approval/
   ↓
6. YOU review and move to Approved/
   ↓
7. Orchestrator sends email via MCP
   ↓
8. Moves to Done/ with result
```

---

## 🧪 Testing Options

### Option A: Test Individual Components

```bash
# 1. Test Gmail authentication
python scripts\gmail_auth.py

# 2. Test Gmail watcher (single check)
python -c "from scripts.gmail_watcher import GmailWatcher; from pathlib import Path; g = GmailWatcher(str(Path('personal-ai-employee')), 'credentials.json'); g.authenticate(); emails = g.check_for_updates(); print(f'Found {len(emails)} emails')"

# 3. Test email processor
python scripts\simple_email_processor.py

# 4. Test orchestrator
python -c "from scripts.orchestrator import Orchestrator; from pathlib import Path; o = Orchestrator(Path('personal-ai-employee')); o.run_once()"
```

### Option B: Test Complete Flow

```bash
# 1. Reset processed IDs
del .gmail_processed_ids.json

# 2. Start all services
scripts\start-all.bat
```

This opens 3 windows:
- **Gmail Watcher** - Checks every 2 minutes
- **LinkedIn Watcher** - Checks every 5 minutes
- **Orchestrator** - Processes every 30 seconds

**Send yourself a test email** and watch the magic happen!

---

## 📁 Folder Structure

```
personal-ai-employee/
├── Needs_Action/          # New emails land here
├── Pending_Approval/      # Awaiting your approval ← CHECK THIS
├── Approved/              # You move files here to execute
├── Done/                  # Completed items
├── In_Progress/           # Needs human review
├── Plans/                 # Processing plans (optional)
└── Dashboard.md           # Status overview
```

---

## 🎯 How to Approve and Send Email

### When you see a file in `Pending_Approval/`:

1. **Review the draft response**
   ```bash
   type personal-ai-employee\Pending_Approval\APPROVAL_*.md
   ```

2. **Edit if needed** (optional)
   ```bash
   notepad personal-ai-employee\Pending_Approval\APPROVAL_*.md
   ```

3. **Approve by moving to Approved/**
   ```bash
   move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\
   ```

4. **Orchestrator will automatically:**
   - Detect the file in `Approved/`
   - Send email via MCP
   - Move to `Done/` with result

---

## 🔧 Troubleshooting

### Gmail watcher detects same emails every time

**Solution:** Delete the processed IDs file
```bash
del .gmail_processed_ids.json
```

### No approval requests created

**Check:**
1. Email has business keywords (project, proposal, budget, etc.)
2. Check logs: `type logs\email_processor.log`
3. Check classification in logs

### Email went to Done/ without approval

**Reason:** Classified as promotional (2+ promotional keywords)

**Fix:** Check `Done/EMAIL_*.md` for reason

### MCP email send fails

**Check:**
1. Credentials valid: `python scripts\gmail_auth.py`
2. Token exists: `dir token.pickle`
3. Check MCP logs: `type logs\orchestrator.log`

---

## 📊 Email Classification Rules

| Category | Keywords | Action |
|----------|----------|--------|
| **Urgent** | urgent, asap, emergency, deadline, priority | Approval + High Priority |
| **Business** | project, proposal, budget, client, contract, invoice, hire, develop | Approval + Draft |
| **Promotional** | newsletter, unsubscribe, promotion, discount, sale (2+ matches) | Archive |
| **Unknown** | No clear category | Move to In_Progress |

---

## 🎬 Example: Test Complete Flow

```bash
# Step 1: Clean slate
del .gmail_processed_ids.json
del personal-ai-employee\Needs_Action\*.md
del personal-ai-employee\Pending_Approval\*.md

# Step 2: Create test email
notepad personal-ai-employee\Needs_Action\EMAIL_TEST_CLIENT.md
```

Paste:
```markdown
---
type: email
from: john.doe@company.com
subject: Website Development Project
received: 2026-03-15T12:00:00
priority: high
---

# Email Received

**From:** john.doe@company.com

**Subject:** Website Development Project

Hi,

I need a professional website for my business. 
Budget is $3000-5000. Can you help?

Thanks,
John
```

```bash
# Step 3: Process
python scripts\simple_email_processor.py

# Step 4: Check result
dir personal-ai-employee\Pending_Approval\

# Step 5: Approve (move to Approved)
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\

# Step 6: Run orchestrator to send
python -c "from scripts.orchestrator import Orchestrator; from pathlib import Path; o = Orchestrator(Path('personal-ai-employee')); o.run_once()"

# Step 7: Check Done folder
dir personal-ai-employee\Done\
```

---

## 📝 Key Files Reference

| File | Purpose |
|------|---------|
| `scripts/gmail_watcher.py` | Monitors Gmail, creates action files |
| `scripts/simple_email_processor.py` | Classifies emails, creates approvals |
| `scripts/orchestrator.py` | Main coordinator, executes approved actions |
| `scripts/gmail_auth.py` | Gmail OAuth authentication |
| `.gmail_processed_ids.json` | Tracks processed emails (auto-created) |
| `logs/email_processor.log` | Email processing logs |
| `logs/gmail_watcher.log` | Gmail watcher logs |
| `logs/orchestrator.log` | Orchestrator logs |

---

## 🎯 Next Steps

1. **Test with real Gmail:**
   ```bash
   del .gmail_processed_ids.json
   python scripts\gmail_watcher.py
   # Wait 2 minutes, check Needs_Action/
   ```

2. **Run full system:**
   ```bash
   scripts\start-all.bat
   ```

3. **Send test email from another account**
   - Watch it get detected
   - Watch approval get created
   - Move to Approved/
   - Watch it send via MCP!

---

## 💡 Tips

- **Check logs first** when something doesn't work
- **Processed IDs persist** - delete `.gmail_processed_ids.json` to re-detect all
- **Approval workflow is manual** - you control what gets sent
- **MCP sends real emails** - test with your own email first
- **Promotional emails auto-archive** - check Done/ if missing

---

*Your AI Employee is now ready to manage your inbox! 🎉*
