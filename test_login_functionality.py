#!/usr/bin/env python3
"""
Test script to demonstrate login functionality
"""

import asyncio
import os
from dotenv import load_dotenv

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.login_bahar import login_bahar

async def test_login_functionality():
    """Test the login functionality."""
    print("🔐 Testing Login Functionality")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Bahar credentials not configured")
        print("   Please set BAHAR_USERNAME and BAHAR_PASSWORD in the .env file")
        print("   Using demo mode...")
        return await test_login_demo()
    
    print("✅ Credentials found")
    print(f"   Username: {bahar_username}")
    print(f"   URL: {bahar_url}")
    
    browser_manager = None
    
    try:
        # Initialize browser
        print("\n🌐 Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        print("✅ Browser initialized")
        
        # Test login
        print(f"\n🔐 Attempting login to {bahar_url}...")
        login_result = await login_bahar(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=5.0
        )
        
        print(f"📝 Login Result: {login_result}")
        
        if "Success" in login_result:
            print("✅ Login successful!")
            
            # Get current URL to verify
            current_url = await browser_manager.get_current_url()
            print(f"   Current URL: {current_url}")
            
            # Keep browser open for inspection
            print("\n🔍 Browser will stay open for 30 seconds for inspection...")
            print("   You can manually verify the login status")
            print("   Press Ctrl+C to close early")
            
            try:
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print("\n⏹️ Closing browser...")
            
            return True
        else:
            print("❌ Login failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during login test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.close()
            except:
                pass


async def test_login_demo():
    """Demo the login functionality without real credentials."""
    print("🧪 Login Functionality Demo")
    print("=" * 50)
    
    try:
        # Initialize browser
        print("\n🌐 Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        print("✅ Browser initialized")
        
        # Navigate to Bahar
        page = await browser_manager.get_current_page()
        await page.goto("https://bahr.sa", wait_until="domcontentloaded")
        
        print("✅ Navigated to Bahar website")
        print("   Browser is open and ready for manual login")
        print("   You can manually log in to test the system")
        
        # Keep browser open
        print("\n🔍 Browser will stay open for 60 seconds...")
        print("   You can manually log in and test the system")
        print("   Press Ctrl+C to close early")
        
        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\n⏹️ Closing browser...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        return False
        
    finally:
        # Clean up
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.close()
            except:
                pass


async def main():
    """Main test function."""
    print("🎯 Login Functionality Test")
    print("=" * 50)
    
    success = await test_login_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Login test completed successfully!")
        return 0
    else:
        print("❌ Login test failed")
        return 1


if __name__ == "__main__":
    asyncio.run(main()) 