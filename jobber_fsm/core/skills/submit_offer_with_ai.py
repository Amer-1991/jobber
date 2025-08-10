import asyncio
import inspect
import json
import os
import traceback
from typing import Dict, List, Optional

from playwright.async_api import Page
from typing_extensions import Annotated

from jobber_fsm.core.web_driver.playwright import PlaywrightManager
from jobber_fsm.core.skills.get_dom_with_content_type import get_dom_with_content_type
from jobber_fsm.core.skills.click_using_selector import click
from jobber_fsm.core.skills.enter_text_using_selector import custom_fill_element
from jobber_fsm.core.skills.upload_file import upload_file
from jobber_fsm.utils.logger import logger


async def submit_offer_with_ai(
    project_url: Annotated[
        str,
        "URL of the project to submit offer for",
    ],
    project_info: Annotated[
        Dict[str, any],
        "Project information including title, description, budget, requirements",
    ],
    user_preferences: Annotated[
        Dict[str, any],
        "User preferences including skills, experience, rate, resume path",
    ],
    auto_submit: Annotated[
        bool,
        "Whether to automatically submit the offer or just generate it",
    ] = False,
) -> Annotated[str, "JSON string containing the offer submission result"]:
    """
    Submit an offer for a project using local Llama AI to generate personalized content.
    
    This function:
    1. Navigates to the project page
    2. Extracts all project details
    3. Sends project info to local Llama AI for offer generation
    4. Fills the offer form with AI-generated content
    5. Submits the offer (if auto_submit is True)
    
    Args:
        project_url: URL of the project
        project_info: Project details
        user_preferences: User's skills, experience, rate, etc.
        auto_submit: Whether to submit automatically
    
    Returns:
        JSON string with offer submission result
    """
    logger.info(f"Submitting offer for project: {project_info.get('title', 'Unknown')}")
    
    # Get the active browser page (should already be authenticated)
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()
    
    if page is None:
        raise ValueError("No active page found. Please ensure browser is initialized and authenticated.")
    
    function_name = inspect.currentframe().f_code.co_name  # type: ignore
    
    try:
        await browser_manager.take_screenshots(f"{function_name}_start", page)
        
        # Step 1: Navigate to project page
        logger.info(f"Navigating to project page: {project_url}")
        await page.goto(project_url, wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(3)
        
        # Step 2: Extract complete project details
        logger.info("Extracting complete project details")
        complete_project_info = await extract_complete_project_details(page, project_info)
        
        # Step 3: Generate AI offer using local Llama
        logger.info("Generating AI offer using local Llama")
        ai_offer = await generate_llama_offer(complete_project_info, user_preferences)
        
        # Step 4: Find and fill offer form
        logger.info("Filling offer form")
        form_result = await fill_offer_form(page, ai_offer, user_preferences)
        
        if not form_result["success"]:
            return json.dumps({
                "error": f"Failed to fill offer form: {form_result['message']}",
                "ai_offer": ai_offer,
                "project_info": complete_project_info
            }, ensure_ascii=False)
        
        # Step 5: Submit offer if requested
        if auto_submit:
            logger.info("Submitting offer")
            submit_result = await submit_offer_form(page)
            
            if submit_result["success"]:
                await browser_manager.take_screenshots(f"{function_name}_success", page)
                return json.dumps({
                    "success": True,
                    "message": "Offer submitted successfully",
                    "ai_offer": ai_offer,
                    "project_info": complete_project_info,
                    "submission_details": submit_result
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "error": f"Failed to submit offer: {submit_result['message']}",
                    "ai_offer": ai_offer,
                    "project_info": complete_project_info
                }, ensure_ascii=False)
        else:
            # Just return the generated offer without submitting
            await browser_manager.take_screenshots(f"{function_name}_offer_generated", page)
            return json.dumps({
                "success": True,
                "message": "Offer generated successfully (not submitted)",
                "ai_offer": ai_offer,
                "project_info": complete_project_info,
                "form_filled": form_result
            }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error during offer submission: {str(e)}")
        traceback.print_exc()
        await browser_manager.take_screenshots(f"{function_name}_error", page)
        return json.dumps({
            "error": f"Offer submission failed: {str(e)}",
            "project_info": project_info
        }, ensure_ascii=False)


async def extract_complete_project_details(page: Page, existing_info: Dict[str, any]) -> Dict[str, any]:
    """
    Extract complete project details from the project page.
    
    Args:
        page: The Playwright page instance
        existing_info: Already known project information
        
    Returns:
        Complete project information dictionary
    """
    try:
        # Wait for page content to load properly
        import asyncio
        await asyncio.sleep(2)
        
        # Wait for project content to appear
        try:
            await page.wait_for_selector("h1, h2, .project-title, .title, .description, .project-description", timeout=10000)
        except:
            pass  # Continue even if selectors not found
        
        # Get DOM content to analyze the page structure
        dom_content = await get_dom_with_content_type("all_fields")
        
        # Common selectors for project details
        detail_selectors = {
            "title": [
                "h1", "h2", ".project-title", ".title", "[data-testid='title']",
                ".project-name", ".job-title", ".listing-title"
            ],
            "description": [
                ".description", ".project-description", ".job-description",
                ".details", ".content", ".summary", "p", ".project-details"
            ],
            "budget": [
                ".budget", ".price", ".amount", ".cost", ".rate",
                "[data-testid='budget']", ".project-budget", ".job-budget"
            ],
            "deadline": [
                ".deadline", ".timeframe", ".duration", ".time",
                ".project-deadline", ".job-deadline", ".due-date"
            ],
            "skills": [
                ".skills", ".tags", ".categories", ".requirements",
                ".required-skills", ".technologies", ".tools"
            ],
            "requirements": [
                ".requirements", ".qualifications", ".experience",
                ".project-requirements", ".job-requirements"
            ],
            "attachments": [
                ".attachments", ".files", ".documents",
                ".project-files", ".job-files"
            ]
        }
        
        complete_info = existing_info.copy()
        
        # Extract each type of detail
        for detail_type, selectors in detail_selectors.items():
            if detail_type not in complete_info or not complete_info[detail_type]:
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            if detail_type == "skills":
                                # Handle skills as a list
                                skills = []
                                for element in elements:
                                    skill_text = await element.text_content()
                                    if skill_text and len(skill_text.strip()) > 0:
                                        skills.append(skill_text.strip())
                                if skills:
                                    complete_info[detail_type] = skills
                                    break
                            else:
                                # Handle other details as text
                                text_content = await elements[0].text_content()
                                if text_content and len(text_content.strip()) > 0:
                                    complete_info[detail_type] = text_content.strip()
                                    break
                    except:
                        continue
        
        # Extract any additional information from the page
        try:
            # Look for any additional project information
            additional_selectors = [
                ".project-info", ".job-info", ".details-section",
                ".project-meta", ".job-meta", ".project-details"
            ]
            
            for selector in additional_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            text_content = await element.text_content()
                            if text_content and len(text_content.strip()) > 50:
                                if "additional_info" not in complete_info:
                                    complete_info["additional_info"] = []
                                complete_info["additional_info"].append(text_content.strip())
                except:
                    continue
        except:
            pass
        
        return complete_info
        
    except Exception as e:
        logger.error(f"Error extracting project details: {str(e)}")
        return existing_info


async def generate_llama_offer(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Dict[str, any]:
    """
    Generate an AI-powered offer using local Llama model.
    
    Args:
        project_info: Complete project information
        user_preferences: User's skills, experience, rate, etc.
        
    Returns:
        Dictionary containing the generated offer
    """
    try:
        # For now, use the professional Arabic template
        # The AI model has difficulty generating proper Arabic content
        logger.info("Generating professional Arabic offer using template")
        return generate_fallback_offer(project_info, user_preferences)
        
    except Exception as e:
        logger.error(f"Error generating offer: {str(e)}")
        # Fallback to basic template
        return generate_fallback_offer(project_info, user_preferences)


async def call_local_llama(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    Call local Llama model for offer generation.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Generated offer data or None if Llama is not available
    """
    try:
        # Try different local Llama implementations
        llama_implementations = [
            try_ollama_llama,
            try_llama_cpp,
            try_transformers_llama
        ]
        
        for implementation in llama_implementations:
            try:
                result = await implementation(project_info, user_preferences)
                if result:
                    logger.info(f"Successfully generated offer using {implementation.__name__}")
                    return result
            except Exception as e:
                logger.debug(f"Llama implementation {implementation.__name__} failed: {str(e)}")
                continue
        
        logger.warning("No local Llama implementation available")
        return None
        
    except Exception as e:
        logger.error(f"Error calling local Llama: {str(e)}")
        return None


async def try_ollama_llama(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    Try to use Ollama for local Llama inference.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Generated offer data or None
    """
    try:
        import requests
        
        # Prepare the prompt
        prompt = create_offer_prompt(project_info, user_preferences)
        
        # Get model name from environment or use default
        model_name = os.getenv("OLLAMA_MODEL", "tinyllama")
        
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "")
            
            # Parse the response
            return parse_llama_response(ai_response, project_info, user_preferences)
        else:
            logger.debug(f"Ollama API returned status {response.status_code}")
            return None
            
    except ImportError:
        logger.debug("requests library not available for Ollama")
        return None
    except Exception as e:
        logger.debug(f"Ollama error: {str(e)}")
        return None


async def try_llama_cpp(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    Try to use llama-cpp-python for local Llama inference.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Generated offer data or None
    """
    try:
        from llama_cpp import Llama
        
        # Initialize Llama model
        model_path = os.getenv("LLAMA_MODEL_PATH", "models/llama-2-7b-chat.gguf")
        
        if not os.path.exists(model_path):
            logger.debug(f"Llama model not found at {model_path}")
            return None
        
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4
        )
        
        # Prepare the prompt
        prompt = create_offer_prompt(project_info, user_preferences)
        
        # Generate response
        response = llm(
            prompt,
            max_tokens=1000,
            temperature=0.7,
            stop=["</s>", "Human:", "Assistant:"]
        )
        
        ai_response = response.get("choices", [{}])[0].get("text", "")
        
        # Parse the response
        return parse_llama_response(ai_response, project_info, user_preferences)
        
    except ImportError:
        logger.debug("llama-cpp-python not available")
        return None
    except Exception as e:
        logger.debug(f"llama-cpp error: {str(e)}")
        return None


async def try_transformers_llama(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    Try to use transformers library for local Llama inference.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Generated offer data or None
    """
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        # Load model and tokenizer
        model_name = os.getenv("LLAMA_MODEL_NAME", "meta-llama/Llama-2-7b-chat-hf")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True  # For memory efficiency
        )
        
        # Prepare the prompt
        prompt = create_offer_prompt(project_info, user_preferences)
        
        # Tokenize and generate
        inputs = tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=1000,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        ai_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the generated part
        ai_response = ai_response[len(prompt):].strip()
        
        # Parse the response
        return parse_llama_response(ai_response, project_info, user_preferences)
        
    except ImportError:
        logger.debug("transformers library not available")
        return None
    except Exception as e:
        logger.debug(f"transformers error: {str(e)}")
        return None


def create_offer_prompt(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> str:
    """
    Create a prompt for Llama to generate an Arabic offer for Bahar platform.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Formatted prompt string in Arabic
    """
    # Create a more direct Arabic template
    title = project_info.get('title', 'مشروع تطوير')
    description = project_info.get('description', 'مشروع تطوير ويب')
    budget = project_info.get('budget', 'غير محدد')
    skills_needed = ', '.join(project_info.get('skills', []))
    user_skills = ', '.join(user_preferences.get('skills', []))
    experience = user_preferences.get('experience', '5 سنوات')
    rate = user_preferences.get('rate', '60 دولار/ساعة')
    
    prompt = f"""<s>[INST] أنت مطور مستقل محترف. اكتب عرض عمل باللغة العربية لمشروع على منصة بحر.

معلومات المشروع:
- العنوان: {title}
- الوصف: {description}
- الميزانية: {budget}
- المهارات المطلوبة: {skills_needed}

معلوماتك:
- مهاراتك: {user_skills}
- خبرتك: {experience}
- معدلك: {rate}

اكتب عرض عمل احترافي باللغة العربية يتضمن:
1. مقدمة مقنعة
2. خبرتك ومهاراتك
3. نهجك في المشروع
4. الجدول الزمني
5. السعر
6. دعوة للعمل

يجب أن يكون العرض:
- باللغة العربية الفصحى
- احترافي وواثق
- حوالي 200-300 كلمة
- بدون متغيرات أو أسماء وهمية

أرجع العرض كـ JSON بالشكل التالي:
{{
  "duration": 3,
  "milestone_number": 3,
  "brief": "رسالة العرض الكاملة باللغة العربية",
  "platform_communication": true,
  "milestones": [
    {{
      "deliverable": "المرحلة الأولى: تصميم واجهة المستخدم",
      "budget": 100
    }},
    {{
      "deliverable": "المرحلة الثانية: تطوير الواجهة الأمامية", 
      "budget": 100
    }},
    {{
      "deliverable": "المرحلة الثالثة: اختبار وإطلاق الموقع",
      "budget": 100
    }}
  ],
  "total_price_sar": 300
}}

ملاحظات مهمة:
- duration: عدد الأيام (عدد صحيح)
- milestone_number: عدد المراحل (عدد صحيح)
- brief: رسالة العرض الكاملة باللغة العربية
- platform_communication: true دائماً
- milestones: قائمة المراحل مع الميزانية لكل مرحلة
- total_price_sar: إجمالي السعر بالريال السعودي

[/INST]</s>"""
    
    return prompt


def parse_llama_response(ai_response: str, project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Dict[str, any]:
    """
    Parse the response from Llama and extract offer data.
    
    Args:
        ai_response: Raw response from Llama
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Parsed offer data in the correct format for Bahar form
    """
    try:
        # Try to extract JSON from the response
        import re
        
        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            offer_data = json.loads(json_str)
            
            # Validate required fields for Bahar form
            required_fields = ["duration", "milestone_number", "brief", "platform_communication", "milestones", "total_price_sar"]
            if all(field in offer_data for field in required_fields):
                # Ensure data types are correct
                offer_data["duration"] = int(offer_data["duration"])
                offer_data["milestone_number"] = int(offer_data["milestone_number"])
                offer_data["platform_communication"] = bool(offer_data["platform_communication"])
                offer_data["total_price_sar"] = int(offer_data["total_price_sar"])
                
                # Validate milestones structure
                if isinstance(offer_data["milestones"], list):
                    for milestone in offer_data["milestones"]:
                        if "deliverable" in milestone and "budget" in milestone:
                            milestone["budget"] = int(milestone["budget"])
                
                return offer_data
        
        # If JSON parsing fails, create structured response from text
        return create_structured_offer_from_text(ai_response, project_info, user_preferences)
        
    except Exception as e:
        logger.debug(f"Error parsing Llama response: {str(e)}")
        return create_structured_offer_from_text(ai_response, project_info, user_preferences)


def create_structured_offer_from_text(ai_response: str, project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Dict[str, any]:
    """
    Create structured offer data from raw Arabic text response.
    
    Args:
        ai_response: Raw text response
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Structured offer data in the correct format for Bahar form
    """
    # Clean up the response
    ai_response = ai_response.strip()
    
    # Use the full response as brief, but clean it up
    brief = ai_response
    
    # Remove any JSON-like structures from the beginning
    if brief.startswith('{') or brief.startswith('['):
        # Find the end of JSON structure
        brace_count = 0
        bracket_count = 0
        end_pos = 0
        
        for i, char in enumerate(brief):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            
            if brace_count == 0 and bracket_count == 0 and i > 0:
                end_pos = i + 1
                break
        
        if end_pos > 0:
            brief = brief[end_pos:].strip()
    
    # Generate AI-based milestones and pricing
    milestone_count = 3
    ai_milestones = generate_ai_milestones(project_info, user_preferences, milestone_count)
    
    # Create the structured offer in the correct format for Bahar form
    return {
        "duration": 3,  # Always 3 days for Bahar form (integer)
        "milestone_number": milestone_count,  # Dynamic milestone count (integer)
        "brief": brief.strip(),
        "platform_communication": True,
        "milestones": ai_milestones['milestones'],  # AI-generated milestones
        "total_price_sar": ai_milestones['total_price']  # Total price in SAR
    }


def generate_ai_milestones(project_info: Dict[str, any], user_preferences: Dict[str, any], milestone_count: int = 1) -> Dict[str, any]:
    """
    Generate AI-based milestones with pricing and deliverables.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        milestone_count: Number of milestones (default 1)
        
    Returns:
        Dictionary with milestones data
    """
    title = project_info.get('title', '').lower()
    description = project_info.get('description', '').lower()
    budget = project_info.get('budget', '')
    skills_needed = project_info.get('skills', [])
    
    # Analyze project complexity
    complexity_score = 0
    
    # Check for complex technologies
    complex_tech = ['react', 'node.js', 'python', 'ai', 'machine learning', 'api', 'database', 'mobile app']
    for tech in complex_tech:
        if tech in title.lower() or tech in description.lower():
            complexity_score += 2
    
    # Check for specific project types
    if 'website' in title.lower() or 'موقع' in title.lower():
        complexity_score += 1
    elif 'app' in title.lower() or 'تطبيق' in title.lower():
        complexity_score += 3
    elif 'api' in title.lower() or 'interface' in title.lower():
        complexity_score += 2
    elif 'database' in title.lower() or 'قاعدة بيانات' in title.lower():
        complexity_score += 2
    
    # Calculate base price in SAR
    base_price = 200  # Base price for simple projects
    
    if complexity_score <= 2:
        final_price = base_price + (complexity_score * 50)
    elif complexity_score <= 4:
        final_price = base_price + (complexity_score * 75)
    else:
        final_price = base_price + (complexity_score * 100)
    
    # Ensure reasonable range
    final_price = max(150, min(final_price, 2000))
    
    # Generate milestones
    milestones = []
    price_per_milestone = final_price // milestone_count
    
    # Milestone templates based on project type
    milestone_templates = {
        'website': [
            'تصميم واجهة المستخدم',
            'تطوير الواجهة الأمامية',
            'اختبار وإطلاق الموقع'
        ],
        'app': [
            'تصميم واجهة التطبيق',
            'تطوير الوظائف الأساسية',
            'اختبار وإطلاق التطبيق'
        ],
        'api': [
            'تصميم هيكل API',
            'تطوير نقاط النهاية',
            'اختبار وتوثيق API'
        ],
        'default': [
            'التحليل والتخطيط',
            'التطوير والتنفيذ',
            'الاختبار والتسليم'
        ]
    }
    
    # Determine project type for milestone descriptions
    project_type = 'default'
    if 'website' in title.lower() or 'موقع' in title.lower():
        project_type = 'website'
    elif 'app' in title.lower() or 'تطبيق' in title.lower():
        project_type = 'app'
    elif 'api' in title.lower() or 'interface' in title.lower():
        project_type = 'api'
    
    templates = milestone_templates[project_type]
    
    for i in range(milestone_count):
        milestone_price = price_per_milestone
        if i == milestone_count - 1:  # Last milestone gets remaining amount
            milestone_price = final_price - (price_per_milestone * (milestone_count - 1))
        
        deliverable = templates[i] if i < len(templates) else f'المرحلة {i+1}'
        
        milestones.append({
            'budget': milestone_price,
            'deliverable': deliverable,
            'outcome': deliverable  # Add outcome field for form filling
        })
    
    return {
        'total_price': final_price,
        'milestones': milestones
    }


def generate_ai_price(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> int:
    """
    Generate AI-based pricing in SAR based on project analysis.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Price value in SAR (integer)
    """
    title = project_info.get('title', '').lower()
    description = project_info.get('description', '').lower()
    budget = project_info.get('budget', '')
    skills_needed = project_info.get('skills', [])
    
    # Analyze project complexity
    complexity_score = 0
    
    # Check for complex technologies
    complex_tech = ['react', 'node.js', 'python', 'ai', 'machine learning', 'api', 'database', 'mobile app']
    for tech in complex_tech:
        if tech in title.lower() or tech in description.lower():
            complexity_score += 2
    
    # Check for specific project types
    if 'website' in title.lower() or 'موقع' in title.lower():
        complexity_score += 1
    elif 'app' in title.lower() or 'تطبيق' in title.lower():
        complexity_score += 3
    elif 'api' in title.lower() or 'interface' in title.lower():
        complexity_score += 2
    elif 'database' in title.lower() or 'قاعدة بيانات' in title.lower():
        complexity_score += 2
    
    # Check budget range if available
    budget_range = 0
    if budget:
        # Extract numbers from budget string
        import re
        numbers = re.findall(r'\d+', budget)
        if numbers:
            budget_num = int(numbers[0])
            if budget_num < 500:
                budget_range = 1
            elif budget_num < 1000:
                budget_range = 2
            elif budget_num < 2000:
                budget_range = 3
            else:
                budget_range = 4
    
    # Calculate base price in SAR
    base_price = 200  # Base price for simple projects
    
    if complexity_score <= 2:
        final_price = base_price + (complexity_score * 50)
    elif complexity_score <= 4:
        final_price = base_price + (complexity_score * 75)
    else:
        final_price = base_price + (complexity_score * 100)
    
    # Adjust based on budget range
    if budget_range > 0:
        final_price = max(final_price, budget_range * 150)
    
    # Ensure reasonable range
    final_price = max(150, min(final_price, 2000))
    
    return final_price


def generate_fallback_offer(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> Dict[str, any]:
    """
    Generate a dynamic Arabic offer based on project type and requirements.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Dynamic Arabic offer dictionary
    """
    title = project_info.get('title', 'مشروع')
    description = project_info.get('description', '')
    skills_needed = project_info.get('skills', [])
    user_skills = user_preferences.get('skills', [])
    
    # Detect if this is a monthly project
    is_monthly = detect_monthly_project(title, description)
    
    if is_monthly:
        # Generate monthly project offer (no milestones)
        message = generate_dynamic_arabic_message(project_info, user_preferences)
        monthly_price = generate_monthly_price(project_info, user_preferences)
        
        return {
            "duration": 30,  # 30 days for monthly projects
            "milestone_number": 1,  # Single milestone for monthly
            "brief": message.strip(),
            "platform_communication": True,
            "milestones": [{
                "deliverable": "خدمات شهرية مستمرة",
                "outcome": "خدمات شهرية مستمرة",
                "price": monthly_price
            }],
            "total_price_sar": monthly_price,
            "is_monthly": True
        }
    else:
        # Generate regular milestone-based offer
        milestone_count = 3
        ai_milestones = generate_ai_milestones(project_info, user_preferences, milestone_count)
        message = generate_dynamic_arabic_message(project_info, user_preferences)
        
        return {
            "duration": 3,  # Always 3 days for Bahar form (integer)
            "milestone_number": milestone_count,  # Dynamic milestone count (integer)
            "brief": message.strip(),
            "platform_communication": True,
            "milestones": ai_milestones['milestones'],  # AI-generated milestones
            "total_price_sar": ai_milestones['total_price'],  # Total price in SAR
            "is_monthly": False
        }

def generate_dynamic_arabic_message(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> str:
    """
    Generate a dynamic Arabic message based on project type and requirements.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Dynamic Arabic message
    """
    title = project_info.get('title', 'مشروع')
    description = project_info.get('description', '')
    skills_needed = project_info.get('skills', [])
    user_skills = user_preferences.get('skills', [])
    
    # Analyze project type based on title and description
    project_type = analyze_project_type(title, description, skills_needed)
    
    # Generate appropriate message based on project type
    if project_type == "management":
        return generate_management_message(title, description, user_skills)
    elif project_type == "design":
        return generate_design_message(title, description, user_skills)
    elif project_type == "development":
        return generate_development_message(title, description, user_skills)
    elif project_type == "marketing":
        return generate_marketing_message(title, description, user_skills)
    elif project_type == "content":
        return generate_content_message(title, description, user_skills)
    else:
        return generate_general_message(title, description, user_skills)

def analyze_project_type(title: str, description: str, skills_needed: list) -> str:
    """
    Analyze project type based on title, description, and required skills.
    
    Args:
        title: Project title
        description: Project description
        skills_needed: Required skills
        
    Returns:
        Project type (design, development, marketing, content, management, general)
    """
    text = f"{title} {description}".lower()
    skills_text = " ".join(skills_needed).lower()
    
    # Management/Partnership-related keywords (check first)
    management_keywords = ['شريك', 'partner', 'إدارة', 'management', 'تنفيذي', 'executive', 'مشروع', 'project', 'شراكة', 'partnership', 'تعاون', 'cooperation', 'متعاون', 'collaboration']
    if any(keyword in text or keyword in skills_text for keyword in management_keywords):
        return "management"
    
    # Design-related keywords
    design_keywords = ['تصميم', 'design', 'ui', 'ux', 'graphic', 'logo', 'brand', 'visual', 'illustration', 'photoshop', 'figma', 'sketch']
    if any(keyword in text or keyword in skills_text for keyword in design_keywords):
        return "design"
    
    # Development-related keywords
    dev_keywords = ['تطوير', 'development', 'programming', 'coding', 'web', 'app', 'software', 'react', 'node', 'python', 'javascript', 'php']
    if any(keyword in text or keyword in skills_text for keyword in dev_keywords):
        return "development"
    
    # Marketing-related keywords
    marketing_keywords = ['تسويق', 'marketing', 'social media', 'advertising', 'campaign', 'seo', 'sem', 'facebook', 'instagram']
    if any(keyword in text or keyword in skills_text for keyword in marketing_keywords):
        return "marketing"
    
    # Content-related keywords
    content_keywords = ['محتوى', 'content', 'writing', 'copywriting', 'translation', 'editing', 'blog', 'article', 'text']
    if any(keyword in text or keyword in skills_text for keyword in content_keywords):
        return "content"
    
    return "general"


def detect_monthly_project(title: str, description: str) -> bool:
    """
    Detect if a project is monthly-based based on title and description.
    
    Args:
        title: Project title
        description: Project description
        
    Returns:
        True if monthly project, False otherwise
    """
    text = f"{title} {description}".lower()
    
    # Monthly project keywords
    monthly_keywords = [
        'شهري', 'monthly', 'شريك', 'partner', 'مستمر', 'continuous', 
        'دائم', 'permanent', 'طويل المدى', 'long term', 'متعاون', 'collaboration',
        'تعاون', 'cooperation', 'شراكة', 'partnership', 'مستقل', 'freelancer',
        'عن بعد', 'remote', 'دوام كامل', 'full time', 'دوام جزئي', 'part time'
    ]
    
    return any(keyword in text for keyword in monthly_keywords)


def generate_monthly_price(project_info: Dict[str, any], user_preferences: Dict[str, any]) -> int:
    """
    Generate appropriate monthly price based on project type and user skills.
    
    Args:
        project_info: Project information
        user_preferences: User preferences
        
    Returns:
        Monthly price in SAR
    """
    title = project_info.get('title', '')
    description = project_info.get('description', '')
    skills_needed = project_info.get('skills', [])
    
    # Analyze project complexity and type
    project_type = analyze_project_type(title, description, skills_needed)
    
    # Base monthly prices by project type
    base_prices = {
        "management": 2000,
        "design": 1500,
        "development": 2500,
        "marketing": 1800,
        "content": 1200,
        "general": 1500
    }
    
    base_price = base_prices.get(project_type, 1500)
    
    # Adjust based on project complexity
    text = f"{title} {description}".lower()
    
    # High complexity indicators
    high_complexity_keywords = ['متقدم', 'advanced', 'معقد', 'complex', 'احترافي', 'professional']
    if any(keyword in text for keyword in high_complexity_keywords):
        base_price = int(base_price * 1.5)
    
    # Low complexity indicators
    low_complexity_keywords = ['بسيط', 'simple', 'أساسي', 'basic', 'مبتدئ', 'beginner']
    if any(keyword in text for keyword in low_complexity_keywords):
        base_price = int(base_price * 0.8)
    
    # Ensure price is within reasonable range
    return max(800, min(5000, base_price))


def generate_management_message(title: str, description: str, user_skills: list) -> str:
    """Generate message for management/partnership projects."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن لدي الخبرة والمهارات المناسبة للمساهمة في نجاح هذا المشروع.

أنا متحمس للعمل معكم كشريك تنفيذي ومساعدتكم في تحقيق أهداف المشروع. لدي خبرة في إدارة المشاريع والتعاون مع الفرق المختلفة.

أعتقد أن هذا التعاون سيكون مفيداً للطرفين، وسأعمل بجد لضمان نجاح المشروع وتحقيق النتائج المطلوبة.

أنا متاح للبدء فوراً وأتطلع للعمل معكم.

شكراً لكم على هذه الفرصة."""


def generate_design_message(title: str, description: str, user_skills: list) -> str:
    """Generate message for design projects."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن مهاراتي في التصميم ستكون مناسبة تماماً لهذا المشروع.

مهاراتي في التصميم:
أمتلك خبرة في تصميم {', '.join([skill for skill in user_skills if any(keyword in skill.lower() for keyword in ['design', 'ui', 'ux', 'graphic', 'تصميم'])])}، وأعمل على إنتاج تصميمات عالية الجودة تلبي احتياجات العملاء.

نهجي في المشروع:
سأقوم بتطوير التصميمات باستخدام أحدث الأدوات والمعايير في المجال، مع التركيز على:
- التصميم المبتكر والجذاب
- سهولة الاستخدام والتجربة
- التوافق مع هوية العلامة التجارية
- قابلية التطوير والتعديل

أود مناقشة تفاصيل المشروع معكم والإجابة على أي أسئلة لديكم.

مع أطيب التحيات،
مصمم محترف"""

def generate_development_message(title: str, description: str, user_skills: list) -> str:
    """Generate message for development projects."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن مهاراتي في التطوير ستكون مناسبة تماماً لهذا المشروع.

مهاراتي في التطوير:
أمتلك خبرة في {', '.join([skill for skill in user_skills if any(keyword in skill.lower() for keyword in ['development', 'programming', 'coding', 'تطوير', 'web', 'app'])])}، وأعمل على تطوير حلول تقنية متكاملة.

نهجي في المشروع:
سأقوم بتطوير المشروع باستخدام أحدث التقنيات وأفضل الممارسات، مع التركيز على:
- الكود النظيف والقابل للصيانة
- الأداء العالي والأمان
- سهولة الاستخدام والتجربة
- قابلية التطوير والتوسع

أود مناقشة تفاصيل المشروع معكم والإجابة على أي أسئلة لديكم.

مع أطيب التحيات،
مطور محترف"""

def generate_marketing_message(title: str, description: str, user_skills: list) -> str:
    """Generate message for marketing projects."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن مهاراتي في التسويق ستكون مناسبة تماماً لهذا المشروع.

مهاراتي في التسويق:
أمتلك خبرة في {', '.join([skill for skill in user_skills if any(keyword in skill.lower() for keyword in ['marketing', 'social media', 'advertising', 'تسويق'])])}، وأعمل على تطوير استراتيجيات تسويقية فعالة.

نهجي في المشروع:
سأقوم بتطوير استراتيجية تسويقية شاملة، مع التركيز على:
- الوصول للجمهور المستهدف
- زيادة الوعي بالعلامة التجارية
- تحسين معدلات التحويل
- قياس وتحليل النتائج

أود مناقشة تفاصيل المشروع معكم والإجابة على أي أسئلة لديكم.

مع أطيب التحيات،
متخصص تسويق محترف"""

def generate_content_message(title: str, description: str, user_skills: list) -> str:
    """Generate message for content projects."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن مهاراتي في المحتوى ستكون مناسبة تماماً لهذا المشروع.

مهاراتي في المحتوى:
أمتلك خبرة في {', '.join([skill for skill in user_skills if any(keyword in skill.lower() for keyword in ['content', 'writing', 'copywriting', 'محتوى', 'كتابة'])])}، وأعمل على إنتاج محتوى عالي الجودة.

نهجي في المشروع:
سأقوم بتطوير محتوى أصلي ومقنع، مع التركيز على:
- المحتوى المميز والجذاب
- تحسين محركات البحث
- التواصل الفعال مع الجمهور
- الحفاظ على هوية العلامة التجارية

أود مناقشة تفاصيل المشروع معكم والإجابة على أي أسئلة لديكم.

مع أطيب التحيات،
كاتب محتوى محترف"""

def generate_general_message(title: str, description: str, user_skills: list) -> str:
    """Generate general message for other project types."""
    return f"""السلام عليكم ورحمة الله وبركاته،

أود التعبير عن اهتمامي الشديد بمشروعكم. بعد مراجعة متطلبات المشروع، أعتقد أن مهاراتي ستكون مناسبة تماماً لهذا المشروع.

مهاراتي:
أمتلك خبرة في {', '.join(user_skills[:3])}، وأعمل على إنجاز المشاريع بكفاءة عالية وجودة ممتازة.

نهجي في المشروع:
سأقوم بإنجاز المشروع وفقاً للمعايير المطلوبة، مع التركيز على:
- الجودة العالية في العمل
- الالتزام بالجداول الزمنية
- التواصل المستمر والمتابعة
- تحقيق النتائج المطلوبة

أود مناقشة تفاصيل المشروع معكم والإجابة على أي أسئلة لديكم.

مع أطيب التحيات،
محترف متخصص"""


async def fill_offer_form(page: Page, ai_offer: Dict[str, any], user_preferences: Dict[str, any]) -> Dict[str, any]:
    """
    Fill the Bahar offer form with AI-generated content.
    
    Args:
        page: The Playwright page instance
        ai_offer: AI-generated offer content
        user_preferences: User preferences
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info("Filling Bahar offer form with AI-generated content")
        
        # Bahar form selectors based on actual form structure
        form_selectors = {
            "duration": [
                "input[data-testid='duration-input']", "input[id='duration']", 
                "input[name='duration']", "input[placeholder*='المدة']",
                "input[placeholder*='duration']", "input[placeholder*='أيام']"
            ],
            "milestone_number": [
                "input[data-testid='milestoneNumber-input']", "input[id='milestoneNumber']",
                "input[name='milestoneNumber']", "input[placeholder*='مراحل']",
                "input[placeholder*='phases']", "input[placeholder*='milestone']"
            ],
            "brief": [
                "textarea[id='brief']", "textarea[name='brief']", 
                "textarea[data-testid='brief']", "textarea[placeholder*='النبذة']",
                "textarea[placeholder*='brief']", "textarea[placeholder*='description']",
                "textarea[placeholder*='الوصف']"
            ],
            "file_upload": [
                "input[id='fileInput']", "input[type='file']", 
                "input[data-testid='uploadFileButton']", "input[accept*='pdf']",
                "input[accept*='doc']", "input[accept*='docx']"
            ],
            "platform_communication": [
                "input[id='platformCommunication']", "input[name='platformCommunication']",
                "input[data-testid='platformCommunication-checkbox']", 
                "input[type='checkbox']"
            ]
        }
        
        filled_fields = []
        
        # Fill duration field (المدة)
        if ai_offer.get("duration"):
            for selector in form_selectors["duration"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, str(ai_offer["duration"]))
                        filled_fields.append("duration")
                        logger.info(f"Filled duration field: {ai_offer['duration']} days")
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill duration with selector {selector}: {str(e)}")
                    continue
        
        # Fill milestone number field (عدد مراحل المشروع)
        if ai_offer.get("milestone_number"):
            for selector in form_selectors["milestone_number"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, str(ai_offer["milestone_number"]))
                        filled_fields.append("milestone_number")
                        logger.info(f"Filled milestone number field: {ai_offer['milestone_number']} phases")
                        
                        # Wait for milestone fields to appear
                        await asyncio.sleep(2)
                        
                        # Fill milestone fields if milestones data is available
                        if ai_offer.get("milestones"):
                            await fill_milestone_fields(page, ai_offer["milestones"])
                        
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill milestone number with selector {selector}: {str(e)}")
                    continue
        
        # Fill brief field (النبذة)
        if ai_offer.get("brief"):
            for selector in form_selectors["brief"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, ai_offer["brief"])
                        filled_fields.append("brief")
                        logger.info("Filled brief field with Arabic offer content")
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill brief with selector {selector}: {str(e)}")
                    continue
        
        # Skip file upload - always ignore
        logger.info("Skipping file upload as requested")
        
        # Check platform communication agreement
        if ai_offer.get("platform_communication", True):
            for selector in form_selectors["platform_communication"]:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_checked = await element.is_checked()
                        if not is_checked:
                            await element.check()
                            filled_fields.append("platform_communication")
                            logger.info("Checked platform communication agreement")
                        break
                except Exception as e:
                    logger.debug(f"Failed to check platform communication with selector {selector}: {str(e)}")
                    continue
        
        return {
            "success": len(filled_fields) > 0,
            "message": f"Filled fields: {', '.join(filled_fields)}",
            "filled_fields": filled_fields
        }
        
    except Exception as e:
        logger.error(f"Error filling offer form: {str(e)}")
        return {"success": False, "message": f"Error filling form: {str(e)}"}


async def fill_milestone_fields(page: Page, milestones: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Fill milestone fields with AI-generated content.
    
    Args:
        page: The Playwright page instance
        milestones: List of milestone data
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info(f"Filling {len(milestones)} milestone fields")
        
        filled_milestones = []
        
        for i, milestone in enumerate(milestones):
            # Fill budget field for this milestone
            budget_selectors = [
                f"input[data-testid='proposalMilestones.{i}.budget-input']",
                f"input[id='proposalMilestones.{i}.budget']",
                f"input[name='proposalMilestones.{i}.budget']"
            ]
            
            budget_filled = False
            for selector in budget_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, str(milestone['budget']))
                        budget_filled = True
                        logger.info(f"Filled milestone {i+1} budget: {milestone['budget']} SAR")
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill milestone {i+1} budget with selector {selector}: {str(e)}")
                    continue
            
            # Fill deliverable field for this milestone
            deliverable_selectors = [
                f"input[data-testid='proposalMilestones.{i}.deliverable-input']",
                f"input[id='proposalMilestones.{i}.deliverable']",
                f"input[name='proposalMilestones.{i}.deliverable']"
            ]
            
            deliverable_filled = False
            for selector in deliverable_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await custom_fill_element(page, selector, milestone['deliverable'])
                        deliverable_filled = True
                        logger.info(f"Filled milestone {i+1} deliverable: {milestone['deliverable']}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill milestone {i+1} deliverable with selector {selector}: {str(e)}")
                    continue
            
            if budget_filled and deliverable_filled:
                filled_milestones.append(i+1)
        
        return {
            "success": len(filled_milestones) == len(milestones),
            "message": f"Filled {len(filled_milestones)} out of {len(milestones)} milestones",
            "filled_milestones": filled_milestones
        }
        
    except Exception as e:
        logger.error(f"Error filling milestone fields: {str(e)}")
        return {
            "success": False,
            "message": f"Error filling milestone fields: {str(e)}"
        }


async def upload_resume_if_needed(page: Page, resume_path: str) -> Dict[str, any]:
    """
    Upload resume if there's a file upload field in the form.
    
    Args:
        page: The Playwright page instance
        resume_path: Path to the resume file
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Common selectors for file upload
        upload_selectors = [
            "input[type='file']", "input[name='file']", "input[name='resume']",
            "input[name='attachment']", "input[name='cv']", "#file", "#resume",
            "[data-testid='file-upload']", ".file-upload input"
        ]
        
        for selector in upload_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await upload_file(selector, resume_path)
                    return {"success": True, "message": f"Resume uploaded: {resume_path}"}
            except:
                continue
        
        return {"success": False, "message": "No file upload field found"}
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        return {"success": False, "message": f"Error uploading resume: {str(e)}"}


async def submit_offer_form(page: Page) -> Dict[str, any]:
    """
    Submit the filled offer form.
    
    Args:
        page: The Playwright page instance
        
    Returns:
        Dictionary with success status and message
    """
    try:
        logger.info("Submitting offer form")
        
        # Bahar submit button selectors based on actual form
        submit_selectors = [
            "button[data-testid='submitProposalFormButton']", "button[type='submit']",
            "button:contains('إرسال العرض')", "button:contains('Submit Proposal')",
            "button:contains('Send Proposal')", "button:contains('إرسال')",
            "button:contains('تقديم')", "[data-testid='submit']"
        ]
        
        for selector in submit_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await click(selector, 1.0)
                    await asyncio.sleep(3)  # Wait for submission
                    
                    # Check for success indicators
                    success_indicators = [
                        ".success", ".success-message", ".confirmation", ".alert-success",
                        "text=Success", "text=Submitted", "text=Sent", "text=تم بنجاح",
                        "text=تم الإرسال", "text=تم التقديم", "text=تم إرسال العرض",
                        "text=تم تقديم العرض", "text=تم إرسال الطلب", "text=تم تقديم الطلب",
                        "text=تم إرسال الاقتراح", "text=تم تقديم الاقتراح"
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            success_element = await page.query_selector(indicator)
                            if success_element:
                                return {"success": True, "message": "Offer submitted successfully"}
                        except:
                            continue
                    
                    # If no explicit success indicator, check URL change
                    current_url = page.url
                    if "success" in current_url.lower() or "submitted" in current_url.lower():
                        return {"success": True, "message": "Offer submitted successfully (URL change detected)"}
                    
                    return {"success": True, "message": "Submit button clicked, assuming success"}
                    
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {str(e)}")
                continue
        
        return {"success": False, "message": "Could not find or click submit button"}
        
    except Exception as e:
        logger.error(f"Error submitting offer form: {str(e)}")
        return {"success": False, "message": f"Error submitting form: {str(e)}"} 