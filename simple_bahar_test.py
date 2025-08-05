#!/usr/bin/env python3
"""
Simple test to check if we can access Bahar at all with different approaches.
"""

import asyncio
import requests
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def test_bahar_accessibility():
    """Test different ways to access Bahar website."""
    
    print("🔍 Testing Bahar Website Accessibility")
    print("=" * 50)
    
    # Test 1: Simple HTTP request
    print("\n1️⃣ Testing simple HTTP request...")
    try:
        response = requests.get("https://bahr.sa", timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"📝 Content length: {len(response.content)} bytes")
        
        # Check if we got redirected
        if response.url != "https://bahr.sa":
            print(f"🔄 Redirected to: {response.url}")
            
    except Exception as e:
        print(f"❌ HTTP request failed: {str(e)}")
    
    # Test 2: Try with different user agent
    print("\n2️⃣ Testing with regular browser user agent...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get("https://bahr.sa", headers=headers, timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"📝 Content length: {len(response.content)} bytes")
        
    except Exception as e:
        print(f"❌ HTTP request with headers failed: {str(e)}")
    
    # Test 3: Try Playwright with stealth mode
    print("\n3️⃣ Testing Playwright with stealth mode...")
    try:
        from playwright_stealth import stealth_async
        
        browser_manager = PlaywrightManager(browser_type="chromium", headless=True)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        # Apply stealth mode
        await stealth_async(page)
        
        # Set user agent
        await page.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Try to navigate
        print("🌐 Attempting to navigate...")
        response = await page.goto("https://bahr.sa", wait_until="domcontentloaded", timeout=15000)
        
        if response:
            print(f"✅ Navigation successful! Status: {response.status}")
            print(f"📍 Final URL: {page.url}")
            
            title = await page.title()
            print(f"📝 Page Title: {title}")
            
            # Check if page has content
            body_text = await page.text_content("body")
            if body_text and len(body_text.strip()) > 100:
                print("✅ Page has content!")
            else:
                print("⚠️ Page seems empty or blocked")
                
        await browser_manager.close()
        
    except Exception as e:
        print(f"❌ Playwright stealth failed: {str(e)}")
        try:
            await browser_manager.close()
        except:
            pass
    
    # Test 4: Manual browser suggestion
    print("\n4️⃣ Manual Browser Approach")
    print("=" * 30)
    print("Since automated access seems blocked, here's what we can do:")
    print()
    print("Option A: Manual Selector Collection")
    print("1. Open your regular browser (Safari/Chrome)")
    print("2. Go to https://bahr.sa")
    print("3. Open Developer Tools (F12 or Cmd+Opt+I)")
    print("4. Navigate to login manually")
    print("5. In Console, run these commands:")
    print()
    print("   // Find username field")
    print("   $('input[type=\"email\"], input[type=\"text\"]')")
    print()
    print("   // Find password field") 
    print("   $('input[type=\"password\"]')")
    print()
    print("   // Find submit button")
    print("   $('button[type=\"submit\"], input[type=\"submit\"]')")
    print()
    print("6. Copy the selectors and share them with me")
    print()
    print("Option B: Use Regular Browser Extension")
    print("1. Install 'ChroPath' or 'SelectorsHub' extension")
    print("2. Navigate to login page manually")
    print("3. Use extension to generate selectors")
    print()
    print("Option C: Network Analysis")
    print("1. Open Developer Tools → Network tab")
    print("2. Perform login manually")
    print("3. Look for login API endpoints")
    print("4. We can use direct API calls instead of form automation")

if __name__ == "__main__":
    asyncio.run(test_bahar_accessibility())