# 🚀 AI Employee - Quick Start Guide

**For Beginners** - Follow these exact steps

---

## ✅ CURRENT STATUS (As of Now)

| Component | Status |
|-----------|--------|
| **PM2** | ✅ Installed & Running |
| **Gmail Watcher** | ✅ Running (checks every 2 min) |
| **LinkedIn Watcher** | ✅ Running (checks every 5 min) |
| **File System Watcher** | ✅ Running (monitors Inbox) |
| **Orchestrator** | ✅ Running (processes every 30 sec) |
| **Windows Task Scheduler** | ❌ Not configured yet |

---

## 📖 PART 1: PM2 (Background Processes) - ALREADY DONE! ✅

Your AI Employee is **already running** in the background using PM2!

### **Check Status**
Open any terminal and run:
```bash
pm2 status
```

**Expected Output:**
```
┌────┬────────────────────┬──────────┬──────┬───────────┬──────────┬──────────┐
│ id │ name               │ mode     │ ↺    │ status    │ cpu      │ memory   │
├────┼────────────────────┼──────────┼──────┼───────────┼──────────┼──────────┤
│ 2  │ filesystem-watcher │ fork     │ 0    │ online    │ 0%       │ 19.3mb   │
│ 0  │ gmail-watcher      │ fork     │ 0    │ online    │ 0%       │ 27.2mb   │
│ 1  │ linkedin-watcher   │ fork     │ 0    │ online    │ 0%       │ 13.4mb   │
│ 3  │ orchestrator       │ fork     │ 0    │ online    │ 0%       │ 15.3mb   │
└────┴────────────────────┴──────────┴──────┴───────────┴──────────┴──────────┘
```

✅ **All processes should show "online"**

---

### **View Live Logs**

To see what's happening in real-time:

```bash
# View all logs together
pm2 logs

# View only Gmail watcher logs
pm2 logs gmail-watcher

# View only LinkedIn watcher logs
pm2 logs linkedin-watcher

# View only orchestrator logs
pm2 logs orchestrator

# View only file system watcher logs
pm2 logs filesystem-watcher
```

**To exit logs:** Press `Ctrl + C`

---

### **Common PM2 Commands**

| Command | What It Does |
|---------|--------------|
| `pm2 status` | Shows if processes are running |
| `pm2 logs` | Shows live logs from all processes |
| `pm2 restart all` | Restarts all processes |
| `pm2 stop all` | Stops all processes |
| `pm2 start all` | Starts all processes |
| `pm2 delete all` | Stops and removes all processes |
| `pm2 save` | Saves process list for auto-restart |

---

### **If Something Goes Wrong**

**Problem:** Processes show "errored" or "stopped"

**Solution:**
```bash
# Restart everything
pm2 restart all

# Check if they're running
pm2 status

# View error logs
pm2 logs --err
```

---

## 📖 PART 2: Windows Task Scheduler (Auto-Start on Boot)

This makes AI Employee start automatically when you turn on your computer.

### **Option A: Easy Way - Run Setup Script**

1. **Press `Windows Key + X`**
2. **Select "Terminal (Admin)" or "Command Prompt (Admin)"**
3. **Click "Yes" if asked for permission**
4. **Copy and paste these commands:**

```batch
cd C:\Projects\Personal-AI-Employe-FTEs
scripts\setup-tasks.bat
```

5. **Press Enter**
6. **Wait for "Setup Complete!" message**
7. **Press any key to close**

---

### **Option B: Manual Commands (More Control)**

Open **Administrator Terminal** and run each command:

```batch
cd C:\Projects\Personal-AI-Employe-FTEs

schtasks /Create /TN "AI_Employee_Gmail_Watcher" /TR "python.exe '%CD%\scripts\gmail_watcher.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F

schtasks /Create /TN "AI_Employee_LinkedIn_Watcher" /TR "python.exe '%CD%\scripts\linkedin_watcher.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F

schtasks /Create /TN "AI_Employee_Orchestrator" /TR "python.exe '%CD%\scripts\orchestrator.py'" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
```

---

### **Verify Task Scheduler Setup**

To check if tasks were created:

```bash
# List all AI Employee tasks
schtasks /Query | findstr "AI_Employee"

# Or open Task Scheduler GUI
taskschd.msc
```

In Task Scheduler:
1. Click "Task Scheduler Library" on the left
2. Look for these tasks:
   - `AI_Employee_Gmail_Watcher`
   - `AI_Employee_LinkedIn_Watcher`
   - `AI_Employee_Orchestrator`

---

### **Task Scheduler Commands**

| Command | What It Does |
|---------|--------------|
| `schtasks /Query \| findstr "AI_Employee"` | Lists all AI Employee tasks |
| `schtasks /Run /TN "AI_Employee_Gmail_Watcher"` | Run Gmail watcher now |
| `schtasks /End /TN "AI_Employee_Gmail_Watcher"` | Stop Gmail watcher |
| `schtasks /Delete /TN "AI_Employee_Gmail_Watcher" /F` | Delete Gmail watcher task |

---

## 📖 PART 3: Testing Your AI Employee

### **Test 1: File System Watcher**

1. **Create a test file:**
   - Open Notepad
   - Type: "This is a test file for AI Employee"
   - Save as: `C:\Projects\Personal-AI-Employe-FTEs\personal-ai-employee\Inbox\test.txt`

2. **Wait 5 seconds**

3. **Check if it was detected:**
   ```bash
   pm2 logs filesystem-watcher
   ```

4. **Look for:**
   ```
   New file detected: test.txt
   Created action file: FILE_abc123.md
   ```

5. **Check Needs_Action folder:**
   ```bash
   dir C:\Projects\Personal-AI-Employe-FTEs\personal-ai-employee\Needs_Action
   ```

---

### **Test 2: Gmail Watcher** (If you have Gmail setup)

1. **Send yourself an email** from another account
   - Subject: "Test Email"
   - Body: "Testing AI Employee"

2. **Wait 2 minutes** (Gmail checks every 2 min)

3. **Check logs:**
   ```bash
   pm2 logs gmail-watcher
   ```

4. **Look for:**
   ```
   Found 1 new email(s)
   Created action file: EMAIL_abc123.md
   ```

---

### **Test 3: Orchestrator Processing**

1. **Check if orchestrator is processing:**
   ```bash
   pm2 logs orchestrator
   ```

2. **Look for (every 30 seconds):**
   ```
   Starting processing cycle
   Found X pending items
   Processing cycle complete
   ```

---

## 📖 PART 4: Daily Usage

### **Morning Check (Takes 30 seconds)**

1. **Check status:**
   ```bash
   pm2 status
   ```
   All should show "online"

2. **Check for pending approvals:**
   ```bash
   dir C:\Projects\Personal-AI-Employe-FTEs\personal-ai-employee\Pending_Approval
   ```
   If any files exist, review and approve/reject them

3. **Check recent logs:**
   ```bash
   pm2 logs --lines 50
   ```

---

### **Evening Check (Takes 1 minute)**

1. **Check what was processed today:**
   ```bash
   dir C:\Projects\Personal-AI-Employe-FTEs\personal-ai-employee\Done
   ```

2. **Review completed tasks**

---

## 📖 PART 5: Troubleshooting

### **Problem: PM2 Not Running**

**Symptoms:**
- `pm2 status` shows empty list
- Processes show "stopped"

**Solution:**
```bash
# Start everything
pm2 start ecosystem.config.cjs

# Verify
pm2 status
```

---

### **Problem: Processes Keep Crashing**

**Symptoms:**
- Status shows "errored"
- Restart count (↺) keeps increasing

**Solution:**
```bash
# View error logs
pm2 logs --err

# Restart all
pm2 restart all

# If still failing, check Python dependencies
cd C:\Projects\Personal-AI-Employe-FTEs
pip install -r requirements.txt
```

---

### **Problem: Emails Not Being Detected**

**Check:**
```bash
# 1. Check Gmail watcher logs
pm2 logs gmail-watcher

# 2. Check if credentials exist
dir credentials.json

# 3. Check if token exists
dir token.pickle
```

**If credentials missing:**
```bash
python scripts\gmail_auth.py
```

---

### **Problem: Duplicate Approvals Being Created**

This was fixed! But if it happens:

```bash
# 1. Stop orchestrator
pm2 stop orchestrator

# 2. Clean up duplicates
cd C:\Projects\Personal-AI-Employe-FTEs
python -c "from pathlib import Path; pa = Path('personal-ai-employee/Pending_Approval'); [f.unlink() for f in pa.glob('APPROVAL_*.md')]"

# 3. Restart orchestrator
pm2 restart orchestrator
```

---

## 📖 PART 6: Quick Reference Card

### **Essential Commands**

```bash
# Check if running
pm2 status

# View logs
pm2 logs

# Restart everything
pm2 restart all

# Stop everything
pm2 stop all

# Start everything
pm2 start all
```

### **Folders to Watch**

| Folder | What's Here |
|--------|-------------|
| `personal-ai-employee\Needs_Action\` | New items to process |
| `personal-ai-employee\Pending_Approval\` | Awaiting your approval |
| `personal-ai-employee\Approved\` | Approved, will be processed |
| `personal-ai-employee\Done\` | Completed items |
| `logs\` | All log files |

---

## 📖 PART 7: What Happens When

### **When Email Arrives:**

1. Gmail Watcher detects it (within 2 minutes)
2. Creates `EMAIL_*.md` in `Needs_Action/`
3. Orchestrator picks it up (within 30 seconds)
4. Qwen AI processes it
5. Creates approval in `Pending_Approval/`
6. You review and move to `Approved/`
7. Orchestrator sends email
8. Moves to `Done/`

---

### **When File Dropped in Inbox:**

1. File System Watcher detects it (instant)
2. Creates `FILE_*.md` in `Needs_Action/`
3. Orchestrator picks it up (within 30 seconds)
4. Processes according to Company Handbook
5. Moves to appropriate folder

---

### **When LinkedIn Notification:**

1. LinkedIn Watcher detects it (within 5 minutes)
2. Creates `LINKEDIN_*.md` in `Needs_Action/`
3. Orchestrator picks it up (within 30 seconds)
4. Qwen AI drafts response/post
5. Creates approval in `Pending_Approval/`
6. You review and approve
7. Posts to LinkedIn

---

## ✅ Checklist for Complete Setup

- [x] PM2 installed
- [x] PM2 processes running
- [ ] Windows Task Scheduler configured (optional)
- [ ] Test file dropped in Inbox
- [ ] Verified file was detected
- [ ] Checked Pending_Approval folder
- [ ] Saved PM2 process list (`pm2 save`)

---

## 🎯 Next Steps

1. **Save PM2 processes** (so they restart on reboot):
   ```bash
   pm2 save
   ```

2. **Setup Task Scheduler** (optional, for auto-start on boot):
   - Run `scripts\setup-tasks.bat` as Administrator

3. **Test the system**:
   - Drop a file in `Inbox/`
   - Watch it get processed

4. **Check back in 1 hour**:
   - See what was processed
   - Review `Done/` folder

---

**You're all set! Your AI Employee is working 24/7!** 🎉

For more details, see: `SILVER_TIER_VERIFICATION.md`
