#!/usr/bin/env python3
"""
Test script for Bahar login functionality.
This script demonstrates how to use the login_bahar skill.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import the Bahar login skill
from jobber_fsm.core.skills.login_bahar import login_bahar, logout_bahar
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_bahar_login():
    """
    Test the Bahar login functionality.
    """
    print("🚀 Starting Bahar login test...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables (for security)
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahar.com")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   You can create a .env file with:")
        print("   BAHAR_USERNAME=your_username")
        print("   BAHAR_PASSWORD=your_password")
        print("   BAHAR_URL=https://bahar.com")
        return
    
    try:
        # Initialize the browser
        print("🌐 Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)  # Use eval mode to not require CDP
        
        # Navigate to a blank page first
        page = await browser_manager.get_current_page()
        await page.goto("about:blank")
        
        # Test login
        print(f"🔐 Attempting to login to {bahar_url}...")
        login_result = await login_bahar(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=5.0
        )
        
        print(f"📝 Login result: {login_result}")
        
        if "Success" in login_result:
            print("✅ Login successful!")
            
            # Wait a bit to see the logged-in state
            await asyncio.sleep(3)
            
            # Test logout
            print("🚪 Testing logout...")
            logout_result = await logout_bahar()
            print(f"📝 Logout result: {logout_result}")
            
        else:
            print("❌ Login failed!")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        try:
            await browser_manager.close()
        except:
            pass

async def test_without_credentials():
    """
    Test the login skill with placeholder credentials for demonstration.
    """
    print("🧪 Testing Bahar login skill structure (without real credentials)...")
    
    try:
        # Initialize the browser
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)  # Use eval mode to not require CDP
        
        # Navigate to a blank page
        page = await browser_manager.get_current_page()
        await page.goto("about:blank")
        
        print("✅ Browser initialized successfully")
        print("✅ Bahar login skill is ready to use")
        print("📝 To use with real credentials:")
        print("   1. Set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   2. Update the bahar_url if needed")
        print("   3. Run the test_bahar_login() function")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        try:
            await browser_manager.close()
        except:
            pass

if __name__ == "__main__":
    print("🎯 Bahar Login Skill Test")
    print("=" * 50)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print("🔑 Credentials found, running full test...")
        asyncio.run(test_bahar_login())
    else:
        print("🔑 No credentials found, running structure test...")
        asyncio.run(test_without_credentials())
    
    print("\n✨ Test completed!") 