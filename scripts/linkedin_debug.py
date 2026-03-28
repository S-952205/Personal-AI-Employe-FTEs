"""
LinkedIn Debug Script - Find correct selectors

Run this to see what elements are available on your LinkedIn feed
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

project_root = Path(__file__).parent.parent.absolute()
session_path = project_root / 'linkedin_session'

print("Opening LinkedIn to find correct selectors...")

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(session_path),
        headless=False,
        viewport={'width': 1280, 'height': 720}
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("Navigating to LinkedIn...")
    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(10000)
    
    print("\n=== Looking for 'Start a post' button ===\n")
    
    # Try to find all buttons
    buttons = page.locator('button')
    count = buttons.count()
    print(f"Total buttons found: {count}")
    
    # Look for specific patterns
    selectors_to_try = [
        'button.share-box-feed-entry__trigger',
        'button:has-text("Start a post")',
        '[data-control-name="post-initiate"]',
        'div.share-box-feed-entry button',
        '.share-box-feed-entry__trigger',
        'button[aria-label*="post"]',
    ]
    
    for sel in selectors_to_try:
        try:
            elements = page.locator(sel)
            cnt = elements.count()
            if cnt > 0:
                print(f"\n✓ FOUND: {sel} ({cnt} elements)")
                # Get text of first element
                try:
                    text = elements.first.inner_text(timeout=2000)
                    print(f"  Text: {text[:50]}...")
                except:
                    pass
            else:
                print(f"✗ Not found: {sel}")
        except Exception as e:
            print(f"✗ Error: {sel} - {e}")
    
    print("\n=== Checking share-box-feed-entry div ===\n")
    
    try:
        share_box = page.locator('div.share-box-feed-entry')
        if share_box.count() > 0:
            print(f"✓ Found share-box-feed-entry ({share_box.count()} elements)")
            
            # Get all buttons inside
            buttons = share_box.first.locator('button')
            print(f"  Buttons inside: {buttons.count()}")
            
            for i in range(min(buttons.count(), 5)):
                try:
                    text = buttons.nth(i).inner_text(timeout=2000)
                    print(f"    Button {i}: {text}")
                except:
                    print(f"    Button {i}: (no text)")
        else:
            print("✗ share-box-feed-entry not found")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Manual inspection ===")
    print("\nKEEP THIS BROWSER OPEN")
    print("Go to LinkedIn and manually click 'Start a post'")
    print("Then come back and check what selectors worked")
    print("\nPress Ctrl+C when done...")
    
    try:
        time.sleep(300)  # Wait 5 minutes
    except KeyboardInterrupt:
        pass
    
    browser.close()
