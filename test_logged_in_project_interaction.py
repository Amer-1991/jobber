#!/usr/bin/env python3
"""
Test that ensures login first, then navigates to projects page and records user interactions.
This will maintain the authenticated session throughout the process.
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.skills.search_bahar_projects import search_bahar_projects
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

class InteractionRecorder:
    """Records user interactions with the page"""
    
    def __init__(self):
        self.interactions = []
        self.start_time = datetime.now()
    
    def add_interaction(self, action, details):
        """Add an interaction to the log"""
        timestamp = datetime.now()
        self.interactions.append({
            "timestamp": timestamp.isoformat(),
            "action": action,
            "details": details
        })
    
    def get_summary(self):
        """Get a summary of all interactions"""
        return {
            "session_start": self.start_time.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_interactions": len(self.interactions),
            "interactions": self.interactions
        }

async def test_logged_in_project_interaction():
    """
    Test the complete workflow: Login -> Navigate to Projects -> Record Interactions
    """
    print("🚀 Starting Logged-In Project Interaction Test...")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    bahar_username = os.getenv("BAHAR_USERNAME")
    bahar_password = os.getenv("BAHAR_PASSWORD")
    
    if not bahar_username or not bahar_password:
        print("❌ Error: Please set BAHAR_USERNAME and BAHAR_PASSWORD environment variables")
        return
    
    browser_manager = None
    recorder = InteractionRecorder()
    
    try:
        # Step 1: Initialize browser
        print("🌐 Step 1: Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        recorder.add_interaction("browser_initialized", {"url": page.url})
        
        # Step 2: Login with ESSO authentication
        print("🔐 Step 2: Logging in with ESSO authentication...")
        login_result = await login_bahar_esso(
            username=bahar_username,
            password=bahar_password,
            bahar_url="https://bahr.sa",
            wait_time=3.0
        )
        
        print(f"📝 Login result: {login_result}")
        recorder.add_interaction("login_attempt", {"result": login_result})
        
        if "Success" not in login_result:
            print("❌ Login failed, cannot proceed")
            return
        
        print("✅ Login successful!")
        
        # Step 3: Check authentication status
        cookies = await page.context.cookies()
        access_token_found = any(cookie.get("name") == "access_token" for cookie in cookies)
        print(f"🍪 Access token in session: {'✅ Yes' if access_token_found else '❌ No'}")
        
        recorder.add_interaction("authentication_check", {
            "access_token_found": access_token_found,
            "total_cookies": len(cookies)
        })
        
        # Step 4: Navigate to projects page
        print("🔄 Step 3: Navigating to projects page...")
        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        recorder.add_interaction("navigate_to_projects", {"url": current_url})
        
        # Step 5: Extract initial projects
        print("🔍 Step 4: Extracting initial projects...")
        search_result = await search_bahar_projects(
            search_query="",
            max_results=5
        )
        
        result_data = json.loads(search_result)
        projects = result_data.get("projects", [])
        print(f"✅ Found {len(projects)} initial projects")
        
        recorder.add_interaction("initial_project_extraction", {
            "projects_found": len(projects),
            "project_titles": [p.get("title", "N/A") for p in projects]
        })
        
        # Step 6: Show projects and wait for user interaction
        print("\n📋 Initial Projects Found:")
        for i, project in enumerate(projects, 1):
            print(f"\n🎯 Project {i}:")
            print(f"   📝 Title: {project.get('title', 'N/A')}")
            print(f"   💰 Budget: {project.get('budget', 'N/A')}")
            if project.get('description'):
                desc = project['description'][:100] + "..." if len(project['description']) > 100 else project['description']
                print(f"   📄 Description: {desc}")
        
        # Step 7: Record user interactions
        print("\n🎯 READY FOR INTERACTION RECORDING!")
        print("=" * 50)
        print("The browser is now on the Bahar projects page with full authentication.")
        print("I will record your interactions as you:")
        print("  - Click on projects")
        print("  - Apply filters")
        print("  - Navigate between pages")
        print("  - Search for specific projects")
        print("  - Or any other actions you perform")
        print()
        print("Press Enter when you're done with your interactions...")
        
        # Set up interaction recording
        await setup_interaction_recording(page, recorder)
        
        # Wait for user to finish
        input("Press Enter when you're done exploring the projects page...")
        
        # Step 8: Final project extraction
        print("\n🔍 Step 5: Extracting final projects after your interactions...")
        final_search_result = await search_bahar_projects(
            search_query="",
            max_results=10
        )
        
        final_result_data = json.loads(final_search_result)
        final_projects = final_result_data.get("projects", [])
        print(f"✅ Found {len(final_projects)} projects after interactions")
        
        recorder.add_interaction("final_project_extraction", {
            "projects_found": len(final_projects),
            "project_titles": [p.get("title", "N/A") for p in projects]
        })
        
        # Step 9: Save interaction log
        interaction_summary = recorder.get_summary()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bahar_interaction_log_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(interaction_summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 Interaction log saved to: {filename}")
        print(f"📊 Total interactions recorded: {len(interaction_summary['interactions'])}")
        
        # Show summary
        print("\n📋 Interaction Summary:")
        for interaction in interaction_summary['interactions']:
            print(f"  {interaction['timestamp']}: {interaction['action']} - {interaction['details']}")
        
        print("\n✅ Logged-in project interaction test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Save error to interaction log
        if 'recorder' in locals():
            recorder.add_interaction("error", {"error": str(e)})
            interaction_summary = recorder.get_summary()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bahar_interaction_log_error_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(interaction_summary, f, ensure_ascii=False, indent=2)
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

async def setup_interaction_recording(page, recorder):
    """
    Set up event listeners to record user interactions.
    """
    try:
        # Record page navigation
        page.on("framenavigated", lambda frame: recorder.add_interaction("page_navigation", {
            "url": frame.url,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Record clicks
        page.on("click", lambda: recorder.add_interaction("click", {
            "timestamp": datetime.now().isoformat()
        }))
        
        # Record form submissions
        page.on("request", lambda request: recorder.add_interaction("request", {
            "url": request.url,
            "method": request.method,
            "timestamp": datetime.now().isoformat()
        }) if request.method == "POST" else None)
        
        print("✅ Interaction recording set up successfully")
        
    except Exception as e:
        print(f"⚠️ Could not set up automatic interaction recording: {str(e)}")
        print("📝 Manual interaction logging will be used instead")

if __name__ == "__main__":
    print("🎯 Logged-In Project Interaction Test")
    print("=" * 50)
    print("This test will:")
    print("1. Login to Bahar using ESSO authentication")
    print("2. Navigate to the projects page")
    print("3. Record all your interactions")
    print("4. Save the interaction log to a file")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting logged-in project interaction test...")
    asyncio.run(test_logged_in_project_interaction())
    
    print("\n✨ Test completed!") 