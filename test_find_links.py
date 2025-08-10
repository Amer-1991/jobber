#!/usr/bin/env python3
"""
Test to find all links on the project page to see if the submit button is actually a link.
"""

import asyncio
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def find_all_links():
    """
    Find all links on the project page to see if the submit button is actually a link.
    """
    print("🔍 Finding All Links on Project Page...")
    
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
        
        # Step 3: Find all links
        print("🔍 Step 3: Finding all links on the page...")
        
        # Find all link elements
        links = await page.query_selector_all("a")
        print(f"📥 Found {len(links)} link elements")
        
        # Step 4: Analyze link texts
        print("\n🔍 Step 4: Analyzing link texts...")
        
        print("\n📋 All Link Elements:")
        for i, link in enumerate(links):
            try:
                link_text = await link.text_content()
                link_href = await link.get_attribute("href")
                link_id = await link.get_attribute("id")
                link_class = await link.get_attribute("class")
                
                print(f"   Link {i+1}:")
                print(f"      Text: '{link_text}'")
                print(f"      Href: {link_href}")
                print(f"      ID: {link_id}")
                print(f"      Class: {link_class}")
                
                # Check if this looks like a submit link
                if link_text and any(keyword in link_text for keyword in ["تقديم", "عرض", "submit", "offer"]):
                    print(f"      🎯 POTENTIAL SUBMIT LINK!")
                
            except Exception as e:
                print(f"   Link {i+1}: Error reading - {str(e)}")
        
        # Step 5: Look for specific submit link patterns
        print("\n🔍 Step 5: Looking for specific submit link patterns...")
        
        # Try different selectors for submit links
        submit_selectors = [
            "a:has-text('تقديم العرض')",
            "a:has-text('تقديم عرض')",
            "a:has-text('تقديم')",
            "a:has-text('عرض')",
            "a[href*='proposals']",
            "a[href*='submit']",
            "a[href*='offer']"
        ]
        
        for selector in submit_selectors:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                href = await element.get_attribute("href")
                print(f"✅ Found with selector '{selector}': '{text}' -> {href}")
            else:
                print(f"❌ Not found with selector '{selector}'")
        
        # Step 6: Scroll down to see if there are more elements
        print("\n🔍 Step 6: Scrolling down to see if there are more elements...")
        
        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        
        # Check for submit button/link again after scrolling
        submit_after_scroll = await page.query_selector("a:has-text('تقديم العرض')")
        if submit_after_scroll:
            text = await submit_after_scroll.text_content()
            href = await submit_after_scroll.get_attribute("href")
            print(f"✅ Found submit link after scrolling: '{text}' -> {href}")
        else:
            print("❌ Still no submit link found after scrolling")
        
        # Step 7: Look for any clickable element with submit text
        print("\n🔍 Step 7: Looking for any clickable element with submit text...")
        
        # Find all elements that might contain submit text
        all_elements = await page.query_selector_all("*")
        submit_elements = []
        
        for element in all_elements:
            try:
                text = await element.text_content()
                if text and ("تقديم" in text or "عرض" in text):
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    submit_elements.append((tag_name, text))
            except:
                pass
        
        if submit_elements:
            print("📋 Elements containing 'تقديم' or 'عرض':")
            for tag_name, text in submit_elements:
                print(f"   <{tag_name}>: '{text}'")
        else:
            print("❌ No elements found containing 'تقديم' or 'عرض'")
        
        print("\n✅ Link analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during link analysis: {str(e)}")
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
    print("🎯 Find All Links Test")
    print("=" * 50)
    print("This will find all links on the project page to see if the submit button is actually a link.")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting link analysis...")
    asyncio.run(find_all_links())
    
    print("\n✨ Analysis completed!") 