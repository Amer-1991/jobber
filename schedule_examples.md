# Scheduling Examples for Bahar Automation

This document provides examples of how to schedule the Bahar automation system to run automatically.

## 🕐 Cron Job Examples

### Basic Cron Setup

Add to your crontab (`crontab -e`):

```bash
# Run automation every 30 minutes during business hours (9 AM - 6 PM)
*/30 9-18 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 3 --headless

# Run automation every hour during business hours
0 9-18 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless

# Run automation twice daily (morning and afternoon)
0 9,14 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless

# Run automation every 2 hours during business hours
0 9,11,13,15,17 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 3 --headless
```

### Advanced Scheduling

```bash
# Run continuous monitoring for 8 hours during business hours
0 9 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --scheduled --duration 8 --headless

# Run automation with result logging
0 9,12,15,18 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless --save-results /path/to/logs/automation_$(date +\%Y\%m\%d_\%H\%M\%S).json

# Run automation only on weekdays with error logging
0 9-17 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 3 --headless 2>&1 | tee -a /path/to/logs/automation.log
```

## 🐳 Docker Scheduling

### Docker Compose with Cron

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  bahar-automation:
    build: .
    environment:
      - BAHAR_USERNAME=${BAHAR_USERNAME}
      - BAHAR_PASSWORD=${BAHAR_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./results:/app/results
    command: python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless
    restart: unless-stopped

  cron:
    image: alpine:latest
    volumes:
      - ./crontab:/etc/crontabs/root
      - ./logs:/app/logs
    command: crond -f -l 2
```

Create `crontab`:

```bash
# Run automation every 30 minutes during business hours
*/30 9-18 * * 1-5 docker-compose run --rm bahar-automation python jobber_fsm/automation_main.py --cycle --max-projects 3 --headless
```

## 🔄 Systemd Service

Create `/etc/systemd/system/bahar-automation.service`:

```ini
[Unit]
Description=Bahar Automation Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/jobber
Environment=BAHAR_USERNAME=your_username
Environment=BAHAR_PASSWORD=your_password
Environment=OPENAI_API_KEY=your_openai_key
ExecStart=/usr/bin/python3 jobber_fsm/automation_main.py --continuous --interval 30 --headless
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable bahar-automation
sudo systemctl start bahar-automation
sudo systemctl status bahar-automation
```

## 📱 GitHub Actions (for cloud scheduling)

Create `.github/workflows/automation.yml`:

```yaml
name: Bahar Automation

on:
  schedule:
    # Run every 30 minutes during business hours (UTC)
    - cron: '*/30 6-15 * * 1-5'  # 9 AM - 6 PM Saudi time
  workflow_dispatch:  # Allow manual triggers

jobs:
  automation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        playwright install chromium
    
    - name: Run automation
      env:
        BAHAR_USERNAME: ${{ secrets.BAHAR_USERNAME }}
        BAHAR_PASSWORD: ${{ secrets.BAHAR_PASSWORD }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless --save-results results.json
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: automation-results
        path: results.json
```

## 🐍 Python Script Scheduling

Create `schedule_runner.py`:

```python
#!/usr/bin/env python3
"""
Python-based scheduler for Bahar automation
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_automation():
    """Run the automation system."""
    try:
        logging.info("Starting automation cycle...")
        
        # Run automation with subprocess
        result = subprocess.run([
            'python', 'jobber_fsm/automation_main.py',
            '--cycle', '--max-projects', '5', '--headless'
        ], capture_output=True, text=True, cwd='/path/to/jobber')
        
        if result.returncode == 0:
            logging.info("Automation completed successfully")
        else:
            logging.error(f"Automation failed: {result.stderr}")
            
    except Exception as e:
        logging.error(f"Error running automation: {str(e)}")

def is_business_hours():
    """Check if it's business hours (9 AM - 6 PM, Monday-Friday)."""
    now = datetime.now()
    return (
        now.weekday() < 5 and  # Monday-Friday
        9 <= now.hour < 18     # 9 AM - 6 PM
    )

def conditional_run():
    """Run automation only during business hours."""
    if is_business_hours():
        run_automation()
    else:
        logging.info("Outside business hours, skipping automation")

# Schedule jobs
schedule.every(30).minutes.do(conditional_run)  # Every 30 minutes during business hours
schedule.every().hour.do(conditional_run)       # Every hour during business hours

# Alternative: Run at specific times
schedule.every().day.at("09:00").do(run_automation)
schedule.every().day.at("12:00").do(run_automation)
schedule.every().day.at("15:00").do(run_automation)
schedule.every().day.at("18:00").do(run_automation)

if __name__ == "__main__":
    logging.info("Starting Bahar automation scheduler...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

## 🔧 Environment Setup for Scheduling

### Create a wrapper script `run_automation.sh`:

```bash
#!/bin/bash

# Set the working directory
cd /path/to/jobber

# Load environment variables
source .env

# Set up logging
LOG_FILE="logs/automation_$(date +%Y%m%d_%H%M%S).log"

# Run automation with error handling
python jobber_fsm/automation_main.py --cycle --max-projects 5 --headless 2>&1 | tee -a "$LOG_FILE"

# Check exit status
if [ $? -eq 0 ]; then
    echo "$(date): Automation completed successfully" >> "$LOG_FILE"
else
    echo "$(date): Automation failed" >> "$LOG_FILE"
fi
```

Make it executable:
```bash
chmod +x run_automation.sh
```

### Cron with wrapper script:

```bash
# Run every 30 minutes during business hours
*/30 9-18 * * 1-5 /path/to/jobber/run_automation.sh
```

## 📊 Monitoring and Alerts

### Create a monitoring script `monitor_automation.py`:

```python
#!/usr/bin/env python3
"""
Monitor automation results and send alerts
"""

import json
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText

def check_recent_results():
    """Check for recent automation results."""
    results_dir = "logs"
    recent_files = []
    
    for file in os.listdir(results_dir):
        if file.startswith("automation_") and file.endswith(".json"):
            file_path = os.path.join(results_dir, file)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time > datetime.now() - timedelta(hours=1):
                recent_files.append(file_path)
    
    return recent_files

def analyze_results(file_path):
    """Analyze automation results."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return {
            'success': data.get('success', False),
            'offers_submitted': data.get('offers_submitted', 0),
            'errors': len(data.get('errors', [])),
            'duration': data.get('duration_seconds', 0)
        }
    except Exception as e:
        return {'error': str(e)}

def send_alert(subject, message):
    """Send email alert."""
    # Configure email settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your-email@gmail.com"
    sender_password = "your-app-password"
    recipient_email = "your-email@gmail.com"
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Alert sent: {subject}")
    except Exception as e:
        print(f"Failed to send alert: {str(e)}")

def main():
    """Main monitoring function."""
    recent_files = check_recent_results()
    
    if not recent_files:
        send_alert(
            "Bahar Automation Alert",
            "No recent automation results found. System may be down."
        )
        return
    
    total_offers = 0
    total_errors = 0
    failed_runs = 0
    
    for file_path in recent_files:
        result = analyze_results(file_path)
        
        if 'error' in result:
            failed_runs += 1
        else:
            total_offers += result['offers_submitted']
            total_errors += result['errors']
            
            if not result['success']:
                failed_runs += 1
    
    # Send summary
    message = f"""
    Bahar Automation Summary (Last Hour):
    
    Files processed: {len(recent_files)}
    Total offers submitted: {total_offers}
    Total errors: {total_errors}
    Failed runs: {failed_runs}
    
    Recent files: {', '.join([os.path.basename(f) for f in recent_files])}
    """
    
    if failed_runs > 0 or total_errors > 5:
        send_alert("Bahar Automation Issues Detected", message)
    elif total_offers > 0:
        send_alert("Bahar Automation Success", message)

if __name__ == "__main__":
    main()
```

## 🎯 Recommended Scheduling Strategy

### For Production Use:

1. **Start Conservative**: Run every 2 hours during business hours
2. **Monitor Results**: Check logs and adjust frequency
3. **Use Headless Mode**: For production runs
4. **Set Daily Limits**: Prevent over-submission
5. **Enable Alerts**: Monitor for issues

### Example Production Cron:

```bash
# Production schedule - every 2 hours during business hours
0 9,11,13,15,17 * * 1-5 cd /path/to/jobber && python jobber_fsm/automation_main.py --cycle --max-projects 3 --headless --save-results logs/automation_$(date +\%Y\%m\%d_\%H\%M\%S).json

# Monitoring - check every hour
0 * * * * cd /path/to/jobber && python monitor_automation.py
```

This provides a comprehensive scheduling solution for the Bahar automation system! 🚀 