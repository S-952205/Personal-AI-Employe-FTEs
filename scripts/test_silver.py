"""
Test script for Silver Tier implementation

This script verifies all Silver Tier components are properly set up:
1. Gmail Watcher with credentials
2. LinkedIn Watcher with Playwright
3. MCP Servers (Email + LinkedIn)
4. HITL Approval Workflow
5. Scheduling scripts
"""

import sys
import json
from pathlib import Path


def test_silver_tier():
    """Test the Silver Tier implementation."""
    # Get the vault path (personal-ai-employee folder)
    project_root = Path(__file__).parent.parent.resolve()
    vault_path = project_root / 'personal-ai-employee'

    # Set stdout to use UTF-8 encoding
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("SILVER TIER IMPLEMENTATION TEST")
    print("=" * 70)
    print(f"\nProject Root: {project_root}")
    print(f"Vault Path: {vault_path}")
    print()

    # Track test results
    tests_passed = 0
    tests_failed = 0

    # ========================================
    # Test 1: Required Vault Files
    # ========================================
    print("-" * 70)
    print("TEST 1: Required Vault Files")
    print("-" * 70)
    
    required_files = [
        'Dashboard.md',
        'Company_Handbook.md',
        'Business_Goals.md'
    ]

    for file in required_files:
        full_path = vault_path / file
        if full_path.exists():
            print(f"   [✓] {file}")
            tests_passed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    print()

    # ========================================
    # Test 2: Required Directories
    # ========================================
    print("-" * 70)
    print("TEST 2: Required Directories")
    print("-" * 70)
    
    required_dirs = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Plans',
        'Approved',
        'Rejected',
        'Accounting',
        'Briefings',
        'Pending_Approval',
        'In_Progress'
    ]

    for dir in required_dirs:
        full_path = vault_path / dir
        if full_path.exists() and full_path.is_dir():
            print(f"   [✓] /{dir}")
            tests_passed += 1
        else:
            print(f"   [✗] /{dir} - MISSING")
            tests_failed += 1
            # Create missing directory
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   [INFO] Created: /{dir}")
    print()

    # ========================================
    # Test 3: Watcher Scripts
    # ========================================
    print("-" * 70)
    print("TEST 3: Watcher Scripts")
    print("-" * 70)
    
    watcher_scripts = [
        'scripts/filesystem_watcher.py',
        'scripts/gmail_watcher.py',
        'scripts/linkedin_watcher.py',
        'scripts/orchestrator.py',
        'scripts/gmail_auth.py'
    ]

    for file in watcher_scripts:
        full_path = project_root / file
        if full_path.exists():
            print(f"   [✓] {file}")
            tests_passed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    print()

    # ========================================
    # Test 4: MCP Servers
    # ========================================
    print("-" * 70)
    print("TEST 4: MCP Servers")
    print("-" * 70)
    
    mcp_servers = [
        'mcp-servers/email-mcp/package.json',
        'mcp-servers/email-mcp/index.js',
        'mcp-servers/linkedin-mcp/package.json',
        'mcp-servers/linkedin-mcp/index.js'
    ]

    for file in mcp_servers:
        full_path = project_root / file
        if full_path.exists():
            print(f"   [✓] {file}")
            tests_passed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    print()

    # ========================================
    # Test 5: Configuration Files
    # ========================================
    print("-" * 70)
    print("TEST 5: Configuration Files")
    print("-" * 70)
    
    config_files = [
        'requirements.txt',
        'mcp-config.json',
        'README.md'
    ]

    for file in config_files:
        full_path = project_root / file
        if full_path.exists():
            print(f"   [✓] {file}")
            tests_passed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    
    # Check for credentials.json (optional but recommended)
    credentials_path = project_root / 'credentials.json'
    if credentials_path.exists():
        print(f"   [✓] credentials.json (Gmail credentials)")
        tests_passed += 1
    else:
        print(f"   [!] credentials.json - NOT FOUND (required for Gmail watcher)")
        print(f"       Please add your Gmail credentials.json to: {credentials_path}")
    print()

    # ========================================
    # Test 6: Helper Scripts
    # ========================================
    print("-" * 70)
    print("TEST 6: Helper Scripts")
    print("-" * 70)
    
    helper_scripts = [
        'scripts/start-all.bat',
        'scripts/setup-tasks.bat'
    ]

    for file in helper_scripts:
        full_path = project_root / file
        if full_path.exists():
            print(f"   [✓] {file}")
            tests_passed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    print()

    # ========================================
    # Test 7: Python Dependencies Check
    # ========================================
    print("-" * 70)
    print("TEST 7: Python Dependencies")
    print("-" * 70)
    
    dependencies = [
        ('watchdog', 'File system monitoring'),
        ('google.oauth2', 'Gmail OAuth2 authentication'),
        ('googleapiclient', 'Gmail API client'),
        ('playwright', 'Browser automation for LinkedIn'),
    ]

    for module, description in dependencies:
        try:
            __import__(module.replace('.', '_'))
            print(f"   [✓] {module} ({description})")
            tests_passed += 1
        except ImportError:
            print(f"   [✗] {module} - NOT INSTALLED ({description})")
            tests_failed += 1
    print()

    # ========================================
    # Test 8: Node.js Dependencies Check
    # ========================================
    print("-" * 70)
    print("TEST 8: Node.js Setup")
    print("-" * 70)
    
    import subprocess
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   [✓] Node.js installed: {result.stdout.strip()}")
            tests_passed += 1
        else:
            print(f"   [✗] Node.js not working")
            tests_failed += 1
    except FileNotFoundError:
        print(f"   [✗] Node.js - NOT INSTALLED (required for MCP servers)")
        tests_failed += 1
    except Exception as e:
        print(f"   [✗] Node.js check failed: {e}")
        tests_failed += 1
    
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   [✓] npm installed: {result.stdout.strip()}")
            tests_passed += 1
        else:
            print(f"   [✗] npm not working")
            tests_failed += 1
    except FileNotFoundError:
        print(f"   [✗] npm - NOT INSTALLED")
        tests_failed += 1
    except Exception as e:
        print(f"   [✗] npm check failed: {e}")
        tests_failed += 1
    print()

    # ========================================
    # Test 9: MCP Package.json Validation
    # ========================================
    print("-" * 70)
    print("TEST 9: MCP Package.json Validation")
    print("-" * 70)
    
    mcp_packages = [
        'mcp-servers/email-mcp/package.json',
        'mcp-servers/linkedin-mcp/package.json'
    ]

    for file in mcp_packages:
        full_path = project_root / file
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'name' in data and 'version' in data:
                    print(f"   [✓] {file} (valid: {data['name']} v{data['version']})")
                    tests_passed += 1
                else:
                    print(f"   [✗] {file} - Invalid structure")
                    tests_failed += 1
            except json.JSONDecodeError as e:
                print(f"   [✗] {file} - JSON parse error: {e}")
                tests_failed += 1
        else:
            print(f"   [✗] {file} - MISSING")
            tests_failed += 1
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests:  {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✓ ALL TESTS PASSED! Silver Tier is ready to use.")
        print()
        print("NEXT STEPS:")
        print("1. Install Node.js dependencies:")
        print(f"   cd {project_root}\\mcp-servers\\email-mcp && npm install")
        print(f"   cd {project_root}\\mcp-servers\\linkedin-mcp && npm install")
        print()
        print("2. Authenticate Gmail (if using Gmail watcher):")
        print("   python scripts/gmail_auth.py")
        print()
        print("3. Install Playwright browsers:")
        print("   playwright install")
        print()
        print("4. Start all watchers:")
        print("   scripts/start-all.bat")
        print()
    else:
        print("✗ SOME TESTS FAILED. Please fix the issues above.")
        print()
        print("QUICK FIXES:")
        print("1. Install Python dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print("2. Install Node.js dependencies:")
        print("   cd mcp-servers/email-mcp && npm install")
        print("   cd mcp-servers/linkedin-mcp && npm install")
        print()
        print("3. Add Gmail credentials.json to project root")
        print()

    print("=" * 70)

    return tests_failed == 0


if __name__ == '__main__':
    success = test_silver_tier()
    sys.exit(0 if success else 1)
