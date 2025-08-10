#!/usr/bin/env python3
"""
Comprehensive Bahar Automation with Login Enabled
================================================

This script enables full authentication but stops before submission.
Combines all tested components with real login.
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
from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.utils.logger import logger


async def comprehensive_automation_with_login():
    """
    Complete automation workflow with login enabled but stops before submission.
    """
    print("🚀 Comprehensive Bahar Automation with Login Enabled")
    print("=" * 60)
    print("⚠️  This will login and prepare offer but STOP before submission")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    bahar_url = "https://bahr.sa"
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        print("   Example:")
        print("   BAHAR_USERNAME=your_email@example.com")
        print("   BAHAR_PASSWORD=your_password")
        return False
    
    print(f"👤 Using credentials for: {bahar_username}")
    
    # User preferences for AI offer generation
    user_preferences = {
        "skills": ["Web Development", "React", "Node.js", "JavaScript", "TypeScript", "MongoDB", "تطوير الويب"],
        "experience": "5 سنوات",
        "rate": "60 دولار/ساعة",
        "portfolio": "https://github.com/yourusername",
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
        # STEP 1: Initialize browser and perform SSO login
        print("\n🔐 Step 1: Initializing browser and performing SSO login...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        # Perform SSO login (from test_extract_project_details.py)
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url=bahar_url,
            wait_time=3.0
        )
        
        if "Success" not in login_result:
            print(f"❌ Login failed: {login_result}")
            return False
            
        print("✅ Login successful!")
        
        # STEP 2: Navigate to projects page and find a project
        print("\n�� Step 2: Navigating to projects page...")
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
        print(f"\n�� Step 3: Navigating to project: {project_url}")
        await page.goto(project_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # Extract project details
        print("\n�� Step 4: Extracting complete project details...")
        project_info = await extract_complete_project_details(page, {})
        
        if not project_info or not project_info.get('title'):
            print("❌ Failed to extract project details")
            return False
        
        print(f"   Project Title: {project_info.get('title', 'N/A')}")
        print(f"   Project Budget: {project_info.get('budget', 'N/A')}")
        print(f"   Project Skills: {', '.join(project_info.get('skills', []))}")
        print(f"   Project Description: {project_info.get('description', 'N/A')[:100]}...")
        
        # STEP 4: Generate AI Arabic offer with integer budget placeholders
        print("\n�� Step 5: Generating AI Arabic offer...")
        ai_offer = generate_fallback_offer(project_info, user_preferences)
        
        print("✅ AI Offer Generated Successfully!")
        print("\n📝 Generated Offer Details:")
        print(f"   Duration: {ai_offer.get('duration', 'N/A')} days")
        print(f"   Milestone Number: {ai_offer.get('milestone_number', 'N/A')} phases")
        print(f"   Total Price SAR: {ai_offer.get('total_price_sar', 'N/A')} ريال")
        print(f"   Platform Communication: {ai_offer.get('platform_communication', 'N/A')}")
        
        # Show milestones with integer budgets
        milestones = ai_offer.get('milestones', [])
        if milestones:
            print(f"\n�� Milestones ({len(milestones)}):")
            for i, milestone in enumerate(milestones, 1):
                print(f"   {i}. {milestone.get('deliverable', 'N/A')} - {milestone.get('budget', 'N/A')} ريال")
        
        # Show brief preview
        brief = ai_offer.get('brief', '')
        if brief:
            print(f"\n💬 Brief Preview:")
            print("=" * 50)
            print(brief[:300] + "..." if len(brief) > 300 else brief)
            print("=" * 50)
        
        # STEP 5: Look for submit offer button
        print("\n🔍 Step 6: Looking for submit offer button...")
        submit_selectors = [
            "a[href*='submit']",
            "a[href*='proposal']",
            "button:contains('تقديم عرض')",
            "button:contains('Submit Offer')",
            "a:contains('تقديم عرض')",
            "a:contains('Submit Offer')",
            "[data-testid='submit-offer']",
            ".submit-offer-btn"
        ]
        
        submit_button = None
        for selector in submit_selectors:
            try:
                submit_button = await page.query_selector(selector)
                if submit_button:
                    print(f"   Found submit button with selector: {selector}")
                    break
            except:
                continue
        
        if not submit_button:
            print("❌ Could not find submit offer button")
            return False
        
        # STEP 6: Click submit offer button to open form
        print("\n📝 Step 7: Opening offer form...")
        await submit_button.click()
        await asyncio.sleep(3)
        
        # STEP 7: Fill the form with AI-generated content
        print("\n✍️ Step 8: Filling form with AI-generated content...")
        fill_result = await fill_offer_form(page, ai_offer, user_preferences)
        
        if fill_result.get('success'):
            print("✅ Form filled successfully!")
            print(f"   Filled Fields: {', '.join(fill_result.get('filled_fields', []))}")
            
            # Show what was filled
            print("\n�� Form Fields Filled:")
            print(f"   Duration: {ai_offer.get('duration')} days")
            print(f"   Milestone Number: {ai_offer.get('milestone_number')} phases")
            print(f"   Total Price: {ai_offer.get('total_price_sar')} ريال")
            print(f"   Brief Length: {len(brief)} characters")
            print(f"   Platform Communication: {ai_offer.get('platform_communication')}")
            
            if milestones:
                print(f"   Milestones Filled:")
                for i, milestone in enumerate(milestones):
                    print(f"     Milestone {i+1}: {milestone.get('budget')} ريال - {milestone.get('deliverable')}")
            
            print("\n🎯 PREPARATION COMPLETE!")
            print("✅ Successfully authenticated with SSO")
            print("✅ Found real project and extracted details")
            print("✅ Generated AI offer with Arabic content and integer budgets")
            print("✅ Opened offer form")
            print("✅ Filled all form fields with AI content")
            print("�� STOPPED BEFORE SUBMISSION - Ready for your review!")
            
            # Save the prepared offer data
            offer_data = {
                "timestamp": datetime.now().isoformat(),
                "project_info": project_info,
                "ai_offer": ai_offer,
                "user_preferences": user_preferences,
                "fill_result": fill_result
            }
            
            with open("prepared_offer_with_login.json", "w", encoding="utf-8") as f:
                json.dump(offer_data, f, ensure_ascii=False, indent=2)
            
            print("\n💾 Offer data saved to: prepared_offer_with_login.json")
            
            # Keep browser open for inspection
            print("\n🔍 Browser will stay open for 60 seconds for inspection...")
            print("   You can manually check the filled form")
            print("   Press Ctrl+C to close early")
            print("   The form is ready but NOT submitted!")
            
            try:
                await asyncio.sleep(60)
            except KeyboardInterrupt:
                print("\n⏹️ Closing browser...")
            
        else:
            print("❌ Failed to fill form")
            print(f"   Error: {fill_result.get('message', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during automation: {str(e)}")
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
    print("🧪 Testing Comprehensive Automation Structure (without real credentials)...")
    
    try:
        # Test AI offer generation with sample data
        project_info = {
            "title": "مشروع تطوير موقع إلكتروني",
            "description": "نحتاج إلى تطوير موقع إلكتروني احترافي مع نظام إدارة المحتوى",
            "budget": "5000",
            "skills": ["تطوير الويب", "React", "Node.js"],
            "category": "Web Development"
        }
        
        user_preferences = {
            "skills": ["Web Development", "React", "Node.js", "JavaScript", "TypeScript", "MongoDB", "تطوير الويب"],
            "experience": "5 سنوات",
            "rate": "60 دولار/ساعة",
            "portfolio": "https://github.com/yourusername"
        }
        
        print("📋 Test Project:")
        print(f"   Title: {project_info['title']}")
        print(f"   Budget: {project_info['budget']}")
        print(f"   Skills: {', '.join(project_info['skills'])}")
        
        print("\n👤 User Profile:")
        print(f"   Skills: {', '.join(user_preferences['skills'])}")
        print(f"   Experience: {user_preferences['experience']}")
        print(f"   Rate: {user_preferences['rate']}")
        
        print("\n🤖 Generating Arabic offer with integer budgets...")
        
        # Test the function
        result = generate_fallback_offer(project_info, user_preferences)
        
        if result:
            print("✅ Arabic offer generation successful!")
            print("\n📝 Generated Offer:")
            print(f"   Duration: {result.get('duration', 'N/A')} days")
            print(f"   Milestone Number: {result.get('milestone_number', 'N/A')} phases")
            print(f"   Total Price SAR: {result.get('total_price_sar', 'N/A')} ريال")
            print(f"   Platform Communication: {result.get('platform_communication', 'N/A')}")
            
            # Show milestones if available
            milestones = result.get('milestones', [])
            if milestones:
                print(f"\n�� Milestones ({len(milestones)}):")
                for i, milestone in enumerate(milestones, 1):
                    print(f"   {i}. {milestone.get('deliverable', 'N/A')} - {milestone.get('budget', 'N/A')} ريال")
            
            brief = result.get('brief', '')
            if brief:
                print(f"\n💬 Brief Preview:")
                print("=" * 50)
                print(brief[:300] + "..." if len(brief) > 300 else brief)
                print("=" * 50)
            
            print("\n✅ Comprehensive automation structure is ready!")
            print("📝 To use with real credentials:")
            print("   1. Set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
            print("   2. Run the comprehensive_automation_with_login() function")
            
            return True
        else:
            print("❌ Arabic offer generation failed - no response generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎯 Comprehensive Bahar Automation with Login Enabled")
    print("=" * 60)
    print("⚠️  This will login and prepare offer but STOP before submission")
    print("=" * 60)
    
    # Check if credentials are available
    load_dotenv()
    if os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD"):
        print("�� Credentials found! Running full automation with login...")
        success = asyncio.run(comprehensive_automation_with_login())
        if success:
            print("\n✨ Automation with login completed successfully!")
            print("🛑 Form is ready but NOT submitted - check the browser!")
        else:
            print("\n❌ Automation failed!")
    else:
        print("🔑 No credentials found, running structure test...")
        asyncio.run(test_without_credentials())
    
    print("\n✨ Test completed!")