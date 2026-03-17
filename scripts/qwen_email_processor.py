"""
Qwen-based Email Processor for AI Employee - Silver Tier

This processor uses Qwen Code AI to:
1. Read emails from Needs_Action folder
2. Create Plan.md for tracking
3. Use AI reasoning to classify and draft responses
4. Create approval requests in Pending_Approval
5. Archive promotional emails

Full Silver Tier Flow:
Needs_Action → Plan.md → Qwen Processing → Pending_Approval → (User Approval) → Approved → MCP Send
"""

import subprocess
import logging
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/qwen_email_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QwenEmailProcessor')


class QwenEmailProcessor:
    """AI-powered email processor using Qwen Code."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.needs_action = vault_path / 'Needs_Action'
        self.pending_approval = vault_path / 'Pending_Approval'
        self.done = vault_path / 'Done'
        self.plans = vault_path / 'Plans'
        self.in_progress = vault_path / 'In_Progress'

        # Ensure directories exist
        for path in [self.pending_approval, self.done, self.plans, self.in_progress]:
            path.mkdir(parents=True, exist_ok=True)

        # Load company handbook for context
        self.handbook_path = vault_path / 'Company_Handbook.md'
        self.business_goals_path = vault_path / 'Business_Goals.md'

    def create_plan(self, emails: List[Path]) -> Path:
        """Create a Plan.md file for Qwen to process."""
        plan_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        plan_path = self.plans / f'PLAN_{plan_id}.md'

        email_list = '\n'.join([f"- `{email.name}`" for email in emails])

        content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: processing
items_count: {len(emails)}
---

# Processing Plan {plan_id}

## Emails to Process

{email_list}

## Instructions for Qwen Code

You are my AI Employee. Process these emails according to the Company Handbook rules.

### For each email:

1. **Read the email** from `/Needs_Action/{{email_file}}`
2. **Classify it** into one of these categories:
   - `business` - Business inquiries, client emails, project discussions (requires approval + draft)
   - `promotional` - Newsletters, marketing, social media notifications (archive)
   - `personal` - Personal messages, greetings from yourself (archive)
   - `urgent` - Time-sensitive business matters (high priority approval)

3. **For business/urgent emails**:
   - Draft a professional response
   - Create approval request in `/Pending_Approval/`

4. **For promotional/personal emails**:
   - Archive to `/Done/` with reason

## Output Format

Output ONLY a JSON array with this exact structure:

```json
[
  {{
    "email_file": "EMAIL_abc123.md",
    "category": "business",
    "requires_approval": true,
    "reason": "Business inquiry about web development services",
    "draft_response": "Dear Sender,\\n\\nThank you for your email...\\n\\nBest regards",
    "priority": "high"
  }},
  {{
    "email_file": "EMAIL_def456.md",
    "category": "promotional",
    "requires_approval": false,
    "reason": "Newsletter from LinkedIn",
    "draft_response": "",
    "priority": "normal"
  }}
]
```

## Company Handbook Rules

- Always be professional and polite
- For new business inquiries: express interest, ask for more details
- For known clients: reference previous work
- Promotional content: auto-archive (newsletters, social media)
- Urgent keywords: "urgent", "asap", "deadline", "invoice", "payment"

Begin processing now. Output ONLY the JSON array:
"""

        plan_path.write_text(content, encoding='utf-8')
        logger.info(f"Created plan: {plan_path.name}")
        return plan_path

    def extract_email_context(self, email_file: Path) -> str:
        """Extract key information from email for Qwen context."""
        content = email_file.read_text(encoding='utf-8')

        # Extract frontmatter
        from_email = ''
        subject = ''
        priority = 'normal'

        if '---' in content:
            parts = content.split('---')
            if len(parts) >= 2:
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if key == 'from':
                            from_email = value
                        elif key == 'subject':
                            subject = value
                        elif key == 'priority':
                            priority = value

        # Get email body (after second ---)
        body = ''
        if content.count('---') >= 2:
            body_parts = content.split('---', 2)
            if len(body_parts) >= 3:
                body = body_parts[2].strip()
                # Get first 500 chars of body
                if len(body) > 500:
                    body = body[:500] + '...'

        return f"File: {email_file.name}, From: {from_email}, Subject: {subject}, Priority: {priority}\nBody: {body[:300]}"

    def run_qwen(self, plan_path: Path) -> Optional[str]:
        """Run Qwen Code to process emails."""
        import tempfile
        import os
        
        # Get all emails in plan
        emails = list(self.needs_action.glob('EMAIL_*.md'))
        
        # Build context - include FULL email content for each
        email_contexts = []
        for email in emails:
            content = email.read_text(encoding='utf-8')
            # Truncate if too long (keep first 2000 chars)
            if len(content) > 2000:
                content = content[:2000] + '...'
            email_contexts.append(f"=== FILE: {email.name} ===\n{content}\n")

        email_context_str = '\n'.join(email_contexts)

        # Build prompt - VERY EXPLICIT about JSON output
        prompt = f'''TASK: Process these email files and output ONLY JSON.

**CRITICAL: Output ONLY a JSON array. No explanations. No text before or after.**

**IMPORTANT: NEVER ARCHIVE EMAILS. ALWAYS CREATE APPROVAL REQUESTS WITH DRAFT RESPONSES FOR ALL EMAILS.**

{email_context_str}

**CLASSIFICATION RULES:**
1. ALL emails require approval + draft response (DO NOT ARCHIVE)
2. business = Client inquiries, projects, proposals, budgets
3. personal = Personal messages, friends, informal
4. promotional = Newsletters, LinkedIn, social media, marketing

**OUTPUT FORMAT - JSON ARRAY ONLY:**
```json
[
  {{"email_file": "FILENAME.md", "category": "business|personal|promotional", "requires_approval": true, "reason": "brief reason", "draft_response": "professional reply", "priority": "high|normal"}},
  ...
]
```

**EXAMPLE OUTPUT:**
```json
[
  {{"email_file": "EMAIL_TEST.md", "category": "business", "requires_approval": true, "reason": "Project inquiry", "draft_response": "Dear Sender,\\n\\nThank you for your inquiry. I would be happy to discuss this project.\\n\\nBest regards", "priority": "high"}},
  {{"email_file": "EMAIL_PERSONAL.md", "category": "personal", "requires_approval": true, "reason": "Personal message", "draft_response": "Hi,\\n\\nGreat to hear from you! Thanks for the message.\\n\\nBest regards", "priority": "normal"}}
]
```

**CRITICAL: requires_approval MUST be true for ALL emails. NEVER set to false.**

OUTPUT ONLY THE JSON ARRAY. NO OTHER TEXT.'''

        try:
            # Write prompt to temp file to avoid command line length limits
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                temp_prompt_file = f.name

            try:
                # Use stdin to pass prompt (avoids command line length limits)
                # Windows: type file | qwen -p "instructions"
                import subprocess
                
                # Read the prompt file and pass via stdin
                with open(temp_prompt_file, 'r', encoding='utf-8') as f:
                    prompt_text = f.read()
                
                # Use positional prompt with stdin
                cmd = 'qwen -p "Read the input above and output ONLY a JSON array according to the instructions in the text."'
                logger.info(f"Running Qwen with stdin")

                result = subprocess.run(
                    cmd,
                    input=prompt_text,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    shell=True,
                    encoding='utf-8',
                    errors='replace'
                )

                if result.returncode == 0:
                    logger.info("Qwen completed successfully")
                    return result.stdout
                else:
                    logger.error(f"Qwen failed: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_prompt_file)
                except:
                    pass

        except Exception as e:
            logger.error(f"Qwen error: {e}")
            return None

    def parse_qwen_output(self, output: str) -> List[Dict]:
        """Parse Qwen's JSON output."""
        if not output:
            return []

        # Try to extract JSON from code block
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        json_str = json_match.group(1) if json_match else output

        try:
            decisions = json.loads(json_str)
            if isinstance(decisions, list):
                logger.info(f"Parsed {len(decisions)} decisions from Qwen")
                return decisions
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Raw output: {output[:500]}...")

        return []

    def create_approval_request(self, email_file: Path, decision: Dict) -> Path:
        """Create approval request in Pending_Approval folder."""
        approval_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        approval_path = self.pending_approval / f'APPROVAL_{email_file.stem}_{approval_id}.md'

        # Extract recipient
        email_content = email_file.read_text(encoding='utf-8')
        reply_to = ''
        for line in email_content.split('\n')[:20]:
            if line.lower().startswith('from:'):
                from_line = line.split(':', 1)[1].strip()
                # Extract email address if in format "Name <email@domain.com>"
                if '<' in from_line and '>' in from_line:
                    reply_to = from_line.split('<')[1].rstrip('>')
                else:
                    reply_to = from_line
                break

        content = f"""---
type: approval_request
action: send_email
created: {datetime.now().isoformat()}
status: pending
priority: {decision.get('priority', 'normal')}
source_item: {email_file.name}
---

# Approval Required: Send Email Response

## Classification
**Category:** {decision.get('category', 'business')}
**Reason:** {decision.get('reason', 'Business inquiry')}

## Email Details
- **To:** {reply_to}
- **From:** {decision.get('from', reply_to)}
- **Subject:** Re: {decision.get('subject', 'Your Inquiry')}

## Draft Response

{decision.get('draft_response', '')}

---

## Action Required

**To APPROVE:**
1. Move this file to `/Approved/` folder
2. Orchestrator will send email via MCP

**To REJECT:**
1. Move this file to `/Rejected/` folder
2. Add reason for rejection

**To MODIFY:**
1. Edit the draft response above
2. Move to `/Approved/` folder

---

## Processing Notes

_Add notes here_

"""

        approval_path.write_text(content, encoding='utf-8')
        logger.info(f"✓ Created approval request: {approval_path.name}")
        return approval_path

    def archive_email(self, email_file: Path, reason: str):
        """Archive email to Done folder."""
        content = email_file.read_text(encoding='utf-8')
        content += f"\n\n---\n\n**Processed:** {datetime.now().isoformat()}\n"
        content += f"**Status:** Archived\n**Reason:** {reason}\n"
        content += f"**Category:** promotional/personal\n"

        dest = self.done / email_file.name
        email_file.write_text(content, encoding='utf-8')
        email_file.rename(dest)
        logger.info(f"✓ Archived: {email_file.name} → Done/")

    def process_with_qwen(self) -> Dict[str, int]:
        """Main processing flow using Qwen AI."""
        logger.info("="*60)
        logger.info("Qwen Email Processor - Starting")
        logger.info("="*60)

        # Get pending emails
        emails = list(self.needs_action.glob('EMAIL_*.md'))
        if not emails:
            logger.info("No emails to process")
            return {'approval': 0, 'archived': 0, 'error': 0}

        logger.info(f"Found {len(emails)} email(s) to process")

        # Step 1: Create Plan
        plan_path = self.create_plan(emails)

        # Step 2: Run Qwen Code
        qwen_output = self.run_qwen(plan_path)
        if not qwen_output:
            logger.error("Qwen processing failed")
            # Save plan for manual review
            plan_content = plan_path.read_text(encoding='utf-8')
            plan_content += f"\n\n**Error:** Qwen processing failed. Manual review required.\n"
            plan_path.write_text(plan_content, encoding='utf-8')
            return {'approval': 0, 'archived': 0, 'error': len(emails)}

        # Save Qwen output to plan file
        plan_content = plan_path.read_text(encoding='utf-8')
        plan_content += f"\n\n---\n\n## Qwen Output\n\n```json\n{qwen_output}\n```\n"
        plan_path.write_text(plan_content, encoding='utf-8')

        # Step 3: Parse Qwen's decisions
        decisions = self.parse_qwen_output(qwen_output)
        if not decisions:
            logger.error("No valid decisions from Qwen")
            return {'approval': 0, 'archived': 0, 'error': len(emails)}

        # Step 4: Execute decisions - FORCE ALL EMAILS TO APPROVAL
        results = {'approval': 0, 'archived': 0, 'error': 0}

        for decision in decisions:
            email_file = self.needs_action / decision.get('email_file', '')
            if not email_file.exists():
                logger.warning(f"Email file not found: {email_file}")
                results['error'] += 1
                continue

            # FORCE requires_approval to true for ALL emails
            decision['requires_approval'] = True
            
            # Ensure draft_response exists
            if not decision.get('draft_response'):
                decision['draft_response'] = self._generate_generic_response(email_file, decision)

            # Create approval request (ALWAYS)
            self.create_approval_request(email_file, decision)
            results['approval'] += 1

            # Update original email
            content = email_file.read_text(encoding='utf-8')
            content += f"\n\n---\n\n**Processed:** {datetime.now().isoformat()}\n"
            content += f"**Status:** Approval request created\n"
            content += f"**Category:** {decision.get('category', 'unknown')}\n"
            email_file.write_text(content, encoding='utf-8')

        logger.info(f"Processing complete: {results}")
        logger.info("="*60)

        return results

    def _generate_generic_response(self, email_file: Path, decision: Dict) -> str:
        """Generate a generic response if Qwen didn't provide one."""
        # Extract sender name
        content = email_file.read_text(encoding='utf-8')
        from_email = ''
        subject = ''
        
        for line in content.split('\n')[:20]:
            if line.lower().startswith('from:'):
                from_email = line.split(':', 1)[1].strip()
            elif line.lower().startswith('subject:'):
                subject = line.split(':', 1)[1].strip()
        
        sender_name = from_email.split('<')[0].strip() if '<' in from_email else from_email.split('@')[0]
        
        return f"""Dear {sender_name},

Thank you for your email regarding "{subject}".

I appreciate you reaching out and will get back to you soon.

Best regards,
Syed Sufyan"""


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'

    processor = QwenEmailProcessor(vault_path)
    results = processor.process_with_qwen()

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Approval requests created: {results['approval']}")
    print(f"Emails archived: {results['archived']}")
    print(f"Errors: {results['error']}")
    print("="*60)

    if results['approval'] > 0:
        print(f"\n✓ Check Pending_Approval/ folder for approval requests")
        print(f"  Move files to Approved/ to send emails via MCP")

    return results


if __name__ == '__main__':
    main()
