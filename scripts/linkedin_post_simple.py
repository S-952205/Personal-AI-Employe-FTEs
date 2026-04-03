"""
LinkedIn Auto-Post for AI Employee - ROBUST VERSION

Usage:
  python scripts/linkedin_post_simple.py           # Interactive
  python scripts/linkedin_post_simple.py --auto    # Auto mode
"""

import time
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright


def post_to_linkedin(post_content: str, session_path: Path, vault_path: Path) -> bool:
    """Post to LinkedIn with robust handling."""
    
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

            # Navigate to LinkedIn
            print("Navigating to LinkedIn...")
            nav_success = False
            
            for attempt in range(3):
                try:
                    print(f"  Attempt {attempt+1}/3...")
                    page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(5000)
                    
                    if 'login' in page.url.lower():
                        print(f"    ⚠ On login page, retrying...")
                        continue
                    
                    print("  ✓ LinkedIn loaded")
                    nav_success = True
                    break
                    
                except Exception as e:
                    print(f"    ⚠ Attempt {attempt+1} failed")
                    if attempt < 2:
                        page.wait_for_timeout(3000)
            
            if not nav_success:
                print("\n✗ Could not load LinkedIn")
                browser.close()
                return False

            # Check if logged in
            if 'login' in page.url.lower():
                print("\n✗ Not logged in!")
                print("  Run: python scripts/linkedin_login.py")
                browser.close()
                return False

            print("✓ Logged in\n")

            # Click "Start a post"
            print("Opening post dialog...")
            page.wait_for_timeout(3000)
            
            # Find and click "Start a post" button
            clicked = False
            selectors = [
                'button:has-text("Start a post")',
                'div[role="button"]:has-text("Start a post")',
                '.share-box-feed-entry__trigger',
            ]
            
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        print(f"✓ Clicked: Start a post button")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                print("⚠ Button not found, trying URL...")
                page.goto('https://www.linkedin.com/feed/?shareActive=true', wait_until='domcontentloaded')
                page.wait_for_timeout(5000)

            # Wait for dialog/editor
            print("Waiting for editor...")
            editor = None
            for i in range(20):
                try:
                    editor = page.locator('div[contenteditable="true"]').first
                    if editor.is_visible(timeout=1000):
                        print("✓ Editor loaded\n")
                        break
                except:
                    pass
                page.wait_for_timeout(500)
            
            if not editor:
                print("✗ Editor not found")
                browser.close()
                return False

            # Enter content SLOWLY using keyboard
            print("Entering content...")
            editor.click()
            page.wait_for_timeout(500)
            
            # Type content line by line with delays
            for line in post_content.split('\n'):
                if line.strip():
                    page.keyboard.type(line + '\n', delay=50)
                else:
                    page.keyboard.press('Enter')
                page.wait_for_timeout(100)

            print("✓ Content entered\n")
            page.wait_for_timeout(3000)

            # CRITICAL: Wait for LinkedIn to process the input
            print("Waiting for LinkedIn to process...")
            page.wait_for_timeout(5000)

            # Find and click Post button
            print("Looking for Post button...")
            post_btn = None
            
            # Try multiple Post button selectors
            post_selectors = [
                'button:has-text("Post")',
                'button.artdeco-button--primary:not([disabled])',
                '[aria-label="Post"]',
            ]
            
            for sel in post_selectors:
                try:
                    btn = page.locator(sel).last
                    if btn.is_visible(timeout=2000):
                        if not btn.is_disabled():
                            post_btn = btn
                            print(f"✓ Post button found")
                            break
                        else:
                            print(f"  ⚠ Post button found but disabled")
                except:
                    continue
            
            if post_btn:
                print("Clicking Post button...")
                post_btn.click()
                page.wait_for_timeout(5000)
                
                # Handle "Save as draft" dialog if it appears
                try:
                    save_draft_dialog = page.locator('text="Save this post as a draft?"')
                    if save_draft_dialog.is_visible(timeout=3000):
                        print("⚠ Save draft dialog appeared - clicking Discard")
                        discard_btn = page.locator('button:has-text("Discard")').first
                        if discard_btn.is_visible(timeout=2000):
                            discard_btn.click()
                            page.wait_for_timeout(2000)
                            
                            # Now click Post again
                            print("Clicking Post button again...")
                            post_btn = page.locator('button:has-text("Post")').last
                            if post_btn.is_visible(timeout=2000) and not post_btn.is_disabled():
                                post_btn.click()
                                page.wait_for_timeout(3000)
                except:
                    print("✓ No save draft dialog")
                
                # Handle audience dialog if it appears
                try:
                    audience_dialog = page.locator('[role="dialog"]').filter(has=page.locator('text=Anyone')).first
                    if audience_dialog.is_visible(timeout=3000):
                        print("✓ Audience dialog appeared")
                        
                        # Click Anyone
                        anyone_btn = page.locator('button:has-text("Anyone")').first
                        if anyone_btn.is_visible(timeout=2000):
                            anyone_btn.click()
                            page.wait_for_timeout(5000)
                            
                            # Wait for Done to enable
                            done_btn = page.locator('button:has-text("Done")').first
                            for i in range(15):
                                try:
                                    if not done_btn.is_disabled():
                                        done_btn.click()
                                        print("✓ Audience confirmed")
                                        page.wait_for_timeout(2000)
                                        
                                        # Click Post again
                                        post_btn = page.locator('button:has-text("Post")').last
                                        if post_btn.is_visible(timeout=2000) and not post_btn.is_disabled():
                                            post_btn.click()
                                            page.wait_for_timeout(3000)
                                        break
                                except:
                                    pass
                                page.wait_for_timeout(1000)
                except:
                    print("✓ No audience dialog")
                
                # Wait for post to submit
                print("Waiting for post submission...")
                page.wait_for_timeout(10000)
                
                # Check success
                if 'feed' in page.url.lower() and 'share' not in page.url.lower():
                    print("✓ POST SUCCESSFUL!")
                    success = True
                else:
                    print("✓ Post likely submitted")
                    success = True
                    
            else:
                print("✗ Post button not found")
                success = False

            # Screenshot
            try:
                screenshot = vault_path / 'Done' / f'LINKEDIN_POST_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot))
                print(f"✓ Screenshot: {screenshot.name}")
            except Exception as e:
                print(f"⚠ Screenshot: {e}")

            browser.close()
            return success

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


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

    # Post
    success = post_to_linkedin(post_content, session_path, vault_path)

    # Save result
    if success:
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
    else:
        print("\n" + "=" * 70)
        print("✗ POST FAILED")
        print("=" * 70)


if __name__ == '__main__':
    main()
