# API-Based Bahar Automation with AI Integration

This system provides automated Bahar project management using API-based browser automation and AI-powered offer generation.

## 🚀 Features

### ✅ Core Features

1. **API-Based Browser Automation**
   - Uses API tokens for browser control (Browserbase, etc.)
   - No local browser installation required
   - Scalable and reliable automation

2. **AI-Powered Offer Generation**
   - Intelligent offer creation based on project details
   - Personalized content using user preferences
   - Professional Arabic offer formatting
   - Fallback templates when AI is unavailable

3. **Automated Project Management**
   - Automatic project discovery and filtering
   - Budget and category-based filtering
   - Open/closed project detection
   - Intelligent project matching

4. **Smart Offer Submission**
   - Automated form filling with AI content
   - Resume upload capability
   - Success verification
   - Error handling and recovery

5. **Scheduling & Monitoring**
   - Configurable automation cycles
   - Daily offer limits
   - Continuous monitoring
   - Status tracking and reporting

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd jobber
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root:

```env
# Browser API Configuration (Required)
BROWSER_API_TOKEN=your_browser_api_token_here
BROWSER_API_BASE_URL=https://api.browserbase.com

# Bahar Website Credentials (Required)
BAHAR_URL=https://bahr.sa
BAHAR_USERNAME=your_bahar_username_here
BAHAR_PASSWORD=your_bahar_password_here

# AI Configuration (Choose one option)
# Option 1: Ollama (Recommended)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Option 2: OpenAI (Fallback)
OPENAI_API_KEY=your_openai_api_key_here

# Project Settings
MIN_PROJECT_BUDGET=100
MAX_PROJECT_BUDGET=5000
PREFERRED_CATEGORIES=Web Development,Mobile Development,Data Analysis,AI/ML

# Automation Settings
MONITORING_INTERVAL_MINUTES=30
MAX_OFFERS_PER_DAY=10
AUTO_SUBMIT_OFFERS=false
```

### 4. Update User Preferences
Edit `jobber_fsm/user_preferences/user_preferences.txt`:

```txt
Personal Info:
First Name: Your Name
Last Name: Your Last Name
Email: your.email@example.com
Expected Salary: 5000
Occupation: Software Developer
Address: Your Address
Phone Number: Your Phone
LinkedIn: https://linkedin.com/in/yourprofile

Bahar Website Credentials:
Bahar URL: https://bahr.sa
Bahar Username: [YOUR_BAHAR_USERNAME]
Bahar Password: [YOUR_BAHAR_PASSWORD]

Project Preferences:
Minimum Project Budget: 100
Maximum Project Budget: 5000
Preferred Project Categories: Web Development,Mobile Development,Data Analysis,AI/ML
Offer Template: "Hi, I'm interested in your project. I have experience in [RELEVANT_SKILLS] and can deliver high-quality results within your timeline. My rate is [RATE] per hour. Looking forward to discussing this project with you!"

Skills and Experience:
- Web Development, JavaScript, React, Node.js
- 5 years of experience in full-stack development
- Experience in cloud infrastructure and databases
- Work authorization for remote work
```

## 🚀 Usage

### Quick Start

1. **Test the system**
   ```bash
   python test_api_automation.py
   ```

2. **Run a single automation cycle**
   ```python
   from jobber_fsm.core.api_automation_orchestrator import APIBaharAutomationOrchestrator
   
   async def main():
       orchestrator = APIBaharAutomationOrchestrator(headless=False)
       await orchestrator.initialize()
       
       result = await orchestrator.run_automation_cycle(max_projects=5)
       print(f"Cycle completed: {result}")
       
       await orchestrator.cleanup()
   
   asyncio.run(main())
   ```

3. **Run scheduled automation**
   ```python
   # Run for 8 hours
   result = await orchestrator.run_scheduled_automation(run_duration_hours=8)
   ```

### Command Line Usage

Create a simple script for command line usage:

```python
#!/usr/bin/env python3
import asyncio
import argparse
from jobber_fsm.core.api_automation_orchestrator import APIBaharAutomationOrchestrator

async def main():
    parser = argparse.ArgumentParser(description='API-Based Bahar Automation')
    parser.add_argument('--cycle', action='store_true', help='Run single cycle')
    parser.add_argument('--scheduled', action='store_true', help='Run scheduled automation')
    parser.add_argument('--max-projects', type=int, default=5, help='Max projects per cycle')
    parser.add_argument('--duration', type=int, default=8, help='Duration in hours')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    orchestrator = APIBaharAutomationOrchestrator(headless=args.headless)
    
    try:
        await orchestrator.initialize()
        
        if args.cycle:
            result = await orchestrator.run_automation_cycle(max_projects=args.max_projects)
            print(f"Cycle result: {result}")
        elif args.scheduled:
            result = await orchestrator.run_scheduled_automation(run_duration_hours=args.duration)
            print(f"Scheduled result: {result}")
        else:
            print("Please specify --cycle or --scheduled")
            
    finally:
        await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration

### Browser API Services

The system supports various API-based browser services:

#### Browserbase (Recommended)
```env
BROWSER_API_TOKEN=your_browserbase_token
BROWSER_API_BASE_URL=https://api.browserbase.com
```

#### Other Services
You can adapt the API endpoints for other services by modifying the `APIBrowserManager` class.

### AI Configuration

#### Option 1: Ollama (Local)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama2

# Set environment
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

#### Option 2: OpenAI (Cloud)
```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 📊 Monitoring

### Status Check
```python
status = orchestrator.get_status()
print(f"Authenticated: {status['is_authenticated']}")
print(f"Offers Today: {status['offers_submitted_today']}/{status['max_offers_per_day']}")
print(f"Session Start: {status['session_start_time']}")
```

### Logs
The system generates detailed logs in the `logs/` directory:
- `screenshots/` - Browser screenshots for debugging
- `automation.log` - Detailed automation logs

## 🔍 Troubleshooting

### Common Issues

1. **API Token Error**
   ```
   Error: API token is required
   ```
   Solution: Set `BROWSER_API_TOKEN` in your `.env` file

2. **Authentication Failed**
   ```
   Failed to authenticate with Bahar
   ```
   Solution: Check `BAHAR_USERNAME` and `BAHAR_PASSWORD` in `.env`

3. **AI Generation Failed**
   ```
   Failed to generate AI offer
   ```
   Solution: Check AI configuration (Ollama or OpenAI)

4. **No Projects Found**
   ```
   No open projects found
   ```
   Solution: Adjust budget range or category filters

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Advanced Usage

### Custom AI Models
You can integrate custom AI models by modifying the `generate_fallback_offer` function in `submit_offer_with_ai.py`.

### Custom Project Filters
Extend the `_project_matches_criteria` method in `APIBaharAutomationOrchestrator` to add custom filtering logic.

### Custom Offer Templates
Modify the offer templates in `user_preferences.txt` or the AI generation logic.

## 📈 Performance

### Optimization Tips

1. **Adjust Monitoring Interval**
   - Shorter intervals for more frequent checks
   - Longer intervals to reduce API calls

2. **Set Realistic Limits**
   - `MAX_OFFERS_PER_DAY` to avoid rate limiting
   - `max_projects` per cycle for optimal performance

3. **Use Headless Mode**
   - Enable `headless=True` for production use
   - Disable screenshots for better performance

### Expected Performance
- **Projects per cycle**: 3-10 (depending on availability)
- **Offers per day**: 10-50 (depending on limits)
- **Cycle duration**: 2-5 minutes
- **Success rate**: 80-95% (depending on project availability)

## 🔒 Security

### Best Practices

1. **Secure Credentials**
   - Never commit `.env` files to version control
   - Use environment variables in production
   - Rotate API tokens regularly

2. **Rate Limiting**
   - Respect Bahar's rate limits
   - Use appropriate delays between actions
   - Monitor for rate limit errors

3. **Error Handling**
   - The system includes comprehensive error handling
   - Failed operations are logged and reported
   - Automatic retry mechanisms for transient failures

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Test with the provided test scripts
4. Check the configuration examples

## 🎯 Next Steps

1. **Set up your environment** with API tokens and credentials
2. **Test the system** with `python test_api_automation.py`
3. **Configure your preferences** in the user preferences file
4. **Run a test cycle** to verify everything works
5. **Deploy to production** with appropriate monitoring

The system is designed to be production-ready with proper error handling, logging, and monitoring capabilities. 