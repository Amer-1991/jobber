# Bahar Project Automation Agent

Based on the [sentient](https://github.com/sentient-engineering/sentient) framework - an AI agent that automatically applies to relevant projects on the Bahar platform (https://bahr.sa) on your behalf.

## 🎯 What This Agent Does

This AI-powered automation agent:
- **Logs into Bahar** automatically using your credentials
- **Discovers new projects** that match your skills and preferences  
- **Crafts personalized offers** using AI based on project requirements
- **Submits offers automatically** on your behalf
- **Monitors for new projects** continuously
- **Tracks success rates** and optimizes offers over time

## 🏗️ Architecture

This project uses the **jobber_fsm** implementation based on [finite state machines](https://github.com/sentient-engineering/multi-agent-fsm) for better scalability and reliability.

### Key Components

- **🔐 Bahar Login Skill** - Handles SSO authentication with Bahar
- **🔍 Project Discovery** - Finds and analyzes relevant projects
- **🤖 AI Offer Crafting** - Generates personalized project proposals
- **📋 Offer Submission** - Automatically submits offers to projects
- **📊 Monitoring System** - Continuously checks for new opportunities

### Legacy Note

The `jobber` folder contains a simpler implementation for job applications. The `jobber_fsm` folder contains our Bahar-specific implementation with more advanced features.

## 🚀 Setup & Installation

### 1. Install Dependencies

#### Option A: Using pip (Recommended)
```bash
pip3 install -r requirements.txt
python3 -m playwright install chrome
```

#### Option B: Using Poetry
```bash
poetry install
python3 -m playwright install chrome
```

### 2. Configure Environment

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   BAHAR_USERNAME=your_bahar_username
   BAHAR_PASSWORD=your_bahar_password
   ```

3. **Update user preferences:**
   ```bash
   cp jobber_fsm/user_preferences/user_preferences_template.txt jobber_fsm/user_preferences/user_preferences.txt
   ```
   Then edit `user_preferences.txt` with your information.

### 3. Test Bahar Login

```bash
python3 test_bahar_login.py
```

### 4. Run the Agent

```bash
python3 -u -m jobber_fsm
```

### 5. Example Task

```bash
"Find and apply to web development projects on Bahar with budget between $500-$2000"
```

### Run evals

1. For Jobber

```bash
 python -m test.tests_processor --orchestrator_type vanilla
```

2. For Jobber FSM

```bash
 python -m test.tests_processor --orchestrator_type fsm
```

#### citations

a bunch of amazing work in the space has inspired this. see [webvoyager](https://arxiv.org/abs/2401.13919), [agent-e](https://arxiv.org/abs/2407.13032)

```
@article{he2024webvoyager,
  title={WebVoyager: Building an End-to-End Web Agent with Large Multimodal Models},
  author={He, Hongliang and Yao, Wenlin and Ma, Kaixin and Yu, Wenhao and Dai, Yong and Zhang, Hongming and Lan, Zhenzhong and Yu, Dong},
  journal={arXiv preprint arXiv:2401.13919},
  year={2024}
}
```

```
@misc{abuelsaad2024-agente,
      title={Agent-E: From Autonomous Web Navigation to Foundational Design Principles in Agentic Systems},
      author={Tamer Abuelsaad and Deepak Akkil and Prasenjit Dey and Ashish Jagmohan and Aditya Vempaty and Ravi Kokku},
      year={2024},
      eprint={2407.13032},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2407.13032},
}
```
