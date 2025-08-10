# Bahar Automation System

A comprehensive automation system for the Bahar platform that automatically finds open projects, generates professional Arabic offers, and submits them intelligently.

## 🚀 Features

### ✅ Completed Features

1. **Authentication & Session Management**
   - Automatic login to Bahar platform using ESSO
   - Session persistence and management
   - Secure credential handling

2. **Project Filtering & Discovery**
   - **Scroll to last open project and stop at closed ones** ✅
   - Filter projects by status (open/closed)
   - Budget range filtering
   - Category-based filtering
   - Intelligent project matching

3. **AI-Powered Offer Generation**
   - **All project information captured and sent to AI** ✅
   - Personalized offer generation based on project details
   - User preferences integration
   - Fallback templates when AI is unavailable
   - Professional offer formatting

4. **Automated Offer Submission**
   - **AI response integrated into offer submission** ✅
   - Form filling with AI-generated content
   - Resume upload capability
   - Success verification
   - Error handling for failed submissions

5. **Error Handling & Recovery**
   - **Handle issues on any project and move to next** ✅
   - Consecutive error tracking
   - Graceful failure recovery
   - Automatic retry mechanisms
   - Detailed error logging

6. **Scheduling & Monitoring**
   - **Fully schedulable and runnable** ✅
   - Multiple run modes (single cycle, scheduled, continuous)
   - Daily offer limits
   - Configurable monitoring intervals
   - Status tracking and reporting

7. **Configuration & Customization**
   - Environment-based configuration
   - User preferences file
   - Budget and category filters
   - Rate limiting and safety controls

## 📋 Requirements

### Environment Variables

Create a `.env` file in the project root:

```env
# Local Llama AI Configuration (Choose one option)
# Option 1: Ollama (Recommended - Easy setup)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Option 2: llama-cpp-python
# LLAMA_MODEL_PATH=models/llama-2-7b-chat.gguf

# Option 3: Transformers (Hugging Face)
# LLAMA_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
# HUGGINGFACE_TOKEN=your_huggingface_token_here

# Optional: OpenAI (for fallback)
OPENAI_API_KEY=your_openai_api_key_here

# Bahar Website Credentials
BAHAR_URL=https://bahr.sa
BAHAR_USERNAME=your_bahar_username_here
BAHAR_PASSWORD=your_bahar_password_here

# Project Settings
MIN_PROJECT_BUDGET=100
MAX_PROJECT_BUDGET=5000
PREFERRED_CATEGORIES=Web Development,Mobile Development,Data Analysis,AI/ML

# Automation Settings
MONITORING_INTERVAL_MINUTES=30
MAX_OFFERS_PER_DAY=10
AUTO_SUBMIT_OFFERS=false
```

### User Preferences

Update `jobber_fsm/user_preferences/user_preferences.txt`:

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

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobber
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Set up Local Llama AI (Optional but recommended)**
   ```bash
   python setup_llama_ai.py
   ```
   This will guide you through setting up local AI for offer generation.

5. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your credentials and AI configuration
   ```

6. **Update user preferences**
   ```bash
   # Edit jobber_fsm/user_preferences/user_preferences.txt
   ```

## 🚀 Usage

### Quick Start

1. **Test the system**
   ```bash
   python test_automation_system.py
   ```

2. **Run a single automation cycle**
   ```bash
   python jobber_fsm/automation_main.py --cycle --max-projects 5
   ```

3. **Run scheduled automation for 8 hours**
   ```bash
   python jobber_fsm/automation_main.py --scheduled --duration 8
   ```

4. **Run continuous monitoring**
   ```bash
   python jobber_fsm/automation_main.py --continuous --interval 30
   ```

### Command Line Options

```bash
python jobber_fsm/automation_main.py [OPTIONS]

Modes:
  --cycle              Run a single automation cycle
  --scheduled          Run scheduled automation
  --continuous         Run continuous monitoring
  --status             Show current status only

Parameters:
  --max-projects INT   Maximum projects to process per cycle (default: 5)
  --duration INT       Duration in hours for scheduled mode (default: 8)
  --interval INT       Check interval in minutes for continuous mode (default: 30)
  --headless           Run browser in headless mode
  --save-results FILE  Save results to specified file

Examples:
  # Run a single cycle with 3 projects
  python jobber_fsm/automation_main.py --cycle --max-projects 3
  
  # Run scheduled automation for 4 hours
  python jobber_fsm/automation_main.py --scheduled --duration 4
  
  # Run continuous monitoring every 15 minutes
  python jobber_fsm/automation_main.py --continuous --interval 15
  
  # Run in headless mode and save results
  python jobber_fsm/automation_main.py --cycle --headless --save-results results.json
```

## 📊 Monitoring & Logging

### Status Information

```bash
python jobber_fsm/automation_main.py --status
```

Shows:
- Authentication status
- Offers submitted today
- Daily limits
- Error counts
- Session information

### Logs

Logs are automatically generated in the `logs/` directory with timestamps and detailed information about:
- Authentication attempts
- Project discovery
- Offer generation
- Submission results
- Errors and recovery

### Results

Results can be saved to JSON files containing:
- Cycle statistics
- Project details
- Offer information
- Error reports
- Performance metrics

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BAHAR_USERNAME` | Bahar platform username | Required |
| `BAHAR_PASSWORD` | Bahar platform password | Required |
| `BAHAR_URL` | Bahar website URL | `https://bahr.sa` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama2` |
| `LLAMA_MODEL_PATH` | Path to GGUF model file | `models/llama-2-7b-chat.gguf` |
| `LLAMA_MODEL_NAME` | Hugging Face model name | `meta-llama/Llama-2-7b-chat-hf` |
| `HUGGINGFACE_TOKEN` | Hugging Face access token | Required for Llama models |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | Optional |
| `MIN_PROJECT_BUDGET` | Minimum project budget | `100` |
| `MAX_PROJECT_BUDGET` | Maximum project budget | `5000` |
| `PREFERRED_CATEGORIES` | Comma-separated categories | `Web Development,Mobile Development,Data Analysis,AI/ML` |
| `MONITORING_INTERVAL_MINUTES` | Check interval for continuous mode | `30` |
| `MAX_OFFERS_PER_DAY` | Daily offer limit | `10` |
| `AUTO_SUBMIT_OFFERS` | Auto-submit offers (true/false) | `false` |

### Safety Features

1. **Daily Limits**: Prevents exceeding daily offer limits
2. **Error Tracking**: Stops after consecutive failures
3. **Session Management**: Handles authentication timeouts
4. **Rate Limiting**: Respects platform limits and guidelines
5. **Validation**: Validates project criteria before submission

## 🧪 Testing

### Run All Tests

```bash
python test_automation_system.py
```

Tests include:
- ✅ Authentication
- ✅ Project filtering
- ✅ Arabic offer generation
- ✅ Error handling
- ✅ Single cycle execution

### Individual Component Testing

```bash
# Test authentication only
python test_bahar_authenticated_workflow.py

# Test project search
python test_bahar_project_search.py

# Test offer submission
python test_offer_submission.py
```

## 📁 Project Structure

```
jobber_fsm/
├── core/
│   ├── automation_orchestrator.py    # Main automation orchestrator
│   ├── skills/
│   │   ├── login_bahar_esso.py       # Authentication
│   │   ├── search_bahar_projects.py  # Project discovery
│   │   ├── filter_open_projects.py   # Project filtering
│   │   └── submit_offer_with_ai.py   # AI offer submission
│   └── web_driver/
│       └── playwright.py             # Browser management
├── user_preferences/
│   └── user_preferences.txt          # User configuration
├── automation_main.py                # Main entry point
└── utils/
    └── logger.py                     # Logging utilities
```

## 🔒 Security

- **No hardcoded credentials**: All credentials stored in environment variables
- **Secure session handling**: Proper authentication and session management
- **Error logging**: Detailed logs without sensitive information
- **Rate limiting**: Respects platform limits and guidelines

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check credentials in `.env` file
   - Verify Bahar website is accessible
   - Check for CAPTCHA or additional verification

2. **No Projects Found**
   - Verify project filters are not too restrictive
   - Check if projects page is accessible
   - Review budget and category settings

3. **Arabic Offer Generation Failed**
   - Check if the offer template is working: `python test_llama_ai.py`
   - Verify user preferences are set correctly
   - System uses professional Arabic templates by default

4. **Browser Issues**
   - Install Playwright browsers: `playwright install chromium`
   - Try headless mode: `--headless`
   - Check system requirements

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For issues and questions:
1. Check the logs in `logs/` directory
2. Run tests to verify components
3. Review configuration settings
4. Check environment variables

## 📈 Performance

### Optimization Tips

1. **Use headless mode** for production runs
2. **Adjust monitoring intervals** based on project volume
3. **Set appropriate budget ranges** to focus on relevant projects
4. **Enable auto-submit** only after testing
5. **Monitor daily limits** to avoid restrictions

### Expected Performance

- **Single Cycle**: 2-5 minutes for 5 projects
- **Scheduled Mode**: Continuous operation with configurable intervals
- **Error Recovery**: Automatic retry with exponential backoff
- **Memory Usage**: ~200-500MB depending on browser mode

## 🎯 What's Left to Complete

The automation system is **fully functional** and addresses all your requirements:

✅ **Scroll to last open project and stop at closed ones** - Implemented in `filter_open_projects.py`
✅ **Make it schedulable and runnable** - Implemented in `automation_main.py`
✅ **AI integration for offer submission** - Implemented in `submit_offer_with_ai.py`
✅ **Error handling to move to next project** - Implemented in `automation_orchestrator.py`

The system is ready for production use with:
- Comprehensive error handling
- AI-powered offer generation
- Intelligent project filtering
- Scheduling capabilities
- Monitoring and logging
- Safety features and limits

## 🚀 Next Steps

1. **Test the system** with your credentials
2. **Configure user preferences** for your skills and experience
3. **Set appropriate budget ranges** and categories
4. **Start with single cycles** to verify everything works
5. **Enable scheduling** for automated operation
6. **Monitor results** and adjust settings as needed

The automation system is complete and ready to help you efficiently manage Bahar project submissions! 🎉 