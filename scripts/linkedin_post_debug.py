"""
LinkedIn Post - Debug Version

This version takes screenshots at each step to help debug the posting flow.
Run this to see exactly what's happening in the browser.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('LinkedIn Debug')


def debug_linkedin_post():
    """Debug LinkedIn post flow with screenshots."""
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'
    session_path = project_root / 'linkedin_session'
    debug_path = vault_path / 'Debug'
    debug_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("LinkedIn Post - DEBUG MODE")
    print("=" * 70)
    print()
    
    # Sample post content
    content = """🚀 Exciting News!

Testing LinkedIn automation with Kilo AI.

#AI #Automation #Testing
"""

    with sync_playwright() as p:
        # Launch browser
        print("Opening browser with saved session...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            viewport={'width': 1280, 'height': 720},
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        screenshot_num = 0
        
        # Navigate to LinkedIn
        print("Navigating to LinkedIn...")
        page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        
        screenshot_num += 1
        page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_after_login.png'))
        print(f"✓ Screenshot {screenshot_num}: After login")
        
        # Check if logged in
        if 'login' in page.url.lower():
            print("✗ NOT LOGGED IN! Please login manually.")
            time.sleep(30)
            browser.close()
            return
        
        # Click "Start a post"
        print("Clicking 'Start a post'...")
        try:
            start_post = page.locator('button:has-text("Start a post")').first
            start_post.click()
            page.wait_for_timeout(3000)
            
            screenshot_num += 1
            page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_post_dialog.png'))
            print(f"✓ Screenshot {screenshot_num}: Post dialog opened")
        except Exception as e:
            print(f"⚠ Could not click Start a post: {e}")
        
        # Fill content
        print("Filling content...")
        try:
            editor = page.locator('div[contenteditable="true"]').first
            editor.click()
            page.wait_for_timeout(1000)
            page.keyboard.type(content)
            page.wait_for_timeout(2000)
            
            screenshot_num += 1
            page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_content_filled.png'))
            print(f"✓ Screenshot {screenshot_num}: Content filled")
        except Exception as e:
            print(f"⚠ Could not fill content: {e}")
        
        # Click Post button
        print("Clicking 'Post' button...")
        try:
            post_btn = page.locator('button:has-text("Post")').first
            post_btn.click()
            page.wait_for_timeout(3000)
            
            screenshot_num += 1
            page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_after_first_post.png'))
            print(f"✓ Screenshot {screenshot_num}: After first Post click")
        except Exception as e:
            print(f"⚠ Could not click Post: {e}")
        
        # Check for audience selector
        print("Checking for audience selector...")
        page.wait_for_timeout(3000)
        
        try:
            # Look for "Anyone" text
            anyone = page.locator('text="Anyone"').first
            if anyone.is_visible(timeout=2000):
                print("✓ Found 'Anyone' option")
                anyone.click()
                page.wait_for_timeout(2000)
                
                screenshot_num += 1
                page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_audience_selected.png'))
                print(f"✓ Screenshot {screenshot_num}: Anyone selected")
                
                # Click Done
                print("Clicking 'Done'...")
                done_btn = page.locator('button:has-text("Done")').first
                done_btn.click()
                page.wait_for_timeout(3000)
                
                screenshot_num += 1
                page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_after_done.png'))
                print(f"✓ Screenshot {screenshot_num}: After Done click")
        except Exception as e:
            print(f"⚠ Audience selector issue: {e}")
        
        # Final Post button
        print("Looking for final Post button...")
        page.wait_for_timeout(2000)
        
        try:
            final_post = page.locator('button:has-text("Post")').first
            final_post.click()
            page.wait_for_timeout(5000)
            
            screenshot_num += 1
            page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_final_post.png'))
            print(f"✓ Screenshot {screenshot_num}: Final Post clicked")
        except Exception as e:
            print(f"⚠ Final Post issue: {e}")
        
        # Wait and check result
        print("Waiting for confirmation...")
        page.wait_for_timeout(8000)
        
        screenshot_num += 1
        page.screenshot(path=str(debug_path / f'{screenshot_num:03d}_final_result.png'))
        print(f"✓ Screenshot {screenshot_num}: Final result")
        
        print()
        print("=" * 70)
        print(f"DEBUG COMPLETE - Check screenshots in: {debug_path}")
        print("=" * 70)
        print()
        print("Review the screenshots to see where the flow breaks.")
        print("Share the screenshots for further debugging.")
        
        browser.close()


if __name__ == '__main__':
    debug_linkedin_post()
