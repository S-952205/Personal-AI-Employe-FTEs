# Silver Tier Gmail - Complete Usage Guide

## ✅ What's Now Working

Your AI Employee now follows the **full Silver Tier flow**:

```
Gmail → Needs_Action → Plan.md → Qwen AI Processing → Pending_Approval → (Your Approval) → Approved → MCP Send → Done
```

---

## 🎯 Complete Workflow Steps

### **Step 1: Start Gmail Watcher**

```bash
cd C:\Projects\Personal-AI-Employe-FTEs
python scripts\gmail_watcher.py
```

**What it does:**
- Checks Gmail every 2 minutes
- Creates `EMAIL_*.md` files in `personal-ai-employee/Needs_Action/`
- Tracks processed emails (won't re-process same emails)

**Leave this running in a terminal window.**

---

### **Step 2: Start Orchestrator**

Open a **new terminal** and run:

```bash
cd C:\Projects\Personal-AI-Employe-FTEs
python scripts\orchestrator.py
```

**What it does:**
- Checks every 30 seconds for new emails in `Needs_Action/`
- Creates `PLAN_*.md` in `Plans/` folder
- Runs **Qwen Code AI** to process emails
- Creates approval requests in `Pending_Approval/`
- Executes approved actions from `Approved/` folder
- Updates `Dashboard.md` with status

**Leave this running in a terminal window.**

---

### **Step 3: Email Processing Flow (Automatic)**

When a new email arrives in Gmail:

1. **Gmail Watcher** detects it (within 2 minutes)
2. Creates `EMAIL_*.md` in `Needs_Action/`
3. **Orchestrator** detects the new file
4. Creates `PLAN_*.md` with processing instructions
5. **Qwen AI** reads the email and classifies it:
   - **Business** → Creates approval request with draft response
   - **Promotional** → Archives to `Done/`
   - **Personal** → Archives to `Done/`
6. Approval request appears in `Pending_Approval/`

---

### **Step 4: Review and Approve (Manual)**

**Check for approval requests:**

```bash
dir personal-ai-employee\Pending_Approval\*.md
```

**View the approval request:**

```bash
type personal-ai-employee\Pending_Approval\APPROVAL_*.md
```

**You'll see:**
- Email classification (business/promotional/personal)
- Draft response written by Qwen AI
- Instructions to approve/reject

**To APPROVE the email:**

```bash
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\
```

**To REJECT:**

```bash
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Rejected\
```

**To MODIFY then approve:**
1. Edit the draft in the approval file
2. Move to `Approved/` folder

---

### **Step 5: Email Sent via MCP (Automatic)**

**Orchestrator will automatically:**
- Detect file in `Approved/` folder (within 30 seconds)
- Extract email recipient and draft response
- Send email via Gmail API (MCP)
- Move approval file to `Done/` with result
- Update dashboard

**Check the result:**

```bash
type personal-ai-employee\Done\APPROVAL_*.md
```

---

## 📋 Quick Reference Commands

### Start All Services

```bash
# Terminal 1: Gmail Watcher
start python scripts\gmail_watcher.py

# Terminal 2: Orchestrator  
start python scripts\orchestrator.py
```

### Check Status

```bash
# Check pending emails
dir personal-ai-employee\Needs_Action\*.md

# Check approval requests
dir personal-ai-employee\Pending_Approval\*.md

# Check approved (waiting to send)
dir personal-ai-employee\Approved\*.md

# Check completed
dir personal-ai-employee\Done\*.md

# View dashboard
type personal-ai-employee\Dashboard.md
```

### View Logs

```bash
# Gmail Watcher logs
type logs\gmail_watcher.log

# Orchestrator logs
type logs\orchestrator.log

# Qwen Processor logs
type logs\qwen_email_processor.log
```

---

## 🧪 Testing the Complete Flow

### Test 1: Create Test Business Email

```bash
# Create test email
notepad personal-ai-employee\Needs_Action\EMAIL_TEST_CLIENT.md
```

Paste this content:

```markdown
---
type: email
from: client@company.com
subject: Website Development Project
received: 2026-03-17T20:00:00
priority: high
status: pending
---

# Email Received

**From:** client@company.com

**Subject:** Website Development Project

Hi,

I need a professional website for my business.
Budget is $3000-5000. Can you help?

Timeline: Need it completed by April 15th.

Thanks,
John Smith
CEO, TechCorp
```

**Wait 30-60 seconds** and check:

```bash
# Should see approval request created
dir personal-ai-employee\Pending_Approval\
```

---

### Test 2: Approve and Send

```bash
# Move to Approved
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\

# Wait 30 seconds for orchestrator

# Check Done folder
dir personal-ai-employee\Done\APPROVAL_*.md

# View result
type personal-ai-employee\Done\APPROVAL_*.md
```

---

## 📊 Email Classification Rules

Qwen AI classifies emails into these categories:

| Category | Keywords | Action |
|----------|----------|--------|
| **Business** | project, proposal, budget, client, contract, invoice, website, develop, hire | Create approval request + draft response |
| **Promotional** | newsletter, unsubscribe, LinkedIn, promotion, discount, marketing | Archive to Done/ |
| **Personal** | Duolingo, social notifications, personal messages | Archive to Done/ |
| **Urgent** | urgent, asap, emergency, deadline, payment | High priority approval request |

---

## 🔧 Troubleshooting

### Issue: Same emails detected repeatedly

**Solution:** Delete processed IDs file

```bash
del .gmail_processed_ids.json
```

---

### Issue: No approval requests created

**Check:**
1. Email has business keywords (project, budget, client, etc.)
2. Qwen is processing (check `Plans/` folder for `PLAN_*.md`)
3. Check logs: `type logs\qwen_email_processor.log`

---

### Issue: Email not sent after approval

**Check:**
1. File is in `Approved/` folder (not subfolder)
2. Orchestrator is running
3. Token file exists: `dir token.pickle`
4. Check logs: `type logs\orchestrator.log`

---

### Issue: Qwen not outputting valid JSON

**Solution:** The processor now handles this automatically:
- Uses stdin to avoid command line length limits
- Better prompt formatting
- Fallback to manual review if parsing fails

---

### Issue: Gmail authentication fails

**Solution:**

```bash
# Re-authenticate
python scripts\gmail_auth.py

# Delete old token and re-authenticate
del token.pickle
python scripts\gmail_auth.py
```

---

## 📁 Folder Structure Reference

```
personal-ai-employee/
├── Needs_Action/          # New emails land here from Gmail
├── Plans/                 # Qwen creates PLAN_*.md here
├── Pending_Approval/      # Approval requests from Qwen AI ← CHECK THIS
├── Approved/              # You move approved files here → Email sent
├── Rejected/              # Rejected approvals
├── Done/                  # Completed items (archived + sent emails)
├── In_Progress/           # Items needing manual review
├── Dashboard.md           # Status overview
├── Company_Handbook.md    # Rules for Qwen AI
└── Business_Goals.md      # Your business objectives
```

---

## 🎯 Daily Workflow

### Morning Check (5 minutes)

```bash
# 1. Check dashboard
type personal-ai-employee\Dashboard.md

# 2. Check pending approvals
dir personal-ai-employee\Pending_Approval\

# 3. Approve any pending emails
move personal-ai-employee\Pending_Approval\*.md personal-ai-employee\Approved\
```

### Evening Review (2 minutes)

```bash
# Check what was processed
dir personal-ai-employee\Done\*.md

# Check logs for errors
type logs\orchestrator.log | findstr "ERROR"
```

---

## ✅ Silver Tier Compliance Checklist

Your implementation now includes:

- [x] **Gmail Watcher** - Monitors every 2 minutes
- [x] **Qwen AI Processing** - Classifies and drafts responses
- [x] **Plan.md Creation** - Tracks processing plans
- [x] **HITL Approval Workflow** - Pending → Approved → Send
- [x] **MCP Email Sending** - Via Gmail API
- [x] **Dashboard Updates** - Real-time status
- [x] **Logging** - All actions logged to `logs/` folder

---

## 🚀 Next Steps (Gold Tier Upgrades)

To upgrade to Gold Tier, add:

1. **Odoo Accounting Integration**
   - Self-hosted accounting via MCP
   - Invoice generation and payment tracking

2. **Social Media Integration**
   - Facebook/Instagram posting
   - Twitter (X) scheduling

3. **Weekly CEO Briefing**
   - Automated business audit every Sunday
   - Revenue, bottlenecks, suggestions

4. **Cloud Deployment**
   - Run 24/7 on cloud VM
   - Always-on watchers

---

## 📞 Support

**Key Files:**
- `scripts/gmail_watcher.py` - Gmail monitoring
- `scripts/qwen_email_processor.py` - AI processing
- `scripts/orchestrator.py` - Main coordinator
- `scripts/gmail_auth.py` - Gmail authentication

**Documentation:**
- `GMAIL_TESTING_GUIDE.md` - Detailed Gmail setup
- `HITL_WORKFLOW.md` - Complete HITL guide
- `SILVER_QUICK_START.md` - Quick reference

---

**Your Silver Tier Gmail is now fully functional!** 🎉

The AI Employee will:
1. ✅ Detect emails from Gmail
2. ✅ Create action files in Needs_Action
3. ✅ Create Plan.md for tracking
4. ✅ Use Qwen AI to classify and draft responses
5. ✅ Create approval requests in Pending_Approval
6. ✅ Wait for your approval
7. ✅ Send via MCP when approved
8. ✅ Log everything to Done/
