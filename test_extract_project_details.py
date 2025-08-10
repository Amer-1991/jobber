#!/usr/bin/env python3
"""
Test to extract complete project details from the project page.
This will capture budget, project description, and title before proposal submission.
"""

import asyncio
import json
import os
from dotenv import load_dotenv

from jobber_fsm.core.skills.login_bahar_esso import login_bahar_esso
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def extract_project_details():
    """
    Extract complete project details from the project page.
    """
    print("🔍 Extracting Complete Project Details...")
    
    # Import required modules
    from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
    
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
        
        # Step 2: Navigate to the project page (not the proposal form)
        print("🔄 Step 2: Navigating to project details page...")
        
        # From the interaction log, we know the project URL
        project_url = "https://bahr.sa/projects/recruitments/01987f02-014f-74b7-96ef-caa0578f2496"
        
        await page.goto(project_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if "recruitments" not in current_url:
            print("❌ Failed to navigate to project page")
            return
        
        print("✅ Successfully navigated to project page!")
        
        # Step 3: Extract project title
        print("🔍 Step 3: Extracting project title...")
        
        # Try different selectors for project title
        title_selectors = [
            "h1",
            ".project-title",
            ".title",
            "[data-testid='project-title']",
            ".project-name",
            ".recruitment-title"
        ]
        
        project_title = ""
        for selector in title_selectors:
            title_elem = await page.query_selector(selector)
            if title_elem:
                title_text = await title_elem.text_content()
                if title_text and len(title_text.strip()) > 5:
                    project_title = title_text.strip()
                    print(f"✅ Found project title: {project_title}")
                    break
        
        if not project_title:
            print("⚠️ Could not find project title with standard selectors")
            # Try to find it in the page text
            text_content = await get_dom_with_content_type("text_only")
            
            # Look for title patterns in the text
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 10 and len(line) < 100 and ("TRACKING" in line or "Google Analytics" in line):
                    project_title = line
                    print(f"✅ Found project title in text: {project_title}")
                    break
        
        # Step 4: Extract project budget
        print("🔍 Step 4: Extracting project budget...")
        
        # Try different selectors for budget
        budget_selectors = [
            ".budget",
            ".project-budget",
            "[data-testid='budget']",
            ".price",
            ".amount",
            ".cost",
            ".budget-amount",
            ".project-cost"
        ]
        
        project_budget = ""
        for selector in budget_selectors:
            budget_elem = await page.query_selector(selector)
            if budget_elem:
                budget_text = await budget_elem.text_content()
                if budget_text and any(currency in budget_text for currency in ["ريال", "SAR", "$", "دولار", "ريال سعودي"]):
                    project_budget = budget_text.strip()
                    print(f"✅ Found project budget: {project_budget}")
                    break
        
        if not project_budget:
            print("⚠️ Could not find budget with standard selectors")
            # Look for budget in page text
            text_content = await get_dom_with_content_type("text_only")
            
            # Look for budget patterns
            budget_keywords = ["الميزانية", "budget", "ميزانية", "التكلفة", "السعر"]
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in budget_keywords):
                    if any(currency in line for currency in ["ريال", "SAR", "$", "دولار"]):
                        project_budget = line
                        print(f"✅ Found budget in text: {project_budget}")
                        break
        
        # Step 5: Extract project description
        print("🔍 Step 5: Extracting project description...")
        
        # Try different selectors for description
        description_selectors = [
            ".description",
            ".project-description",
            "[data-testid='description']",
            ".details",
            ".project-details",
            ".content",
            ".project-content",
            ".recruitment-description"
        ]
        
        project_description = ""
        for selector in description_selectors:
            desc_elem = await page.query_selector(selector)
            if desc_elem:
                desc_text = await desc_elem.text_content()
                if desc_text and len(desc_text.strip()) > 50:
                    project_description = desc_text.strip()
                    print(f"✅ Found project description: {project_description[:100]}...")
                    break
        
        if not project_description:
            print("⚠️ Could not find description with standard selectors")
            # Look for description in page text
            text_content = await get_dom_with_content_type("text_only")
            
            # Look for longer text blocks that might be descriptions
            lines = text_content.split('\n')
            description_lines = []
            for line in lines:
                line = line.strip()
                if len(line) > 30 and not any(skip in line for skip in ["القائمة", "menu", "navigation", "filter", "تصفية", "فرز"]):
                    description_lines.append(line)
            
            if description_lines:
                project_description = " ".join(description_lines[:5])  # Take first 5 lines
                print(f"✅ Found description in text: {project_description[:100]}...")
        
        # Step 6: Extract additional project details
        print("🔍 Step 6: Extracting additional project details...")
        
        # Get all text content for comprehensive analysis
        text_content = await get_dom_with_content_type("text_only")
        
        # Look for specific project details
        project_details = {}
        
        # Look for job category
        category_keywords = ["الوظيفة", "job", "category", "التصنيف"]
        for line in text_content.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in category_keywords):
                if "تسويق" in line or "marketing" in line.lower():
                    project_details["category"] = line
                    break
        
        # Look for location
        location_keywords = ["الموقع", "location", "مكان"]
        for line in text_content.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in location_keywords):
                if "عن بُعد" in line or "remote" in line.lower():
                    project_details["location"] = line
                    break
        
        # Look for start date
        date_keywords = ["تاريخ البدء", "start date", "تاريخ"]
        for line in text_content.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in date_keywords):
                if "فوري" in line or "immediate" in line.lower():
                    project_details["start_date"] = line
                    break
        
        # Look for freelancers needed
        freelancer_keywords = ["عدد المستقلين", "freelancers", "المطلوب"]
        for line in text_content.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in freelancer_keywords):
                if any(char.isdigit() for char in line):
                    project_details["freelancers_needed"] = line
                    break
        
        # Look for project status (open/closed)
        status_keywords = ["مفتوح", "مغلق", "open", "closed", "status"]
        for line in text_content.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in status_keywords):
                if "مفتوح" in line:
                    project_details["status"] = "مفتوح (Open)"
                    break
                elif "مغلق" in line:
                    project_details["status"] = "مغلق (Closed)"
                    break
        
        # Look for available offers count
        offers_keywords = ["العروض المتاحة", "available offers", "offers"]
        for i, line in enumerate(text_content.split('\n')):
            line = line.strip()
            if any(keyword in line for keyword in offers_keywords):
                # Get the next line which should contain the number
                if i + 1 < len(text_content.split('\n')):
                    next_line = text_content.split('\n')[i + 1].strip()
                    if any(char.isdigit() for char in next_line):
                        project_details["available_offers"] = f"{line}: {next_line}"
                        break
        
        # Look for deadline
        deadline_keywords = ["الموعد النهائي", "deadline", "تاريخ الانتهاء"]
        for i, line in enumerate(text_content.split('\n')):
            line = line.strip()
            if any(keyword in line for keyword in deadline_keywords):
                # Get the next line which should contain the date
                if i + 1 < len(text_content.split('\n')):
                    next_line = text_content.split('\n')[i + 1].strip()
                    if any(char.isdigit() for char in next_line):
                        project_details["deadline"] = f"{line}: {next_line}"
                        break
        
        # Look for freelancers needed (enhanced)
        freelancer_keywords = ["عدد المستقلين", "freelancers", "المطلوب"]
        for i, line in enumerate(text_content.split('\n')):
            line = line.strip()
            if any(keyword in line for keyword in freelancer_keywords):
                # Get the next line which should contain the number
                if i + 1 < len(text_content.split('\n')):
                    next_line = text_content.split('\n')[i + 1].strip()
                    if any(char.isdigit() for char in next_line):
                        project_details["freelancers_needed"] = f"{line}: {next_line}"
                        break
        
        # Step 7: Compile complete project information
        print("📋 Step 7: Compiling complete project information...")
        
        project_info = {
            "title": project_title,
            "budget": project_budget,
            "description": project_description,
            "url": current_url,
            "project_id": "01987f02-014f-74b7-96ef-caa0578f2496",
            "additional_details": project_details
        }
        
        print("\n📋 Complete Project Information:")
        print("=" * 50)
        print(f"🎯 Title: {project_info['title']}")
        print(f"💰 Budget: {project_info['budget']}")
        print(f"📄 Description: {project_info['description'][:200]}...")
        print(f"🔗 URL: {project_info['url']}")
        print(f"🆔 Project ID: {project_info['project_id']}")
        
        if project_details:
            print("\n📊 Additional Details:")
            for key, value in project_details.items():
                print(f"   {key}: {value}")
        
        # Step 8: Check if we've already sent an offer
        print("🔍 Step 8: Checking if we've already sent an offer...")
        
        # Look for "تقديم العرض" link - if it exists, we can submit
        submit_link = await page.query_selector("a:has-text('تقديم العرض')")
        if submit_link:
            link_text = await submit_link.text_content()
            link_href = await submit_link.get_attribute("href")
            
            project_details["offer_status"] = "Can submit offer"
            project_details["button_status"] = f"Submit link active: {link_href}"
        else:
            # If no submit button, look for "عرضي" dropdown (My Offer)
            my_offer_dropdown = await page.query_selector("button:has-text('عرضي')")
            if my_offer_dropdown:
                project_details["offer_status"] = "Offer already submitted"
                project_details["button_status"] = "My Offer dropdown found"
            else:
                # Look for any dropdown or menu that might contain our offer
                dropdowns = await page.query_selector_all("[role='button'], .dropdown, .menu")
                offer_found = False
                for dropdown in dropdowns:
                    dropdown_text = await dropdown.text_content()
                    if dropdown_text and ("عرضي" in dropdown_text or "my offer" in dropdown_text.lower()):
                        project_details["offer_status"] = "Offer already submitted"
                        project_details["button_status"] = f"Offer dropdown found: {dropdown_text}"
                        offer_found = True
                        break
                
                if not offer_found:
                    project_details["offer_status"] = "Status unclear - no submit button or offer dropdown found"
                    project_details["button_status"] = "No clear indicators found"
        
        print(f"✅ Offer status: {project_details['offer_status']}")
        print(f"✅ Button status: {project_details['button_status']}")
        
        # Step 9: Save project information
        print("\n💾 Step 9: Saving project information...")
        
        with open("project_details.json", "w", encoding="utf-8") as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)
        
        print("✅ Project details saved to: project_details.json")
        
        # Step 10: Save full page text for analysis
        with open("project_page_text.txt", "w", encoding="utf-8") as f:
            f.write(text_content)
        
        print("✅ Project page text saved to: project_page_text.txt")
        
        print("\n✅ Project details extraction completed!")
        print("📁 Check the saved files:")
        print("   - project_details.json (structured data)")
        print("   - project_page_text.txt (full page text)")
        
        return project_info
        
    except Exception as e:
        print(f"❌ Error during project extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if browser_manager:
            print("\n🧹 Cleaning up...")
            try:
                await browser_manager.stop_playwright()
            except:
                pass

if __name__ == "__main__":
    print("🎯 Project Details Extraction")
    print("=" * 50)
    print("This will extract complete project information:")
    print("1. Project title")
    print("2. Project budget (if specified)")
    print("3. Project description")
    print("4. Additional project details")
    print()
    
    # Check credentials
    load_dotenv()
    if not (os.getenv("BAHAR_USERNAME") and os.getenv("BAHAR_PASSWORD")):
        print("❌ Please set BAHAR_USERNAME and BAHAR_PASSWORD in .env file")
        exit(1)
    
    print("🚀 Starting project details extraction...")
    asyncio.run(extract_project_details())
    
    print("\n✨ Extraction completed!") 