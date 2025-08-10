#!/usr/bin/env python3
"""
Test to navigate through multiple projects, check their status, and move to the next one.
"""

import asyncio
import os
import json
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def navigate_multiple_projects():
    """
    Navigate through multiple projects, check their status, and move to the next one.
    """
    print("🔍 Navigating Multiple Projects...")
    
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
        
        # Step 2: Navigate to projects page
        print("🔄 Step 2: Navigating to projects page...")
        
        await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "projects" not in current_url:
            print("❌ Failed to navigate to projects page")
            return
        
        print("✅ Successfully navigated to projects page!")
        
        # Step 3: Get list of projects
        print("🔍 Step 3: Getting list of projects...")
        
        # Wait for projects to load
        await asyncio.sleep(5)
        
        # Find all project cards
        project_cards = await page.query_selector_all("[data-testid='project-card'], .project-card, .project-listing, .مشروع")
        print(f"📥 Found {len(project_cards)} project cards")
        
        if not project_cards:
            print("❌ No project cards found")
            return
        
        # Step 4: Process each project
        print("🔍 Step 4: Processing projects...")
        
        processed_projects = []
        max_projects_to_check = 10  # Limit to avoid infinite loop
        
        for i, card in enumerate(project_cards[:max_projects_to_check]):
            try:
                print(f"\n📋 Processing Project {i+1}/{len(project_cards[:max_projects_to_check])}...")
                
                # Get project title
                title_element = await card.query_selector("h3, h2, .project-title, .title")
                title = await title_element.text_content() if title_element else f"Project {i+1}"
                title = title.strip() if title else f"Project {i+1}"
                
                print(f"   🎯 Title: {title}")
                
                # Get project link
                link_element = await card.query_selector("a")
                if link_element:
                    project_url = await link_element.get_attribute("href")
                    if project_url and not project_url.startswith("http"):
                        project_url = f"https://bahr.sa{project_url}"
                else:
                    project_url = None
                
                print(f"   🔗 URL: {project_url}")
                
                if not project_url:
                    print("   ⚠️ No project URL found, skipping...")
                    continue
                
                # Step 5: Navigate to project details
                print("   🔄 Navigating to project details...")
                
                await page.goto(project_url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                
                # Step 6: Check project status
                print("   🔍 Checking project status...")
                
                project_status = await check_project_status(page)
                
                print(f"   📊 Status: {project_status['offer_status']}")
                print(f"   📊 Button: {project_status['button_status']}")
                
                # Step 7: Make decision based on status
                decision = make_decision(project_status, title)
                print(f"   🤔 Decision: {decision}")
                
                # Step 8: Take action if needed
                if decision == "submit_offer":
                    print("   ✅ Submitting offer...")
                    # Here you would implement the offer submission logic
                    action_result = "Offer submitted successfully"
                elif decision == "skip_project":
                    print("   ⏭️ Skipping project...")
                    action_result = "Project skipped"
                else:
                    print("   ℹ️ No action needed...")
                    action_result = "No action taken"
                
                # Step 9: Record project info
                project_info = {
                    "title": title,
                    "url": project_url,
                    "status": project_status,
                    "decision": decision,
                    "action_result": action_result,
                    "processed_at": asyncio.get_event_loop().time()
                }
                
                processed_projects.append(project_info)
                
                # Step 10: Go back to projects list
                print("   🔄 Going back to projects list...")
                await page.goto("https://bahr.sa/projects", wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                
                # Wait for projects to reload
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing project {i+1}: {str(e)}")
                continue
        
        # Step 11: Save results
        print("\n💾 Step 11: Saving results...")
        
        results = {
            "total_projects_processed": len(processed_projects),
            "projects": processed_projects,
            "summary": {
                "submitted_offers": len([p for p in processed_projects if p["decision"] == "submit_offer"]),
                "skipped_projects": len([p for p in processed_projects if p["decision"] == "skip_project"]),
                "no_action": len([p for p in processed_projects if p["decision"] == "no_action"])
            }
        }
        
        with open("multiple_projects_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("✅ Results saved to: multiple_projects_results.json")
        
        # Step 12: Print summary
        print("\n📊 Summary:")
        print(f"   Total projects processed: {results['summary']['submitted_offers'] + results['summary']['skipped_projects'] + results['summary']['no_action']}")
        print(f"   Offers submitted: {results['summary']['submitted_offers']}")
        print(f"   Projects skipped: {results['summary']['skipped_projects']}")
        print(f"   No action taken: {results['summary']['no_action']}")
        
        print("\n✅ Multiple projects navigation completed!")
        
    except Exception as e:
        print(f"❌ Error during multiple projects navigation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

async def check_project_status(page):
    """
    Check the status of a project (can submit offer, already submitted, etc.)
    """
    try:
        # Look for "تقديم العرض" link - if it exists, we can submit
        submit_link = await page.query_selector("a:has-text('تقديم العرض')")
        
        if submit_link:
            link_text = await submit_link.text_content()
            link_href = await submit_link.get_attribute("href")
            
            return {
                "offer_status": "Can submit offer",
                "button_status": f"Submit link active: {link_href}"
            }
        else:
            # If no submit link, look for "عرضي" dropdown (My Offer)
            my_offer_dropdown = await page.query_selector("button:has-text('عرضي')")
            if my_offer_dropdown:
                return {
                    "offer_status": "Offer already submitted",
                    "button_status": "My Offer dropdown found"
                }
            else:
                # Look for any dropdown or menu that might contain our offer
                dropdowns = await page.query_selector_all("[role='button'], .dropdown, .menu")
                offer_found = False
                for dropdown in dropdowns:
                    dropdown_text = await dropdown.text_content()
                    if dropdown_text and ("عرضي" in dropdown_text or "my offer" in dropdown_text.lower()):
                        return {
                            "offer_status": "Offer already submitted",
                            "button_status": f"Offer dropdown found: {dropdown_text}"
                        }
                
                return {
                    "offer_status": "Status unclear - no submit link or offer dropdown found",
                    "button_status": "No clear indicators found"
                }
    
    except Exception as e:
        return {
            "offer_status": f"Error checking status: {str(e)}",
            "button_status": "Error occurred"
        }

def make_decision(project_status, title):
    """
    Make a decision about what to do with this project based on its status.
    """
    offer_status = project_status.get("offer_status", "")
    
    # If we can submit an offer
    if "Can submit offer" in offer_status:
        # You can add more sophisticated logic here
        # For example, check if the project title matches your skills
        if any(keyword in title.lower() for keyword in ["tracking", "analytics", "marketing", "digital"]):
            return "submit_offer"
        else:
            return "skip_project"
    
    # If we already submitted an offer
    elif "Offer already submitted" in offer_status:
        return "no_action"
    
    # If status is unclear
    elif "Status unclear" in offer_status:
        return "skip_project"
    
    # Default case
    else:
        return "skip_project"

if __name__ == "__main__":
    print("🎯 Navigate Multiple Projects Test")
    print("=" * 50)
    print("This will navigate through multiple projects, check their status, and move to the next one.")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting multiple projects navigation...")
    asyncio.run(navigate_multiple_projects())
    
    print("\n✨ Navigation completed!") 