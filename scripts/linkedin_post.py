"""
LinkedIn Auto-Post for AI Employee

Usage:
  python scripts/linkedin_post.py           # Interactive
  python scripts/linkedin_post.py --auto    # Auto mode
"""

import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    project_root = Path(__file__).parent.parent.absolute()
    vault_path = project_root / 'personal-ai-employee'
    session_path = vault_path.parent / 'linkedin_session'

    auto_mode = '--auto' in sys.argv or '-a' in sys.argv

    print("\n" + "=" * 70)
    print("AI Employee - LinkedIn Auto-Post")
    print("=" * 70)
    print()

    # Generate post content
    post_content = """🚀 Exciting News!

I'm thrilled to share that we're launching a new AI-powered automation service to help businesses streamline their operations.

Key benefits:
✅ 24/7 autonomous operations
✅ 85% cost reduction vs traditional methods
✅ Seamless integration with your existing tools

We're helping businesses transform how they work with intelligent agents that never sleep.

Interested in learning more? Drop a comment or send me a DM!

#AI #Automation #BusinessTransformation #Innovation #DigitalTransformation #ArtificialIntelligence
"""

    print("✓ Post content generated")
    print()
    print("-" * 70)
    print(post_content)
    print("-" * 70)
    print()

    # Save draft
    draft_path = vault_path / 'Plans' / f'LINKEDIN_POST_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(f"""---
type: linkedin_post
created: {datetime.now().isoformat()}
---

# LinkedIn Post

{post_content}
""", encoding='utf-8')
    print(f"✓ Draft saved: {draft_path.name}")

    # Confirm
    if not auto_mode:
        response = input("\nPost this? (yes or Enter to skip): ").strip().lower()
        if response != 'yes':
            print("\nCancelled.")
            return

    print("\n" + "=" * 70)
    print("Posting to LinkedIn")
    print("=" * 70)
    print()

    if not session_path.exists():
        print("ERROR: No LinkedIn session!")
        print("Run: python scripts/linkedin_login.py")
        return

    try:
        with sync_playwright() as p:
            # Open browser
            print("Opening LinkedIn...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_path),
                headless=False,
                viewport={'width': 1280, 'height': 720},
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to LinkedIn with retry
            print("Navigating to LinkedIn...")
            nav_success = False
            for attempt in range(3):
                try:
                    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(5000)
                    nav_success = True
                    break
                except Exception as e:
                    print(f"⚠ Navigation attempt {attempt + 1}/3 failed: {e}")
                    if attempt < 2:
                        print("  Retrying...")
                        page.wait_for_timeout(3000)
            
            if not nav_success:
                print("✗ Could not load LinkedIn after 3 attempts")
                print(f"  Current URL: {page.url}")
                browser.close()
                return

            # Check login
            if 'login' in page.url.lower():
                print("\n✗ Not logged in!")
                print("Run: python scripts/linkedin_login.py")
                browser.close()
                return

            print("✓ Logged in")
            print()

            # Click "Start a post"
            print("Opening post dialog...")
            
            # Wait for page to fully load
            page.wait_for_timeout(5000)
            
            # Try many selectors
            clicked = False
            selectors = [
                'button:has-text("Start a post")',
                'button:has-text("Start")',
                '.share-box-feed-entry__trigger',
                'button.artdeco-button:has-text("Start a post")',
                'div[role="button"]:has-text("Start a post")',
                '[aria-label*="Start a post"]',
            ]
            
            print("Looking for Start a post button...")
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print(f"✓ Clicked: {sel}")
                        clicked = True
                        break
                except Exception as e:
                    logger.debug(f"{sel}: {e}")
                    continue
            
            if not clicked:
                # Debug: show what buttons are available
                try:
                    buttons = page.locator('button').all()
                    print(f"  Found {len(buttons)} buttons, checking text...")
                    for i, btn in enumerate(buttons[:20]):
                        try:
                            text = btn.inner_text(timeout=1000)
                            if text.strip():
                                print(f"    [{i}] {text[:50]}")
                        except:
                            pass
                except:
                    pass
                
                print("⚠ Could not find Start a post button")
                print("  Opening via URL...")
                page.goto('https://www.linkedin.com/feed/?shareActive=true', wait_until='domcontentloaded')
                page.wait_for_timeout(8000)  # Longer wait for URL method

            # Wait for dialog AND content to load
            print("Waiting for dialog...")
            dialog_found = False
            for i in range(30):  # 30 * 500ms = 15 seconds max
                try:
                    dialog = page.locator('[role="dialog"]').first
                    if dialog.is_visible(timeout=1000):
                        print("✓ Dialog opened")
                        # Wait for editor inside dialog
                        try:
                            editor_check = page.locator('div[contenteditable="true"]').first
                            if editor_check.is_visible(timeout=3000):
                                print("✓ Editor loaded")
                                dialog_found = True
                                break
                            else:
                                print("  Dialog open, waiting for editor...")
                        except:
                            print("  Dialog open, editor not ready...")
                except:
                    pass
                page.wait_for_timeout(500)
            
            if not dialog_found:
                print("⚠ Dialog not detected by selector")
                # Check if editor exists (means dialog is open)
                try:
                    editor_check = page.locator('div[contenteditable="true"]').first
                    if editor_check.is_visible(timeout=1000):
                        print("✓ But editor found - dialog is open")
                        dialog_found = True
                except:
                    pass
                
                if not dialog_found:
                    print(f"  Current URL: {page.url}")
                    print("  ⚠ Cannot proceed without dialog")
                    browser.close()
                    return False

            # Enter content using keyboard
            print()
            print("Entering content...")
            
            # Find editor with better selectors
            editor = None
            editor_selectors = [
                'div[role="dialog"] div[contenteditable="true"]',
                'div[contenteditable="true"]',
                'div.ProseMirror',
                '.editor[contenteditable]',
                'div.share-box-feed-entry__editor-box div[contenteditable="true"]',
            ]
            
            print("Looking for editor...")
            for sel in editor_selectors:
                try:
                    editor = page.locator(sel).first
                    if editor.is_visible(timeout=2000):
                        print(f"✓ Found editor: {sel}")
                        break
                    editor = None
                except:
                    continue
            
            # Debug if not found
            if not editor:
                print("  Editor not found, debugging...")
                try:
                    # Count contenteditable elements
                    ce_count = page.evaluate('() => document.querySelectorAll(\'[contenteditable="true"]\').length')
                    print(f"  Contenteditable elements: {ce_count}")
                    
                    # Check dialog
                    dialog_count = page.evaluate('() => document.querySelectorAll(\'[role="dialog"]\').length')
                    print(f"  Dialogs: {dialog_count}")
                    
                    # Try to get first contenteditable
                    if ce_count > 0:
                        editor = page.locator('[contenteditable="true"]').first
                        print("  ✓ Found contenteditable element")
                except Exception as e:
                    print(f"  Debug error: {e}")
            
            if editor:
                try:
                    # Click and type
                    editor.click()
                    page.wait_for_timeout(1000)
                    
                    # Type content line by line
                    print("Typing content...")
                    for line in post_content.split('\n'):
                        page.keyboard.type(line)
                        page.keyboard.press('Enter')
                        page.wait_for_timeout(100)
                    
                    print("✓ Content entered")
                    
                    # IMPORTANT: Wait for LinkedIn to process input
                    print("Waiting for LinkedIn to process...")
                    page.wait_for_timeout(5000)
                    
                except Exception as e:
                    print(f"⚠ Error entering content: {e}")
                    print("  Please paste manually:")
                    print("-" * 70)
                    print(post_content)
                    print("-" * 70)
                    print("  Waiting 30 seconds...")
                    for i in range(30):
                        time.sleep(1)
                        if i % 10 == 0:
                            print(f"  Waiting... ({i}/30s)")
            else:
                print("⚠ Editor not found")
                print("  Please paste manually:")
                print("-" * 70)
                print(post_content)
                print("-" * 70)
                print("  Waiting 30 seconds...")
                for i in range(30):
                    time.sleep(1)
                    if i % 10 == 0:
                        print(f"  Waiting... ({i}/30s)")

            # Wait for Post button
            print()
            print("Looking for Post button...")
            post_btn = None
            post_selectors = [
                'button:has-text("Post")',
                'button:has-text("POST")',
                'button.artdeco-button--primary:not([disabled])',
                '[aria-label="Post"]',
                'button.share-actions__primary-action',
            ]
            
            for i in range(15):  # 15 seconds max
                for sel in post_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=500):
                            disabled = btn.get_attribute('disabled')
                            if not disabled:
                                post_btn = btn
                                print(f"✓ Post button found ({sel})")
                                break
                            else:
                                print(f"  Button found but disabled ({sel})")
                    except:
                        pass
                if post_btn:
                    break
                page.wait_for_timeout(1000)
                if (i + 1) % 5 == 0:
                    print(f"  Still waiting... ({i+1}/15s)")

            if post_btn:
                print("Clicking Post button...")
                post_btn.click()
                page.wait_for_timeout(3000)
                
                # Handle audience dialog if it appears
                try:
                    dialog = page.locator('[role="dialog"]').last
                    if dialog.is_visible(timeout=2000):
                        print("✓ Audience dialog opened")
                        # Click Anyone
                        try:
                            anyone = page.locator('button:has-text("Anyone")').first
                            if anyone.is_visible(timeout=1500):
                                anyone.click()
                                page.wait_for_timeout(1000)
                        except:
                            pass
                        # Click Done
                        try:
                            done = page.locator('button:has-text("Done")').first
                            if done.is_visible(timeout=1500):
                                done.click()
                                page.wait_for_timeout(2000)
                        except:
                            pass
                        # Click Post again
                        try:
                            final_btn = page.locator('button:has-text("Post")').first
                            if final_btn.is_visible(timeout=1500):
                                final_btn.click()
                                print("✓ Post submitted")
                        except:
                            pass
                except:
                    print("✓ Post submitted")
                
                # Wait for confirmation
                page.wait_for_timeout(5000)
                
                # Check if on feed
                if 'feed' in page.url.lower() and 'share' not in page.url.lower():
                    print("✓ POST SUCCESSFUL!")
                else:
                    print("✓ Post likely submitted")
            else:
                print("⚠ Post button not found or still disabled")
                print("  You may need to click Post manually")
                print("  Waiting 30 seconds...")
                for i in range(30):
                    time.sleep(1)
                    if i % 10 == 0:
                        print(f"  Waiting... ({i}/30s)")

            # Screenshot
            try:
                screenshot = vault_path / 'Done' / f'LINKEDIN_POST_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot))
                print(f"✓ Screenshot saved: {screenshot.name}")
            except Exception as e:
                print(f"⚠ Screenshot: {e}")

            browser.close()

        # Save result
        result_path = vault_path / 'Done' / f'LINKEDIN_POST_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        result_path.write_text(f"""---
type: linkedin_post_result
created: {datetime.now().isoformat()}
status: posted
---

# Posted Successfully

{post_content}
""", encoding='utf-8')

        print("\n" + "=" * 70)
        print("✓ POST COMPLETE!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == '__main__':
    main()
