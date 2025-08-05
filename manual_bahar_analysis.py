#!/usr/bin/env python3
"""
Manual Bahar website analysis - opens browser for you to manually navigate
and analyze the login form elements.
"""

import asyncio
import json
from datetime import datetime

from jobber_fsm.core.web_driver.playwright import PlaywrightManager

async def manual_bahar_analysis():
    """
    Open browser for manual navigation and analysis of Bahar login.
    """
    print("🔍 Manual Bahar Website Analysis")
    print("=" * 50)
    print()
    print("This tool will:")
    print("1. Open a browser for you")
    print("2. Navigate to Bahar homepage")
    print("3. Let YOU manually navigate to the login page")
    print("4. Analyze the actual login form once you get there")
    print()
    
    try:
        # Initialize browser
        print("🌐 Opening browser...")
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        await browser_manager.async_initialize(eval_mode=True)
        
        page = await browser_manager.get_current_page()
        
        # Navigate to Bahar
        print("📍 Navigating to https://bahr.sa...")
        await page.goto("https://bahr.sa", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        print()
        print("🎯 MANUAL STEPS:")
        print("=" * 30)
        print("1. In the browser that just opened:")
        print("   - Click on the login/دخول button")
        print("   - Wait for the SSO redirect to complete")
        print("   - You should see the actual login form")
        print()
        print("2. When you see the login form, press Enter here")
        print("   - I'll then analyze the form elements")
        print()
        
        input("Press Enter when you've navigated to the login form and can see username/password fields...")
        
        # Now analyze the current page
        print()
        print("🔍 Analyzing current page...")
        current_url = page.url
        title = await page.title()
        
        print(f"📍 Current URL: {current_url}")
        print(f"📝 Page Title: {title}")
        
        # Analyze form elements
        forms = await page.query_selector_all("form")
        print(f"📝 Found {len(forms)} forms on the page")
        
        form_analysis = []
        
        for i, form in enumerate(forms):
            print(f"\n📋 Analyzing Form {i+1}:")
            
            # Form attributes
            action = await form.get_attribute('action')
            method = await form.get_attribute('method')
            form_id = await form.get_attribute('id')
            form_class = await form.get_attribute('class')
            
            print(f"   Action: {action}")
            print(f"   Method: {method}")
            print(f"   ID: {form_id}")
            print(f"   Class: {form_class}")
            
            # Find inputs
            inputs = await form.query_selector_all("input")
            print(f"   Found {len(inputs)} input fields:")
            
            input_data = []
            for j, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_placeholder = await input_elem.get_attribute('placeholder')
                input_class = await input_elem.get_attribute('class')
                
                print(f"      Input {j+1}: type={input_type}, name={input_name}, id={input_id}")
                print(f"                 placeholder={input_placeholder}")
                
                input_data.append({
                    "type": input_type,
                    "name": input_name,
                    "id": input_id,
                    "placeholder": input_placeholder,
                    "class": input_class
                })
            
            # Find buttons
            buttons = await form.query_selector_all("button, input[type='submit']")
            print(f"   Found {len(buttons)} buttons:")
            
            button_data = []
            for j, button in enumerate(buttons):
                button_type = await button.get_attribute('type')
                button_text = await button.text_content()
                button_id = await button.get_attribute('id')
                button_class = await button.get_attribute('class')
                
                print(f"      Button {j+1}: type={button_type}, text='{button_text.strip() if button_text else ''}'")
                print(f"                   id={button_id}")
                
                button_data.append({
                    "type": button_type,
                    "text": button_text.strip() if button_text else "",
                    "id": button_id,
                    "class": button_class
                })
            
            form_analysis.append({
                "form_index": i,
                "action": action,
                "method": method,
                "id": form_id,
                "class": form_class,
                "inputs": input_data,
                "buttons": button_data
            })
        
        # Also check for inputs outside forms
        all_inputs = await page.query_selector_all("input")
        standalone_inputs = []
        
        print(f"\n🔍 Total inputs on page: {len(all_inputs)}")
        
        for input_elem in all_inputs:
            # Check if this input is inside a form
            form_parent = None
            try:
                form_parent = await input_elem.query_selector("xpath=ancestor::form")
            except:
                pass
            
            if not form_parent:  # Standalone input
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_placeholder = await input_elem.get_attribute('placeholder')
                
                standalone_inputs.append({
                    "type": input_type,
                    "name": input_name,
                    "id": input_id,
                    "placeholder": input_placeholder
                })
        
        if standalone_inputs:
            print(f"\n📝 Found {len(standalone_inputs)} standalone inputs:")
            for i, input_data in enumerate(standalone_inputs):
                print(f"   Input {i+1}: type={input_data['type']}, name={input_data['name']}, id={input_data['id']}")
        
        # Generate selectors
        print("\n🔧 GENERATING SELECTORS...")
        print("=" * 30)
        
        username_selectors = []
        password_selectors = []
        submit_selectors = []
        
        # Analyze all forms
        for form in form_analysis:
            for input_data in form["inputs"]:
                input_type = (input_data.get("type") or "").lower()
                input_name = (input_data.get("name") or "").lower()
                input_id = input_data.get("id") or ""
                input_placeholder = (input_data.get("placeholder") or "").lower()
                
                # Username/email field detection
                if (input_type in ["email", "text"] or
                    "email" in input_name or "username" in input_name or "user" in input_name or
                    "email" in input_placeholder or "username" in input_placeholder or "user" in input_placeholder):
                    
                    if input_name:
                        username_selectors.append(f"input[name='{input_data['name']}']")
                    if input_id:
                        username_selectors.append(f"#{input_id}")
                        username_selectors.append(f"input[id='{input_id}']")
                
                # Password field detection
                if (input_type == "password" or
                    "password" in input_name or "pass" in input_name or
                    "password" in input_placeholder or "pass" in input_placeholder):
                    
                    if input_name:
                        password_selectors.append(f"input[name='{input_data['name']}']")
                    if input_id:
                        password_selectors.append(f"#{input_id}")
                        password_selectors.append(f"input[id='{input_id}']")
            
            # Submit button detection
            for button_data in form["buttons"]:
                button_type = (button_data.get("type") or "").lower()
                button_text = (button_data.get("text") or "").lower()
                button_id = button_data.get("id") or ""
                
                if (button_type == "submit" or
                    "login" in button_text or "sign in" in button_text or "submit" in button_text or
                    "دخول" in button_text or "تسجيل" in button_text):
                    
                    if button_id:
                        submit_selectors.append(f"#{button_id}")
                        submit_selectors.append(f"button[id='{button_id}']")
                    if button_text:
                        submit_selectors.append(f"button:has-text('{button_data['text']}')")
                    submit_selectors.append("button[type='submit']")
        
        # Remove duplicates
        username_selectors = list(set(username_selectors))
        password_selectors = list(set(password_selectors))
        submit_selectors = list(set(submit_selectors))
        
        print("\n🎯 RECOMMENDED SELECTORS:")
        print("=" * 30)
        
        print(f"\n📧 Username/Email Selectors ({len(username_selectors)} found):")
        for selector in username_selectors:
            print(f"   {selector}")
        
        print(f"\n🔒 Password Selectors ({len(password_selectors)} found):")
        for selector in password_selectors:
            print(f"   {selector}")
        
        print(f"\n🚀 Submit Button Selectors ({len(submit_selectors)} found):")
        for selector in submit_selectors:
            print(f"   {selector}")
        
        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "url": current_url,
            "title": title,
            "forms": form_analysis,
            "standalone_inputs": standalone_inputs,
            "recommended_selectors": {
                "username": username_selectors,
                "password": password_selectors,
                "submit": submit_selectors
            }
        }
        
        with open("manual_bahar_analysis_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to manual_bahar_analysis_results.json")
        
        # Generate code snippet
        code_snippet = f'''
# BAHAR LOGIN SELECTORS - Updated from manual analysis
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# URL: {current_url}

username_selectors = {username_selectors}

password_selectors = {password_selectors}

submit_selectors = {submit_selectors}
'''
        
        with open("bahar_manual_selectors.py", "w") as f:
            f.write(code_snippet)
        
        print("💾 Selectors saved to bahar_manual_selectors.py")
        
        print("\n📋 NEXT STEPS:")
        print("1. Review the generated selectors")
        print("2. Update login_bahar.py with the new selectors")
        print("3. Test the login functionality")
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🧹 Cleaning up...")
        try:
            await browser_manager.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(manual_bahar_analysis())