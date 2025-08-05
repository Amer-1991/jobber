#!/usr/bin/env python3
"""
Script to analyze the Bahar website structure and identify login form selectors.
This will help us update the login_bahar.py skill with correct selectors.
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.core.skills.get_screenshot import get_screenshot

async def analyze_bahar_website():
    """
    Analyze the Bahar website to identify login form elements and structure.
    """
    print("🔍 Starting Bahar website analysis...")
    
    # Load environment variables
    load_dotenv()
    
    # Get Bahar URL from environment or use default
    bahar_url = os.getenv("BAHAR_URL", "https://bahr.sa")
    
    try:
        # Initialize the browser
        print("🌐 Initializing browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        # Get current page
        page = await browser_manager.get_current_page()
        
        # Navigate to Bahar homepage first
        print(f"📍 Navigating to {bahar_url}...")
        await page.goto(bahar_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)  # Wait for page to fully load
        
        # Take screenshot of homepage
        print("📸 Taking homepage screenshot...")
        await get_screenshot()
        
        # Analyze homepage for login links/buttons
        print("🔍 Analyzing homepage structure...")
        homepage_analysis = await analyze_page_structure(page, "homepage")
        
        # Look for login page link
        login_found = await find_and_navigate_to_login(page, bahar_url)
        
        if login_found:
            print("✅ Login page found! Analyzing login form...")
            await asyncio.sleep(2)  # Wait for login page to load
            
            # Take screenshot of login page
            print("📸 Taking login page screenshot...")
            await get_screenshot()
            
            # Analyze login page structure
            print("🔍 Analyzing login form structure...")
            login_analysis = await analyze_login_form(page)
            
            # Save analysis results
            analysis_results = {
                "timestamp": datetime.now().isoformat(),
                "bahar_url": bahar_url,
                "homepage_analysis": homepage_analysis,
                "login_analysis": login_analysis,
                "current_url": page.url
            }
            
            # Save to file
            with open("bahar_analysis_results.json", "w") as f:
                json.dump(analysis_results, f, indent=2)
            
            print("💾 Analysis results saved to bahar_analysis_results.json")
            
            # Generate updated selectors
            await generate_updated_selectors(login_analysis)
            
        else:
            print("❌ Could not find login page automatically")
            print("🔍 Please manually navigate to login page and run login form analysis")
            
            # Save what we found so far
            analysis_results = {
                "timestamp": datetime.now().isoformat(),
                "bahar_url": bahar_url,
                "homepage_analysis": homepage_analysis,
                "current_url": page.url,
                "note": "Login page not found automatically"
            }
            
            with open("bahar_analysis_results.json", "w") as f:
                json.dump(analysis_results, f, indent=2)
        
        # Keep browser open for manual inspection
        print("\n🔍 MANUAL INSPECTION:")
        print("The browser will stay open for you to manually inspect the website.")
        print("You can:")
        print("1. Navigate to the login page manually")
        print("2. Right-click on login elements and 'Inspect Element'")
        print("3. Use browser extensions to record selectors")
        print("4. Press Enter when done to close the browser")
        
        input("Press Enter to close browser and complete analysis...")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        try:
            await browser_manager.close()
        except:
            pass

async def analyze_page_structure(page, page_type):
    """
    Analyze the structure of a page to find relevant elements.
    """
    try:
        # Get page title and URL
        title = await page.title()
        url = page.url
        
        # Look for common login-related elements
        login_indicators = [
            # Common login links/buttons
            "a[href*='login']",
            "a[href*='signin']", 
            "a[href*='sign-in']",
            "a[href*='auth']",
            "button:has-text('login')",
            "button:has-text('sign in')",
            "button:has-text('تسجيل دخول')",  # Arabic for login
            ".login",
            ".signin",
            ".auth",
            
            # Navigation elements
            ".navbar",
            ".header",
            ".navigation",
            ".menu",
            
            # User account related
            "[data-testid*='login']",
            "[data-testid*='auth']",
            ".user-menu",
            ".account"
        ]
        
        found_elements = {}
        
        for selector in login_indicators:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    element_info = []
                    for element in elements[:3]:  # Limit to first 3 matches
                        text = await element.text_content()
                        href = await element.get_attribute('href') if await element.get_attribute('href') else None
                        element_info.append({
                            "text": text.strip() if text else "",
                            "href": href,
                            "selector": selector
                        })
                    found_elements[selector] = element_info
            except:
                continue
        
        return {
            "page_type": page_type,
            "title": title,
            "url": url,
            "found_login_elements": found_elements
        }
        
    except Exception as e:
        return {
            "page_type": page_type,
            "error": str(e)
        }

async def find_and_navigate_to_login(page, base_url):
    """
    Try to find and navigate to the login page.
    """
    try:
        # Common login page paths to try
        login_paths = [
            "/login",
            "/signin", 
            "/sign-in",
            "/auth/login",
            "/user/login",
            "/account/login",
            "/تسجيل-دخول"  # Arabic login path
        ]
        
        # First, try clicking login links on current page
        login_selectors = [
            "a[href*='login']",
            "a[href*='signin']",
            "a[href*='sign-in']",
            "button:has-text('login')",
            "button:has-text('sign in')",
            "button:has-text('تسجيل دخول')",
            ".login a",
            ".signin a",
            ".auth a"
        ]
        
        for selector in login_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"🔗 Found login link with selector: {selector}")
                    await element.click()
                    print("⏳ Waiting for redirect (SSO might take time)...")
                    await page.wait_for_load_state("networkidle", timeout=30000)  # Wait up to 30 seconds
                    await asyncio.sleep(5)  # Extra wait for SSO redirect
                    
                    # Check if we're on a login page now
                    current_url = page.url.lower()
                    print(f"📍 Current URL after redirect: {page.url}")
                    # Check for SSO/auth URLs or login indicators
                    if any(term in current_url for term in ['login', 'signin', 'auth', 'sso', 'oauth', 'esso']):
                        print(f"✅ Successfully navigated to login/SSO page: {page.url}")
                        return True
            except:
                continue
        
        # If clicking didn't work, try direct navigation
        for path in login_paths:
            try:
                login_url = base_url.rstrip('/') + path
                print(f"🔗 Trying direct navigation to: {login_url}")
                
                response = await page.goto(login_url, wait_until="networkidle", timeout=30000)
                print("⏳ Waiting for SSO redirect to complete...")
                await asyncio.sleep(5)
                
                # Check if page loaded successfully (not 404)
                if response and response.status < 400:
                    current_url = page.url.lower()
                    print(f"📍 Current URL after direct navigation: {page.url}")
                    if any(term in current_url for term in ['login', 'signin', 'auth', 'sso', 'oauth', 'esso']):
                        print(f"✅ Successfully navigated to login/SSO page: {page.url}")
                        return True
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"❌ Error finding login page: {str(e)}")
        return False

async def analyze_login_form(page):
    """
    Analyze the login form to identify input fields and submit buttons.
    """
    try:
        # Get page info
        title = await page.title()
        url = page.url
        
        # Look for form elements
        forms = await page.query_selector_all("form")
        
        form_analysis = []
        
        for i, form in enumerate(forms):
            print(f"📝 Analyzing form {i+1}...")
            
            # Get form attributes
            form_action = await form.get_attribute('action')
            form_method = await form.get_attribute('method')
            form_id = await form.get_attribute('id')
            form_class = await form.get_attribute('class')
            
            # Find input fields within this form
            inputs = await form.query_selector_all("input")
            input_analysis = []
            
            for input_elem in inputs:
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_class = await input_elem.get_attribute('class')
                input_placeholder = await input_elem.get_attribute('placeholder')
                input_value = await input_elem.get_attribute('value')
                
                input_analysis.append({
                    "type": input_type,
                    "name": input_name,
                    "id": input_id,
                    "class": input_class,
                    "placeholder": input_placeholder,
                    "value": input_value,
                    "selector_candidates": [
                        f"input[name='{input_name}']" if input_name else None,
                        f"input[id='{input_id}']" if input_id else None,
                        f"input[type='{input_type}']" if input_type else None,
                        f"#{input_id}" if input_id else None
                    ]
                })
            
            # Find buttons within this form
            buttons = await form.query_selector_all("button, input[type='submit']")
            button_analysis = []
            
            for button in buttons:
                button_type = await button.get_attribute('type')
                button_text = await button.text_content()
                button_id = await button.get_attribute('id')
                button_class = await button.get_attribute('class')
                button_value = await button.get_attribute('value')
                
                button_analysis.append({
                    "type": button_type,
                    "text": button_text.strip() if button_text else "",
                    "id": button_id,
                    "class": button_class,
                    "value": button_value,
                    "selector_candidates": [
                        f"button[type='{button_type}']" if button_type else None,
                        f"#{button_id}" if button_id else None,
                        f"button:has-text('{button_text.strip()}')" if button_text and button_text.strip() else None
                    ]
                })
            
            form_analysis.append({
                "form_index": i,
                "action": form_action,
                "method": form_method,
                "id": form_id,
                "class": form_class,
                "inputs": input_analysis,
                "buttons": button_analysis
            })
        
        # Also look for input fields outside of forms (some sites don't use form tags)
        all_inputs = await page.query_selector_all("input")
        standalone_inputs = []
        
        for input_elem in all_inputs:
            # Check if this input is already part of a form we analyzed
            form_parent = await input_elem.query_selector("xpath=ancestor::form")
            if not form_parent:  # Input is not inside a form
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_class = await input_elem.get_attribute('class')
                input_placeholder = await input_elem.get_attribute('placeholder')
                
                standalone_inputs.append({
                    "type": input_type,
                    "name": input_name,
                    "id": input_id,
                    "class": input_class,
                    "placeholder": input_placeholder,
                    "selector_candidates": [
                        f"input[name='{input_name}']" if input_name else None,
                        f"input[id='{input_id}']" if input_id else None,
                        f"#{input_id}" if input_id else None
                    ]
                })
        
        return {
            "page_title": title,
            "page_url": url,
            "forms": form_analysis,
            "standalone_inputs": standalone_inputs,
            "total_forms": len(forms),
            "total_inputs": len(all_inputs)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "page_url": page.url if page else "unknown"
        }

async def generate_updated_selectors(login_analysis):
    """
    Generate updated selectors based on the analysis results.
    """
    try:
        print("\n🔧 GENERATING UPDATED SELECTORS...")
        print("=" * 50)
        
        username_selectors = []
        password_selectors = []
        submit_selectors = []
        
        # Analyze forms
        if "forms" in login_analysis:
            for form in login_analysis["forms"]:
                print(f"\n📝 Form {form['form_index'] + 1} Analysis:")
                if form.get("action"):
                    print(f"   Action: {form['action']}")
                
                # Analyze inputs
                for input_data in form.get("inputs", []):
                    input_type = input_data.get("type", "").lower()
                    input_name = input_data.get("name", "")
                    input_placeholder = input_data.get("placeholder", "").lower()
                    
                    print(f"   Input: type={input_type}, name={input_name}, placeholder={input_placeholder}")
                    
                    # Identify username/email fields
                    if (input_type in ["email", "text"] or 
                        "email" in input_name.lower() or 
                        "username" in input_name.lower() or
                        "user" in input_name.lower() or
                        "email" in input_placeholder or
                        "username" in input_placeholder):
                        
                        for selector in input_data.get("selector_candidates", []):
                            if selector:
                                username_selectors.append(selector)
                    
                    # Identify password fields
                    if (input_type == "password" or
                        "password" in input_name.lower() or
                        "pass" in input_name.lower() or
                        "password" in input_placeholder):
                        
                        for selector in input_data.get("selector_candidates", []):
                            if selector:
                                password_selectors.append(selector)
                
                # Analyze buttons
                for button_data in form.get("buttons", []):
                    button_text = button_data.get("text", "").lower()
                    button_type = button_data.get("type", "").lower()
                    
                    print(f"   Button: type={button_type}, text={button_text}")
                    
                    # Identify submit buttons
                    if (button_type == "submit" or
                        "login" in button_text or
                        "sign in" in button_text or
                        "تسجيل دخول" in button_text or
                        "دخول" in button_text):
                        
                        for selector in button_data.get("selector_candidates", []):
                            if selector:
                                submit_selectors.append(selector)
        
        # Remove duplicates and None values
        username_selectors = list(set(filter(None, username_selectors)))
        password_selectors = list(set(filter(None, password_selectors)))
        submit_selectors = list(set(filter(None, submit_selectors)))
        
        print("\n🎯 RECOMMENDED SELECTORS:")
        print("=" * 30)
        
        print("\n📧 Username/Email Selectors:")
        for selector in username_selectors[:5]:  # Show top 5
            print(f"   {selector}")
        
        print("\n🔒 Password Selectors:")
        for selector in password_selectors[:5]:  # Show top 5
            print(f"   {selector}")
        
        print("\n🚀 Submit Button Selectors:")
        for selector in submit_selectors[:5]:  # Show top 5
            print(f"   {selector}")
        
        # Generate updated login_bahar.py code snippet
        updated_code = f'''
# UPDATED SELECTORS FOR BAHAR WEBSITE
# Generated from website analysis on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

username_selectors = {username_selectors}

password_selectors = {password_selectors}

submit_selectors = {submit_selectors}
'''
        
        with open("bahar_updated_selectors.py", "w") as f:
            f.write(updated_code)
        
        print(f"\n💾 Updated selectors saved to bahar_updated_selectors.py")
        print("\n📋 Next steps:")
        print("1. Review the generated selectors")
        print("2. Update login_bahar.py with the new selectors")
        print("3. Test the updated login functionality")
        
    except Exception as e:
        print(f"❌ Error generating selectors: {str(e)}")

if __name__ == "__main__":
    print("🎯 Bahar Website Analysis Tool")
    print("=" * 50)
    
    asyncio.run(analyze_bahar_website())
    
    print("\n✨ Analysis completed!")