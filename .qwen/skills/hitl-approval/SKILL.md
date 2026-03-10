---
name: hitl-approval
description: |
  Human-in-the-Loop (HITL) approval workflow management. Create approval requests,
  process approved items, and manage the approval pipeline. Use for sensitive actions
  requiring human oversight before execution.
---

# HITL Approval Workflow

Manage human approval workflow for sensitive actions.

## Overview

The HITL system ensures human oversight for sensitive operations:
- Payments over threshold
- Communications to new contacts
- Social media posts
- Subscription cancellations

## Folder Structure

```
personal-ai-employee/
├── Pending_Approval/    # Awaiting human review
├── Approved/            # Approved, ready to execute
├── Rejected/            # Rejected, with reason
└── Done/                # Completed actions
```

## Workflow

### Step 1: Create Approval Request

When Claude detects a sensitive action:

```markdown
---
type: approval_request
action: send_email
created: 2026-03-10T10:00:00
status: pending
priority: high
source_item: EMAIL_abc123.md
---

# Approval Required: Send Email

## Details
- To: newclient@example.com
- Subject: Project Proposal
- Reason: New contact (first communication)

## To Approve
Move this file to /Approved/ folder.

## To Reject
Move this file to /Rejected/ folder.
```

### Step 2: Human Review

User reviews file in Obsidian or file explorer.

### Step 3: Decision

| Action | Result |
|--------|--------|
| Move to `/Approved/` | Execute action |
| Move to `/Rejected/` | Discard with reason |
| Edit then `/Approved/` | Modify then execute |

### Step 4: Execution

Orchestrator detects approved file and executes via MCP.

## Approval Thresholds

Per Company_Handbook.md:

| Action Type | Threshold | Auto-OK |
|-------------|-----------|---------|
| Payments | > $50 | ❌ Require approval |
| Emails to new contacts | Any | ❌ Require approval |
| LinkedIn posts | Any | ❌ Require approval |
| Connection requests (VIP) | Any | ❌ Require approval |
| Subscription cancellation | Any | ❌ Require approval |
| Emails to known contacts | Any | ✅ Auto-send |
| Payments < $50 (recurring) | < $50 | ✅ Auto-process |

## Create Approval Request Template

```python
def create_approval_request(action_type, details, source_item):
    """Create approval request file in Pending_Approval/"""
    approval_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = pending_approval_path / f'APPROVAL_{action_type}_{approval_id}.md'
    
    content = f"""---
type: approval_request
action: {action_type}
created: {datetime.now().isoformat()}
status: pending
priority: {details.get('priority', 'normal')}
source_item: {source_item.name}
---

# Approval Required: {action_type.replace('_', ' ').title()}

## Details

{json.dumps(details, indent=2)}

## Source

Generated while processing: `{source_item.name}`

## Action Required

**To APPROVE:** Move to `/Approved/` → Auto-executes

**To REJECT:** Move to `/Rejected/` → Add reason

**To MODIFY:** Edit → Move to `/Approved/`

---

*Expires: {datetime.now().strftime('%Y-%m-%d')} EOD*
"""
    filepath.write_text(content)
```

## Process Approved Items

```python
def process_approved_items():
    """Process items in Approved folder"""
    for item in approved_path.glob('*.md'):
        # Read approval details
        content = item.read_text()
        
        # Extract action type and execute via MCP
        action_type = extract_action_type(content)
        details = extract_details(content)
        
        # Execute via appropriate MCP server
        result = execute_via_mcp(action_type, details)
        
        # Log and move to Done
        if result.success:
            content += f"\n**Executed:** {datetime.now().isoformat()}\n"
            item.rename(done_path / item.name)
```

## Audit Trail

All approvals are logged:
- Original request in `Pending_Approval/`
- Decision timestamp in file content
- Execution result in `Done/`
- Rejection reasons in `Rejected/`

## Best Practices

1. **Clear descriptions** - Explain why approval is needed
2. **Expiry dates** - Set reasonable deadlines
3. **Priority levels** - Mark urgent vs normal
4. **Source tracking** - Link to original action file
5. **Execution logging** - Record results in Done folder

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Approval not executing | Check orchestrator is running |
| File stuck in Approved | Check MCP server availability |
| Duplicate approvals | Check processed_files set in orchestrator |
| Missing audit trail | Ensure logging in all execution paths |
