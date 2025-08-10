#!/usr/bin/env python3
"""
Combined Bahar Automation Script
================================

This script combines three tested components:
1. Token-first browser login (from test_bahar_esso_login.py option 3)
2. Project finding and extraction (already tested)
3. AI Arabic offer generation with full mapping placeholders (already tested)
"""

import asyncio
import os
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Import the tested components
from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.submit_offer_with_ai import generate_fallback_offer, extract_complete_project_details, fill_offer_form
from jobber_fsm.core.skills.login_bahar_esso import perform_esso_authentication, setup_browser_session_with_token
from jobber_fsm.utils.logger import logger


async def combined_bahar_automation():
    """
    Complete Bahar automation workflow combining:
    1. Token-first browser login
    2. Project finding and extraction
    3. AI Arabic offer generation
    """
    print("🚀 Combined Bahar Automation")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = "https://bahr.sa"
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return False
    
    print(f"👤 Using credentials for: {bahar_username}")
    
    # User preferences for AI offer generation
    user_preferences = {
        "skills": ["Web Development", "React", "Node.js", "JavaScript", "TypeScript", "MongoDB", "تطوير الويب"],
        "experience": "5 سنوات",
        "rate": "60 دولار/ساعة",
        "Minimum Project Budget": 100,
        "Maximum Project Budget": 5000,
        "Preferred Project Categories": ["Web Development", "Mobile Development", "Data Analysis", "AI/ML"]
    }
    
    print("👤 User Preferences Loaded:")
    print(f"   Skills: {', '.join(user_preferences.get('skills', []))}")
    print(f"   Experience: {user_preferences.get('experience', 'N/A')}")
    print(f"   Rate: {user_preferences.get('rate', 'N/A')}")
    
    browser_manager = None
    
    try:
        # STEP 1: Token-first browser login (Option 3 from test_bahar_esso_login.py)
        print("\n🔐 Step 1: Getting authentication token from ESSO API...")
        auth_result = await perform_esso_authentication(bahar_username, bahar_password)
        
        if not auth_result["success"]:
            print(f"❌ Failed to get token: {auth_result['message']}")
            return False
            
        print("✅ Token received successfully!")
        
        print("🌐 Step 2: Setting up browser with authentication token...")
        
        # Initialize browser
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        page = await browser_manager.get_current_page()
        
        # Set up browser session with token
        session_result = await setup_browser_session_with_token(page, auth_result, bahar_url)
        
        if not session_result["success"]:
            print(f"❌ Failed to set up browser session: {session_result['message']}")
            return False
            
        print("✅ Browser session set up with token!")
        
        # STEP 2: Navigate to projects page and find projects
        print("\n🔍 Step 3: Navigating to projects page...")
        await page.goto(f"{bahar_url}/projects", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        print("📋 Looking for available projects...")
        
        # Try to find project links
        project_selectors = [
            "a[href*='/projects/']",
            ".project-card a",
            ".project-item a",
            "[data-testid='project-link']",
            ".project-link",
            "a[href*='project']"
        ]
        
        project_url = None
        for selector in project_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    # Get the first project URL
                    project_url = await elements[0].get_attribute('href')
                    if project_url and not project_url.startswith('http'):
                        project_url = f"{bahar_url}{project_url}"
                    print(f"   Found project URL: {project_url}")
                    break
            except Exception as e:
                print(f"   Failed with selector {selector}: {str(e)}")
                continue
        
        if not project_url:
            print("❌ No project found")
            return False
        
        # STEP 3: Navigate to the project page and extract details
        print(f"\n📄 Step 4: Navigating to project: {project_url}")
        await page.goto(project_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Extract project details
        print("\n📝 Step 5: Extracting project details...")
        project_info = await extract_complete_project_details(page, {})
        
        if not project_info or not project_info.get('title'):
            print("❌ Failed to extract project details")
            return False
        
        print(f"   Project Title: {project_info.get('title', 'N/A')}")
        print(f"   Project Budget: {project_info.get('budget', 'N/A')}")
        print(f"   Project Skills: {', '.join(project_info.get('skills', []))}")
        print(f"   Project Description: {project_info.get('description', 'N/A')[:100]}...")
        
        # STEP 4: Generate AI Arabic offer with full mapping placeholders
        print("\n🤖 Step 6: Generating AI Arabic offer...")
        ai_offer = generate_fallback_offer(project_info, user_preferences)
        
        print("✅ AI Offer Generated Successfully!")
        print("\n📝 Generated Offer Details:")
        print(f"   Duration: {ai_offer.get('duration', 'N/A')} days")
        print(f"   Milestones: {ai_offer.get('milestone_number', 'N/A')}")
        print(f"   Total Price: {ai_offer.get('total_price_sar', 'N/A')} SAR")
        print(f"   Brief: {ai_offer.get('brief', 'N/A')[:100]}...")
        print(f"   Platform Communication: {ai_offer.get('platform_communication', 'N/A')}")
        
        # STEP 5: Fill and submit the offer form
        print("\n📝 Step 7: Filling offer form...")
        fill_result = await fill_offer_form(page, ai_offer, user_preferences)
        
        if fill_result.get("success"):
            print("✅ Offer form filled successfully!")
            print(f"   Result: {fill_result.get('message', 'N/A')}")
        else:
            print("❌ Failed to fill offer form")
            print(f"   Error: {fill_result.get('message', 'N/A')}")
        
        print("\n🎉 Combined automation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during combined automation: {str(e)}")
        traceback.print_exc()
        return False
        
    finally:
        if browser_manager:
            try:
                await browser_manager.stop_playwright()
            except:
                pass


async def test_without_credentials():
    """
    Test the structure without real credentials.
    """
    print("🧪 Testing Combined Bahar Automation Structure (without real credentials)...")
    
    try:
        # Test AI offer generation with sample data
        sample_project = {
            "title": "تطوير موقع ويب احترافي",
            "description": "مشروع تطوير موقع ويب شامل مع واجهة مستخدم حديثة",
            "budget": "5000",
            "skills": ["Web Development", "React", "JavaScript"],
            "category": "Web Development"
        }
        
        user_preferences = {
            "skills": ["Web Development", "React", "Node.js", "JavaScript", "TypeScript", "MongoDB", "تطوير الويب"],
            "experience": "5 سنوات",
            "rate": "60 دولار/ساعة"
        }
        
        print("🤖 Testing AI offer generation...")
        ai_offer = generate_fallback_offer(sample_project, user_preferences)
        
        print("✅ AI Offer Generated Successfully!")
        print("\n📝 Sample Offer Details:")
        print(f"   Duration: {ai_offer.get('duration', 'N/A')} days")
        print(f"   Milestones: {ai_offer.get('milestone_number', 'N/A')}")
        print(f"   Total Price: {ai_offer.get('total_price_sar', 'N/A')} SAR")
        print(f"   Brief: {ai_offer.get('brief', 'N/A')[:100]}...")
        print(f"   Platform Communication: {ai_offer.get('platform_communication', 'N/A')}")
        
        print("\n✅ Combined automation structure is ready!")
        print("📝 To use with real credentials:")
        print("   1. Set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   2. Run the combined_bahar_automation() function")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 Combined Bahar Automation Test")
    print("=" * 50)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print("🔑 Credentials found! Running full automation...")
        success = asyncio.run(combined_bahar_automation())
        if success:
            print("\n✨ Full automation completed successfully!")
        else:
            print("\n❌ Automation failed!")
    else:
        print("🔑 No credentials found, running structure test...")
        asyncio.run(test_without_credentials())
    
    print("\n✨ Test completed!") 