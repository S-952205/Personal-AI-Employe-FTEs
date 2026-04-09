---
name: ralph-wiggum
description: Autonomous multi-step task completion loop with stop hook pattern
version: 1.0.0
---

# Ralph Wiggum Loop - Autonomous Task Completion

The Ralph Wiggum pattern keeps the AI Employee working autonomously until tasks are complete by intercepting exit attempts and re-injecting prompts.

## How It Works

```
┌─────────────────┐
│ 1. Create State │───▶ State file in /In_Progress/
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Run AI Agent │───▶ Process task
└────────┬────────┘
         ▼
┌─────────────────────┐
│ 3. Check Completion │───▶ Done? ──YES──▶ Exit
└────────┬────────────┘
         │ NO
         ▼
┌──────────────────────┐
│ 4. Re-inject Prompt  │───▶ Loop to step 2
└──────────────────────┘
```

## Quick Start

### CLI Usage

```bash
# Basic usage
python scripts/ralph_wiggum.py --prompt "Process all items in Needs_Action"

# With custom settings
python scripts/ralph_wiggum.py \
  --prompt "Process all emails and create approval requests" \
  --max-iterations 15 \
  --completion-promise "TASK_COMPLETE" \
  --vault-path /path/to/vault
```

### Python API Usage

```python
from pathlib import Path
from ralph_wiggum import RalphWiggumLoop

vault = Path('/path/to/personal-ai-employee')

loop = RalphWiggumLoop(
    vault_path=vault,
    prompt="Process all items in Needs_Action folder",
    max_iterations=10,
    completion_promise="TASK_COMPLETE"
)

success = loop.run()
if success:
    print("✅ Task completed!")
else:
    print("⚠️ Max iterations reached")
```

### Integration with Orchestrator

```python
from ralph_wiggum import create_state_file, check_task_complete

# Create state file to trigger autonomous processing
create_state_file(vault, "Process pending approvals and execute approved actions")

# Check if task is complete (used by stop hook)
if check_task_complete(vault):
    print("Task complete, allowing exit")
else:
    print("Task incomplete, blocking exit")
```

## Completion Detection Strategies

The loop checks for completion using multiple strategies (in order):

1. **Completion Promise**: Exact string match in output (e.g., `TASK_COMPLETE`)
2. **Promise Tag**: `<promise>TASK_COMPLETE</promise>` in output
3. **Completion File**: File exists at specified pattern
4. **Empty Queue**: No items left in `/Needs_Action/`

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prompt` | (required) | Task prompt for AI agent |
| `--vault-path` | `../personal-ai-employee` | Path to Obsidian vault |
| `--max-iterations` | 10 | Maximum retry attempts |
| `--completion-promise` | `TASK_COMPLETE` | String to look for in output |
| `--completion-file` | None | File pattern for completion check |
| `--qwen-command` | `qwen` | Command to run AI agent |

## State File Format

State files are created in `/In_Progress/RALPH_STATE_*.md`:

```yaml
---
type: ralph_wiggum_state
iteration: 3
max_iterations: 10
status: in_progress
started: 2026-04-05T10:30:00
prompt: Process all items in Needs_Action
---
```

Status values:
- `pending` - Waiting to start
- `in_progress` - Currently processing
- `completed` - Task finished successfully
- `max_iterations_reached` - Failed to complete

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Infinite loop | Reduce `--max-iterations`, check completion criteria |
| AI agent not running | Verify `--qwen-command` works: `qwen --version` |
| Task never completes | Make prompt more specific, increase max iterations |
| State files not created | Check vault path exists and is writable |

## Advanced: Stop Hook Integration

For Claude Code integration, add a stop hook that checks task completion:

```bash
# In .claude/settings.json or CLAUDE_SETTINGS_PATH
{
  "stop_hook": {
    "enabled": true,
    "script": "scripts/ralph_wiggum.py --check-completion /path/to/vault"
  }
}
```

The stop hook:
1. Intercepts Claude's exit attempt
2. Checks if task file is in `/Done/`
3. If NO → Block exit, re-inject prompt
4. If YES → Allow exit
