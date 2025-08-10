#!/usr/bin/env python3
"""
Test to find all buttons on the project page to identify the correct submit button.
"""

import asyncio
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def find_all_buttons():
    """
    Find all buttons on the project page to identify the submit button.
    """
    print("🔍 Finding All Buttons on Project Page...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    browser_manager = None
    
    try:
        # Step 1: Initialize browser and login
        print("🌐 Step 1: Initializing browser and logging in...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        # Login
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url="https://bahr.sa",
            wait_time=3.0
        )
        
        if "Success" not in login_result:
            print("❌ Login failed, cannot proceed")
            return
        
        print("✅ Login successful!")
        
        # Step 2: Navigate to the project page
        print("🔄 Step 2: Navigating to project page...")
        
        project_url = "https://bahr.sa/projects/recruitments/01987f02-014f-74b7-96ef-caa0578f2496"
        
        await page.goto(project_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "recruitments" not in current_url:
            print("❌ Failed to navigate to project page")
            return
        
        print("✅ Successfully navigated to project page!")
        
        # Step 3: Find all buttons
        print("🔍 Step 3: Finding all buttons on the page...")
        
        # Find all button elements
        buttons = await page.query_selector_all("button")
        print(f"📥 Found {len(buttons)} button elements")
        
        # Find all elements that might be buttons (with role="button")
        role_buttons = await page.query_selector_all("[role='button']")
        print(f"📥 Found {len(role_buttons)} elements with role='button'")
        
        # Find all clickable elements (links, buttons, etc.)
        clickable_elements = await page.query_selector_all("a, button, [role='button'], [onclick], [tabindex]")
        print(f"📥 Found {len(clickable_elements)} clickable elements")
        
        # Step 4: Analyze button texts
        print("\n🔍 Step 4: Analyzing button texts...")
        
        print("\n📋 All Button Elements:")
        for i, button in enumerate(buttons):
            try:
                button_text = await button.text_content()
                button_id = await button.get_attribute("id")
                button_class = await button.get_attribute("class")
                button_disabled = await button.get_attribute("disabled")
                
                print(f"   Button {i+1}:")
                print(f"      Text: '{button_text}'")
                print(f"      ID: {button_id}")
                print(f"      Class: {button_class}")
                print(f"      Disabled: {button_disabled}")
                
                # Check if this looks like a submit button
                if button_text and any(keyword in button_text for keyword in ["تقديم", "عرض", "submit", "offer"]):
                    print(f"      🎯 POTENTIAL SUBMIT BUTTON!")
                
            except Exception as e:
                print(f"   Button {i+1}: Error reading - {str(e)}")
        
        print("\n📋 All Role Button Elements:")
        for i, button in enumerate(role_buttons):
            try:
                button_text = await button.text_content()
                button_id = await button.get_attribute("id")
                button_class = await button.get_attribute("class")
                
                print(f"   Role Button {i+1}:")
                print(f"      Text: '{button_text}'")
                print(f"      ID: {button_id}")
                print(f"      Class: {button_class}")
                
                # Check if this looks like a submit button
                if button_text and any(keyword in button_text for keyword in ["تقديم", "عرض", "submit", "offer"]):
                    print(f"      🎯 POTENTIAL SUBMIT BUTTON!")
                
            except Exception as e:
                print(f"   Role Button {i+1}: Error reading - {str(e)}")
        
        # Step 5: Look for specific submit button patterns
        print("\n🔍 Step 5: Looking for specific submit button patterns...")
        
        # Try different selectors for submit buttons
        submit_selectors = [
            "button:has-text('تقديم عرض')",
            "button:has-text('تقديم العرض')",
            "button:has-text('تقديم')",
            "button:has-text('عرض')",
            "[role='button']:has-text('تقديم عرض')",
            "[role='button']:has-text('تقديم العرض')",
            "a:has-text('تقديم عرض')",
            "a:has-text('تقديم العرض')"
        ]
        
        for selector in submit_selectors:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                print(f"✅ Found with selector '{selector}': '{text}'")
            else:
                print(f"❌ Not found with selector '{selector}'")
        
        # Step 6: Look for any text containing "تقديم" or "عرض"
        print("\n🔍 Step 6: Looking for any text containing 'تقديم' or 'عرض'...")
        
        from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
        text_content = await get_dom_with_content_type("text_only")
        
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if "تقديم" in line or "عرض" in line:
                print(f"   Line {i+1}: '{line}'")
        
        print("\n✅ Button analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during button analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

if __name__ == "__main__":
    print("🎯 Find All Buttons Test")
    print("=" * 50)
    print("This will find all buttons on the project page to identify the submit button.")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting button analysis...")
    asyncio.run(find_all_buttons())
    
    print("\n✨ Analysis completed!") 