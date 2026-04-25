"""
LinkedIn Login Script for AI Employee

Flow:
1. Run this script
2. Browser opens (visible)
3. Login to LinkedIn with your credentials
4. Wait until you see your feed
5. Close browser manually
6. Session saved for watcher and posting

Uses Kilo Code for reasoning.
"""

import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('LinkedIn Login')


def login():
    """Open LinkedIn in visible browser for manual login."""
    project_root = Path(__file__).parent.parent.absolute()
    session_path = project_root / 'linkedin_session'
    session_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("LinkedIn Login for AI Employee")
    print("=" * 70)
    print()
    print("A browser window will open in 3 seconds...")
    print()
    print("INSTRUCTIONS:")
    print("  1. Login to LinkedIn with your credentials")
    print("  2. Wait until you see your home feed")
    print("  3. DO NOT close the browser yet")
    print("  4. The script will detect login and save session")
    print("  5. Then you can close the browser")
    print()
    print("Starting in 3 seconds...")
    time.sleep(3)

    with sync_playwright() as p:
        # Launch visible browser
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,  # Visible browser
            viewport={'width': 1280, 'height': 720},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
            ]
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("\n" + "=" * 70)
        print("Browser opened - Please login to LinkedIn")
        print("=" * 70)
        print()
        
        # Navigate to LinkedIn login
        page.goto('https://www.linkedin.com/login', wait_until='networkidle', timeout=60000)
        
        # Wait for user to login (check every 3 seconds, max 5 minutes)
        print("Waiting for login... (checking every 3 seconds)")
        print("Once logged in, you'll see your feed.")
        print("The session will be saved automatically.")
        print()
        
        logged_in = False
        for i in range(100):  # 100 * 3 = 300 seconds = 5 minutes
            try:
                current_url = page.url
                
                # Check if logged in (URL contains feed, mynetwork, etc.)
                if any(x in current_url for x in ['/feed', '/mynetwork', '/jobs', '/messaging']):
                    print("\n✓ Login detected!")
                    print("✓ Waiting 10 seconds to ensure session is fully loaded...")
                    time.sleep(10)
                    logged_in = True
                    break
                
                # Show progress every 10 checks
                if (i + 1) % 10 == 0:
                    print(f"  Still waiting... ({(i+1)*3}/300 seconds)")
                
                time.sleep(3)
                
            except Exception as e:
                logger.debug(f"Check error: {e}")
                time.sleep(3)
        
        if logged_in:
            print("\n" + "=" * 70)
            print("✓ LOGIN SUCCESSFUL!")
            print("=" * 70)
            print()
            print(f"Session saved to: {session_path}")
            print()
            print("You can now close this browser window.")
            print()
            print("NEXT STEP:")
            print("  Run: python scripts/linkedin_post.py")
            print("  This will open LinkedIn and post using Kilo AI")
            print()
            
            # Wait for user to close browser
            try:
                while browser.is_connected():
                    time.sleep(1)
            except:
                pass
        else:
            print("\n" + "=" * 70)
            print("Login not completed within 5 minutes")
            print("=" * 70)
            print()
            print("Please run the script again and login faster.")
            browser.close()


if __name__ == '__main__':
    login()
