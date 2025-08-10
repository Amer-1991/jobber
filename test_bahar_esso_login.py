#!/usr/bin/env python3
"""
Test script for Bahar ESSO login functionality.
This script demonstrates how to use the login_bahar_esso skill.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import the Bahar ESSO login skill
from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso, logout_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_bahar_esso_login():
    """
    Test the Bahar ESSO login functionality.
    """
    print("🚀 Starting Bahar ESSO login test...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables (for security)
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   You can create a .env file with:")
        print("   BAHAR_USERNAME=your_username")
        print("   BAHAR_PASSWORD=your_password")
        print("   BAHAR_URL=https://bahr.sa")
        return
    
    try:
        # Initialize the browser
        print("🌐 Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)  # Use eval mode to not require CDP
        
        # Navigate to a blank page first
        page = await browser_manager.get_current_page()
        await page.goto("about:blank")
        
        # Test ESSO login
        print(f"🔐 Attempting to login to {bahar_url} using ESSO API...")
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=5.0
        )
        
        print(f"📝 Login result: {login_result}")
        
        if "Success" in login_result:
            print("✅ ESSO login successful!")
            
            # Wait a bit to see the logged-in state
            await asyncio.sleep(3)
            
            # Test logout
            print("🚪 Testing logout...")
            logout_result = await logout_bahar_esso()
            print(f"📝 Logout result: {logout_result}")
            
        else:
            print("❌ ESSO login failed!")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        try:
            await browser_manager.stop_playwright()
        except:
            pass

async def test_esso_api_only():
    """
    Test just the ESSO API call without browser automation.
    """
    print("🧪 Testing ESSO API call only...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    try:
        # Import the ESSO authentication function
        from jobber_fsm.core.skills.login_bahar_esso import perform_esso_authentication
        
        print(f"🔐 Step 1: Getting authentication token from ESSO API for {bahar_username}...")
        auth_result = await perform_esso_authentication(bahar_username, bahar_password)
        
        print(f"📝 ESSO API result: {auth_result}")
        
        if auth_result["success"]:
            print("✅ ESSO API authentication successful!")
            
            # Extract token information
            response_data = auth_result.get("response_data", {})
            access_token = response_data.get("access_token", "")
            sid_cookie = auth_result.get("cookies", "")
            
            print(f"🔑 Access Token received: {access_token[:50]}...")
            print(f"🍪 SID Cookie received: {sid_cookie[:100]}...")
            print(f"🆔 User ID: {response_data.get('id', 'N/A')}")
            print(f"📧 Email: {response_data.get('email', 'N/A')}")
            print(f"⏰ Token expires: {response_data.get('expires_at', 'N/A')}")
            
        else:
            print("❌ ESSO API authentication failed!")
            
    except Exception as e:
        print(f"❌ Error during ESSO API test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_token_based_browser_login():
    """
    Test the token-first approach: Get token from API, then set up browser session.
    """
    print("🧪 Testing Token-First Browser Login...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    try:
        print("🔐 Step 1: Getting authentication token from ESSO API...")
        from jobber_fsm.core.skills.login_bahar_esso import perform_esso_authentication, setup_browser_session_with_token
        
        # Get token from API first
        auth_result = await perform_esso_authentication(bahar_username, bahar_password)
        
        if not auth_result["success"]:
            print(f"❌ Failed to get token: {auth_result['message']}")
            return
            
        print("✅ Token received successfully!")
        
        print("🌐 Step 2: Setting up browser with authentication token...")
        
        # Initialize browser
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        page = await browser_manager.get_current_page()
        
        # Set up browser session with token
        session_result = await setup_browser_session_with_token(page, auth_result, bahar_url)
        
        if session_result["success"]:
            print("✅ Browser session set up with token!")
            
            print("🚀 Step 3: Navigating to Bahar dashboard...")
            dashboard_url = f"{bahar_url.rstrip('/')}/dashboard"
            await page.goto(dashboard_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            print(f"📍 Current URL: {page.url}")
            print("✅ Token-based authentication complete!")
            
        else:
            print(f"❌ Failed to set up browser session: {session_result['message']}")
            
        # Clean up
        await browser_manager.stop_playwright()
        
    except Exception as e:
        print(f"❌ Error during token-based login test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_without_credentials():
    """
    Test the ESSO login skill structure (without real credentials).
    """
    print("🧪 Testing Bahar ESSO login skill structure (without real credentials)...")
    
    try:
        # Initialize the browser
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        # Navigate to a blank page
        page = await browser_manager.get_current_page()
        await page.goto("about:blank")
        
        print("✅ Browser initialized successfully")
        print("✅ Bahar ESSO login skill is ready to use")
        print("📝 To use with real credentials:")
        print("   1. Set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   2. Update the bahar_url if needed")
        print("   3. Run the test_bahar_esso_login() function")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        try:
            await browser_manager.stop_playwright()
        except:
            pass

if __name__ == "__main__":
    print("🎯 Bahar ESSO Login Skill Test")
    print("=" * 50)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print("🔑 Credentials found!")
        print("Choose test option:")
        print("1. Full ESSO login test (legacy approach)")
        print("2. ESSO API test only (no browser)")
        print("3. Token-first browser login (recommended)")
        
        choice = input("Enter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            print("🔑 Running full ESSO login test...")
            asyncio.run(test_bahar_esso_login())
        elif choice == "2":
            print("🔑 Running ESSO API test only...")
            asyncio.run(test_esso_api_only())
        elif choice == "3":
            print("🔑 Running token-first browser login...")
            asyncio.run(test_token_based_browser_login())
        else:
            print("❌ Invalid choice, running token-first test...")
            asyncio.run(test_token_based_browser_login())
    else:
        print("🔑 No credentials found, running structure test...")
        asyncio.run(test_without_credentials())
    
    print("\n✨ Test completed!") 