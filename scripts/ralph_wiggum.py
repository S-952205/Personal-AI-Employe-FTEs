"""
Ralph Wiggum Loop - Gold Tier

Implements the Stop hook pattern that keeps the AI Employee working autonomously
until tasks are complete. Intercepts exit attempts and re-injects prompts until
completion criteria are met.

Usage:
    python ralph_wiggum.py --prompt "Process all items in Needs_Action" \
                           --max-iterations 10 \
                           --completion-promise "TASK_COMPLETE"
"""

import subprocess
import logging
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ralph_wiggum.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RalphWiggum')


class RalphWiggumLoop:
    """
    Autonomous task completion loop using the Ralph Wiggum pattern.
    
    How it works:
    1. Create state file with prompt
    2. Run AI agent on task
    3. Check if task is complete (file in /Done/ OR promise in output)
    4. If complete -> exit
    5. If not complete -> re-inject prompt with state update, loop continues
    """

    def __init__(
        self,
        vault_path: Path,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: Optional[str] = None,
        completion_file_pattern: Optional[str] = None,
        kilo_command: str = "kilo"
    ):
        self.vault_path = vault_path
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.completion_file_pattern = completion_file_pattern
        self.kilo_command = kilo_command
        self.current_iteration = 0
        self.state_file = self.vault_path / 'In_Progress' / 'ralph_wiggum_state.md'

    def run(self) -> bool:
        """
        Main loop. Returns True if task completed, False if max iterations reached.
        """
        logger.info(f"🔄 Starting Ralph Wiggum Loop")
        logger.info(f"   Prompt: {self.prompt[:100]}...")
        logger.info(f"   Max iterations: {self.max_iterations}")
        logger.info(f"   Completion promise: {self.completion_promise}")

        # Ensure In_Progress directory exists
        (self.vault_path / 'In_Progress').mkdir(parents=True, exist_ok=True)

        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            logger.info(f"\n{'='*60}")
            logger.info(f"📍 Iteration {iteration}/{self.max_iterations}")
            logger.info(f"{'='*60}")

            # Update state file
            self._update_state_file(iteration)

            # Build prompt with iteration context
            iteration_prompt = self._build_iteration_prompt(iteration)

            # Run AI agent
            output = self._run_ai_agent(iteration_prompt)

            # Check completion
            if self._check_completion(output):
                logger.info(f"\n✅ Task completed on iteration {iteration}!")
                self._update_state_file(iteration, status="completed")
                return True

            # Check for max iterations
            if iteration == self.max_iterations:
                logger.warning(f"\n⚠️ Max iterations ({self.max_iterations}) reached!")
                self._update_state_file(iteration, status="max_iterations_reached")
                return False

            # Not complete, will retry
            logger.info(f"⏳ Task not complete, retrying...")
            time.sleep(2)  # Brief pause before next iteration

        return False

    def _update_state_file(self, iteration: int, status: str = "in_progress"):
        """Update state file with current progress."""
        content = f"""---
type: ralph_wiggum_state
iteration: {iteration}
max_iterations: {self.max_iterations}
status: {status}
started: {datetime.now().isoformat()}
prompt: {self.prompt}
---

# Ralph Wiggum Loop State

## Current Status
- **Iteration:** {iteration}/{self.max_iterations}
- **Status:** {status}
- **Started:** {datetime.now().isoformat()}

## Original Prompt
{self.prompt}

## Iteration History
"""
        self.state_file.write_text(content, encoding='utf-8')

    def _build_iteration_prompt(self, iteration: int) -> str:
        """Build prompt with iteration context."""
        if iteration == 1:
            return self.prompt
        else:
            return f"""{self.prompt}

IMPORTANT: This is iteration {iteration}/{self.max_iterations}.
Previous attempts did not complete the task.

Please continue working on this task. When you are done:
1. Move all processed items to /Done/
2. Output: <promise>TASK_COMPLETE</promise>

Current state:
{self._get_current_state_summary()}
"""

    def _get_current_state_summary(self) -> str:
        """Get summary of current vault state."""
        needs_action = self.vault_path / 'Needs_Action'
        done = self.vault_path / 'Done'
        pending = self.vault_path / 'Pending_Approval'

        needs_count = len(list(needs_action.glob('*.md'))) if needs_action.exists() else 0
        done_count = len(list(done.glob('*.md'))) if done.exists() else 0
        pending_count = len(list(pending.glob('*.md'))) if pending.exists() else 0

        return f"""
- Items in Needs_Action: {needs_count}
- Items in Done: {done_count}
- Items Pending Approval: {pending_count}
"""

    def _run_ai_agent(self, prompt: str) -> str:
        """
        Run AI agent (Kilo Code) with the given prompt.
        Returns the output text.
        """
        logger.info(f"🤖 Running AI agent...")

        try:
            # Run Kilo Code with the prompt
            result = subprocess.run(
                [self.kilo_command, '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per iteration
                cwd=str(self.vault_path)
            )

            output = result.stdout
            if result.stderr:
                logger.warning(f"AI agent stderr: {result.stderr[:200]}")

            logger.info(f"✅ AI agent completed (exit code: {result.returncode})")
            return output

        except subprocess.TimeoutExpired:
            logger.error("⏰ AI agent timed out after 5 minutes")
            return "TIMEOUT"
        except FileNotFoundError:
            logger.error(f"❌ AI agent command not found: {self.kilo_command}")
            raise
        except Exception as e:
            logger.error(f"❌ AI agent error: {e}")
            return f"ERROR: {str(e)}"

    def _check_completion(self, output: str) -> bool:
        """
        Check if task is complete using multiple strategies:
        1. Completion promise in output
        2. Completion file pattern in vault
        3. No items left in Needs_Action (if applicable)
        """
        # Strategy 1: Check for completion promise
        if self.completion_promise and self.completion_promise in output:
            logger.info(f"✅ Found completion promise: {self.completion_promise}")
            return True

        # Strategy 2: Check for <promise>TASK_COMPLETE</promise> tag
        if '<promise>TASK_COMPLETE</promise>' in output:
            logger.info("✅ Found TASK_COMPLETE promise tag")
            return True

        # Strategy 3: Check completion file pattern
        if self.completion_file_pattern:
            pattern_path = self.vault_path / self.completion_file_pattern
            if pattern_path.exists():
                logger.info(f"✅ Found completion file: {self.completion_file_pattern}")
                return True

        # Strategy 4: Check if Needs_Action is empty (common pattern)
        needs_action = self.vault_path / 'Needs_Action'
        if needs_action.exists():
            pending_items = list(needs_action.glob('*.md'))
            if len(pending_items) == 0:
                logger.info("✅ No items left in Needs_Action")
                return True

        return False


def create_state_file(vault_path: Path, prompt: str) -> Path:
    """
    Helper function to create a state file for Ralph Wiggum loop.
    Used by orchestrator to trigger autonomous processing.
    """
    state_dir = vault_path / 'In_Progress'
    state_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    state_file = state_dir / f'RALPH_STATE_{timestamp}.md'

    content = f"""---
type: ralph_wiggum_state
created: {datetime.now().isoformat()}
status: pending
prompt: {prompt}
---

# Ralph Wiggum Autonomous Task

## Task
{prompt}

## Status
Waiting for orchestrator to trigger Ralph Wiggum loop.
"""
    state_file.write_text(content, encoding='utf-8')
    return state_file


def check_task_complete(vault_path: Path) -> bool:
    """
    Check if current Ralph Wiggum task is complete.
    Used by stop hook to decide whether to allow exit.
    """
    # Check for completion files in In_Progress
    in_progress = vault_path / 'In_Progress'
    if in_progress.exists():
        state_files = list(in_progress.glob('RALPH_STATE_*.md'))
        for state_file in state_files:
            content = state_file.read_text(encoding='utf-8')
            if 'status: completed' in content:
                return True

    # Check if Needs_Action is empty
    needs_action = vault_path / 'Needs_Action'
    if needs_action.exists():
        pending_items = list(needs_action.glob('*.md'))
        if len(pending_items) == 0:
            return True

    return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Ralph Wiggum Autonomous Loop')
    parser.add_argument(
        '--prompt',
        type=str,
        required=True,
        help='Task prompt for AI agent'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default=str(Path(__file__).parent.parent / 'personal-ai-employee'),
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum number of iterations (default: 10)'
    )
    parser.add_argument(
        '--completion-promise',
        type=str,
        default='TASK_COMPLETE',
        help='Completion promise string to look for'
    )
    parser.add_argument(
        '--completion-file',
        type=str,
        default=None,
        help='File pattern to check for completion'
    )
    parser.add_argument(
        '--kilo-command',
        type=str,
        default='kilo',
        help='Command to run Kilo Code (default: kilo)'
    )

    args = parser.parse_args()

    vault = Path(args.vault_path)
    if not vault.exists():
        logger.error(f"Vault path does not exist: {vault}")
        sys.exit(1)

    loop = RalphWiggumLoop(
        vault_path=vault,
        prompt=args.prompt,
        max_iterations=args.max_iterations,
        completion_promise=args.completion_promise,
        completion_file_pattern=args.completion_file,
        kilo_command=args.kilo_command
    )

    success = loop.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
