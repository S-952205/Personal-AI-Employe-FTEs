"""
Manual LinkedIn Session Setup

Since LinkedIn/Google blocks automated browsers, use this approach:

1. Open Chrome normally (not via script)
2. Go to linkedin.com and login
3. Run this script to copy your Chrome cookies to the watcher session
"""

import json
import sqlite3
import shutil
from pathlib import Path
from http.cookiejar import MozillaCookieJar

def get_chrome_cookies():
    """Extract cookies from your logged-in Chrome browser."""
    print("=" * 60)
    print("Manual LinkedIn Session Setup")
    print("=" * 60)
    print()
    print("STEP 1: Open Chrome and login to LinkedIn")
    print("  1. Open Google Chrome (regular browser)")
    print("  2. Go to https://www.linkedin.com")
    print("  3. Log in with your credentials")
    print("  4. Make sure you can see your feed")
    print("  5. KEEP Chrome OPEN")
    print()
    input("Press Enter when you're logged in to LinkedIn in Chrome...")
    
    # Chrome cookie database location (Windows)
    chrome_cookie_path = Path.home() / 'AppData/Local/Google/Chrome/User Data/Default/Cookies'
    
    if not chrome_cookie_path.exists():
        print("\nChrome cookie file not found at expected location.")
        print("Trying alternative locations...")
        
        # Try other Chrome profiles
        alternatives = [
            Path.home() / 'AppData/Local/Google/Chrome/User Data/Profile 1/Cookies',
            Path.home() / 'AppData/Local/Google/Chrome/User Data/Profile 2/Cookies',
            Path.home() / 'AppData/Local/Chromium/User Data/Default/Cookies',
        ]
        
        for alt in alternatives:
            if alt.exists():
                chrome_cookie_path = alt
                print(f"Found cookies at: {alt}")
                break
        else:
            print("\nCould not find Chrome cookies.")
            print("Please ensure Chrome is installed and you're logged into LinkedIn.")
            return False
    
    print(f"\nFound Chrome cookies at: {chrome_cookie_path}")
    print("\nNOTE: Chrome must be CLOSED to copy cookies.")
    print("Please close ALL Chrome windows now.")
    input("Press Enter when Chrome is closed...")
    
    # Copy cookie database
    project_root = Path(__file__).parent.parent.absolute()
    session_path = project_root / 'linkedin_session'
    session_path.mkdir(parents=True, exist_ok=True)
    
    # We'll use the cookie database directly
    cookie_db = session_path / 'Cookies'
    
    try:
        shutil.copy2(chrome_cookie_path, cookie_db)
        print(f"\n✓ Cookies copied to: {cookie_db}")
        print("\nSTEP 3: Reopen Chrome and verify LinkedIn login")
        print("The watcher will now use these cookies.")
        return True
    except Exception as e:
        print(f"\nError copying cookies: {e}")
        print("\nAlternative: Use a browser extension to export cookies")
        print("Extension: 'EditThisCookie' or 'Cookie Editor'")
        print("1. Install extension in Chrome")
        print("2. Go to linkedin.com")
        print("3. Export cookies as JSON")
        print("4. Save to: linkedin_session/cookies.json")
        return False


def main():
    success = get_chrome_cookies()
    
    if success:
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print("\nNow run the LinkedIn watcher:")
        print("  python scripts/linkedin_watcher.py")
    else:
        print("\n" + "=" * 60)
        print("SETUP FAILED - Try Alternative Method")
        print("=" * 60)
        print("\nUse browser extension method:")
        print("1. Install 'EditThisCookie' extension for Chrome")
        print("2. Login to LinkedIn in Chrome")
        print("3. Click extension icon > Export (JSON format)")
        print("4. Save as: linkedin_session/cookies.json")
        print("\nThen modify linkedin_watcher.py to load cookies from JSON")


if __name__ == '__main__':
    main()
