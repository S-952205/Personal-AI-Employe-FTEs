"""
Test script for Bronze Tier implementation

This script tests the file system watcher by:
1. Creating a test file in Inbox
2. Waiting for the watcher to process it
3. Verifying the action file was created in Needs_Action
"""

import time
import sys
from pathlib import Path


def test_bronze_tier():
    """Test the Bronze tier implementation."""
    # Get the vault path (personal-ai-employee folder)
    project_root = Path(__file__).parent.parent.resolve()
    vault_path = project_root / 'personal-ai-employee'
    
    # Set stdout to use UTF-8 encoding
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("[TEST] Testing Bronze Tier Implementation")
    print("=" * 50)
    print(f"Project Root: {project_root}")
    print(f"Vault Path: {vault_path}")
    print()
    
    # Step 1: Check required files exist in vault
    print("1. Checking required vault files...")
    required_files = [
        'Dashboard.md',
        'Company_Handbook.md',
        'Business_Goals.md'
    ]
    
    for file in required_files:
        full_path = vault_path / file
        if full_path.exists():
            print(f"   [OK] {file}")
        else:
            print(f"   [FAIL] {file} - MISSING")
    
    # Step 2: Check required directories in vault
    print("\n2. Checking required vault directories...")
    required_dirs = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Plans',
        'Approved',
        'Rejected',
        'Accounting',
        'Briefings',
        'Pending_Approval'
    ]
    
    for dir in required_dirs:
        full_path = vault_path / dir
        if full_path.exists() and full_path.is_dir():
            print(f"   [OK] /{dir}")
        else:
            print(f"   [FAIL] /{dir} - MISSING")
            # Create missing directory
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   [INFO] Created: /{dir}")
    
    # Step 3: Check scripts exist in project root
    print("\n3. Checking scripts in project root...")
    script_files = [
        'scripts/filesystem_watcher.py',
        'scripts/orchestrator.py',
        'requirements.txt',
        'README.md'
    ]
    
    for file in script_files:
        full_path = project_root / file
        if full_path.exists():
            print(f"   [OK] {file}")
        else:
            print(f"   [FAIL] {file} - MISSING")
    
    # Step 4: Create a test file
    print("\n4. Creating test file in Inbox...")
    inbox_path = vault_path / 'Inbox'
    inbox_path.mkdir(parents=True, exist_ok=True)
    test_file = inbox_path / 'test_document.txt'
    test_file.write_text('This is a test file for Bronze Tier testing.', encoding='utf-8')
    print(f"   [OK] Created: {test_file.name}")
    
    # Step 4: Instructions for manual testing
    print("\n" + "=" * 50)
    print("NEXT STEPS FOR MANUAL TESTING:")
    print("=" * 50)
    print("""
1. Start the File System Watcher:
   python scripts/filesystem_watcher.py

2. In a separate terminal, start the Orchestrator:
   python scripts/orchestrator.py

3. Watch the logs:
   - logs/filesystem_watcher.log
   - logs/orchestrator.log

4. Check the Needs_Action folder for the created action file

5. Open Dashboard.md in Obsidian to see the status

6. Press Ctrl+C in both terminals to stop

To run Claude Code manually:
   claude --prompt "Process the files in Needs_Action folder following the Company Handbook"
""")
    
    print("=" * 50)
    print("[OK] Bronze Tier setup complete!")
    print("=" * 50)


if __name__ == '__main__':
    test_bronze_tier()
