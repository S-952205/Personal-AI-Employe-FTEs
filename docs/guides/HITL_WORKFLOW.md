# Complete HITL (Human-in-the-Loop) Workflow Guide

## Overview

This guide explains the **complete workflow** where Qwen AI processes emails, creates approval requests, and sends emails only after your approval.

---

## 📋 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE HITL WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Gmail Watcher                                                   │
│     └─→ Detects new email                                          │
│     └─→ Creates EMAIL_*.md in /Needs_Action/                       │
│                                                                     │
│  2. Orchestrator                                                    │
│     └─→ Creates PLAN_*.md                                          │
│     └─→ Triggers Qwen Code                                         │
│                                                                     │
│  3. Qwen AI Processing                                              │
│     ├─→ Reads Company Handbook                                     │
│     ├─→ For promotional emails:                                    │
│     │   └─→ Marks as "No action required" → Moves to /Done/       │
│     │                                                               │
│     └─→ For business emails requiring response:                    │
│         ├─→ Drafts professional response                           │
│         ├─→ Creates APPROVAL_*.md in /Pending_Approval/           │
│         └─→ Original email → Moves to /Done/                       │
│                                                                     │
│  4. Human Review (YOU)                                              │
│     ├─→ Check /Pending_Approval/ folder                            │
│     ├─→ Review draft response                                      │
│     ├─→ If approved: Move file to /Approved/                       │
│     └─→ If rejected: Move to /Rejected/ with reason                │
│                                                                     │
│  5. Orchestrator (Auto-detects approval)                            │
│     ├─→ Detects file in /Approved/                                 │
│     ├─→ Extracts email details                                     │
│     ├─→ Calls MCP server to send email                             │
│     └─→ Moves to /Done/ with result                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Usage

### **Step 1: Start the System**

```bash
# Terminal 1: Start Gmail Watcher
python scripts/gmail_watcher.py

# Terminal 2: Start Orchestrator
python scripts/orchestrator.py
```

---

### **Step 2: Email Arrives**

When a new email arrives:

```
2026-03-14 22:15:00 - GmailWatcher - INFO - Found 1 new email(s)
2026-03-14 22:15:01 - GmailWatcher - INFO - Created action file: EMAIL_abc123.md
```

**File created:** `personal-ai-employee/Needs_Action/EMAIL_abc123.md`

---

### **Step 3: Orchestrator Processes**

```
2026-03-14 22:15:30 - Orchestrator - INFO - Found 1 pending items
2026-03-14 22:15:30 - Orchestrator - INFO - Created plan: PLAN_20260314_221530.md
2026-03-14 22:15:30 - Orchestrator - INFO - Triggering Qwen Code...
```

---

### **Step 4: Qwen AI Creates Approval Request**

For emails requiring response, Qwen creates:

**File:** `personal-ai-employee/Pending_Approval/APPROVAL_send_email_20260314_221600.md`

```markdown
---
type: approval_request
action: send_email
created: 2026-03-14T22:16:00
status: pending
priority: high
source_item: EMAIL_abc123.md
---

# Approval Required: Send Email Response

## Email Details
- To: client@example.com
- Subject: Re: Project Inquiry
- Reason: Response requires human approval per Company Handbook

## Draft Response

Dear Client,

Thank you for your inquiry. We would be happy to discuss your project...

[Full email response here]

Best regards,
Your Name

## To Approve
Move this file to /Approved/ folder.

## To Reject
Move this file to /Rejected/ folder with reason.
```

---

### **Step 5: You Review and Approve**

**Option A: Approve**
```bash
# Move file to Approved folder
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\
```

**Option B: Reject**
```bash
# Move to Rejected with note
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Rejected\
# Edit file to add rejection reason
```

**Option C: Modify then Approve**
```bash
# Edit the draft response in the approval file
# Then move to Approved
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\
```

---

### **Step 6: Orchestrator Sends Email**

Within 30 seconds, orchestrator detects approval:

```
2026-03-14 22:20:00 - Orchestrator - INFO - Found 1 approved items
2026-03-14 22:20:00 - Orchestrator - INFO - Processing approved item: APPROVAL_*.md
2026-03-14 22:20:01 - Orchestrator - INFO - Sending email via MCP to: client@example.com
2026-03-14 22:20:05 - Orchestrator - INFO - ✓ Email sent successfully to client@example.com
2026-03-14 22:20:05 - Orchestrator - INFO - Moved to Done: APPROVAL_*.md
```

---

## 📁 Folder Structure

```
personal-ai-employee/
├── Needs_Action/          # New emails arrive here
├── Pending_Approval/      # Approval requests from Qwen
├── Approved/              # You move approved items here
├── Rejected/              # Rejected items with reason
├── Done/                  # Completed items
│   ├── EMAIL_*.md        # Processed emails
│   └── APPROVAL_*.md     # Sent email approvals
└── Plans/                 # Qwen's processing plans
```

---

## 🎯 What Requires Approval?

Per Company Handbook:

| Action | Approval Required? |
|--------|-------------------|
| Email response to new contact | ✅ Yes |
| Email response to known client | ✅ Yes (Silver tier) |
| Payment > $50 | ✅ Yes |
| LinkedIn post | ✅ Yes |
| Connection request to VIP | ✅ Yes |
| Promotional email (no response) | ❌ No - auto-archived |

---

## 📊 Dashboard Status

The Dashboard.md shows:

```markdown
| Metric | Count | Status |
|--------|-------|--------|
| Pending Actions | 0 | ✅ Clear |
| Pending Approvals | 2 | ⏳ Awaiting Review |
| Last Processed | 2026-03-14 22:20:05 | |
```

---

## 🔧 Testing the Workflow

### **Create Test Email**

```bash
# Create a test email file
cat > personal-ai-employee/Needs_Action/EMAIL_TEST001.md << EOF
---
type: email
from: test@example.com
subject: Business Inquiry
received: 2026-03-14T22:00:00
priority: high
status: pending
---

# Email Received

**From:** test@example.com

**Subject:** Business Inquiry

I'm interested in your services. Can you send me a quote?

---

## Suggested Actions

- [ ] Draft response
- [ ] Create approval request
- [ ] Send after approval
EOF
```

### **Run Orchestrator**

```bash
python scripts/orchestrator.py
```

### **Check for Approval Request**

```bash
# After 2 minutes, check Pending_Approval folder
dir personal-ai-employee\Pending_Approval\
```

### **Approve and Send**

```bash
# Move to Approved
move personal-ai-employee\Pending_Approval\APPROVAL_*.md personal-ai-employee\Approved\

# Wait 30 seconds for orchestrator to process
# Check Done folder
dir personal-ai-employee\Done\APPROVAL_*.md
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| No approval request created | Check Qwen output, ensure prompt includes approval instructions |
| Email not sent after approval | Check MCP server is running, credentials valid |
| Orchestrator not detecting approval | Ensure file moved to `/Approved/` (not subfolder) |
| MCP send fails | Check `logs/orchestrator.log` for error details |

---

## 📝 Key Files

| File | Purpose |
|------|---------|
| `scripts/orchestrator.py` | Main coordinator with HITL workflow |
| `scripts/gmail_watcher.py` | Monitors Gmail for new emails |
| `mcp-servers/email-mcp/index.js` | Email MCP server |
| `personal-ai-employee/Company_Handbook.md` | Rules for Qwen AI |

---

## ✅ Workflow Checklist

- [ ] Gmail watcher running
- [ ] Orchestrator running
- [ ] Email arrives → Creates action file
- [ ] Qwen processes → Creates approval request
- [ ] You review approval request
- [ ] Move to `/Approved/` folder
- [ ] Orchestrator sends email via MCP
- [ ] Result saved to `/Done/`

---

**Your AI Employee now has full HITL workflow!** 🎉
