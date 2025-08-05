# 🎯 Browser Extension Recording Guide for Bahar Login

Since the automated browser analysis is having issues, let's use browser extensions to record your login flow. This is actually a more reliable approach for complex SSO websites.

## 🔧 **Recommended Browser Extensions**

### **Option 1: Rayrun (Best for Playwright) ⭐**
- **Install**: [Rayrun Chrome Extension](https://chromewebstore.google.com/detail/rayrun/olljocejdgeipcaompahmnfebhkfmnma)
- **Perfect for**: Generating Playwright-compatible selectors
- **Features**: CSS, XPath, and Playwright locators

### **Option 2: Selenium IDE**
- **Install**: [Selenium IDE](https://chromewebstore.google.com/detail/selenium-ide/mooikfkahbdckldjjndioackbalphokd)
- **Features**: Records actions and generates code
- **Good for**: Complete flow recording

### **Option 3: Action Replay**
- **Install**: [Action Replay](https://chromewebstore.google.com/detail/action-replay/ofiinglkciflfnjchbljhfgelmobmdoi)
- **Features**: Records and replays actions
- **Good for**: Understanding the workflow

## 📋 **Step-by-Step Recording Process**

### **Step 1: Install Extension**
1. Install **Rayrun** (recommended) from Chrome Web Store
2. Pin the extension to your browser toolbar

### **Step 2: Navigate to Bahar**
1. Open a new tab and go to `https://bahr.sa`
2. Open the Rayrun extension
3. Click "Start Recording" or similar

### **Step 3: Record Login Flow**
1. **Click the login button** (دخول)
2. **Wait for SSO redirect** to complete
3. **Fill username field** (but don't submit yet)
4. **Right-click on username field** → Select "Copy Selector" or use Rayrun
5. **Fill password field** (but don't submit yet)
6. **Right-click on password field** → Select "Copy Selector" or use Rayrun
7. **Right-click on login/submit button** → Select "Copy Selector" or use Rayrun

### **Step 4: Copy the Selectors**
Record these selectors:
- **Username field selector**: `_________________`
- **Password field selector**: `_________________`
- **Submit button selector**: `_________________`
- **Login page URL**: `_________________`

## 🛠 **Alternative: Manual Inspection**

If extensions don't work, use browser DevTools:

### **Method 1: Right-Click Inspect**
1. Navigate to the login page
2. Right-click on username field → "Inspect Element"
3. In DevTools, right-click the highlighted element → "Copy selector"
4. Repeat for password field and submit button

### **Method 2: DevTools Console**
Open DevTools console and run:
```javascript
// Find username field
document.querySelector('input[type="email"]') || document.querySelector('input[type="text"]')

// Find password field  
document.querySelector('input[type="password"]')

// Find submit button
document.querySelector('button[type="submit"]') || document.querySelector('input[type="submit"]')
```

## 📝 **What to Look For**

### **Username Field Indicators:**
- `input[type="email"]`
- `input[type="text"]`
- `input[name*="email"]`
- `input[name*="username"]`
- `input[placeholder*="email"]`
- `input[id*="email"]`

### **Password Field Indicators:**
- `input[type="password"]`
- `input[name*="password"]`
- `input[id*="password"]`

### **Submit Button Indicators:**
- `button[type="submit"]`
- `input[type="submit"]`
- `button` containing text like "Login", "Sign In", "دخول"

## 🔄 **Once You Have the Selectors**

When you get the selectors, we'll update the `login_bahar.py` file:

```python
# Replace these arrays in login_bahar.py
username_selectors = [
    "YOUR_USERNAME_SELECTOR_HERE",
    # ... existing selectors as fallback
]

password_selectors = [
    "YOUR_PASSWORD_SELECTOR_HERE", 
    # ... existing selectors as fallback
]

submit_selectors = [
    "YOUR_SUBMIT_SELECTOR_HERE",
    # ... existing selectors as fallback
]
```

## 🎯 **Quick Test Script**

Once you have selectors, create a test file:

```python
#!/usr/bin/env python3
import asyncio
from jobber_fsm.core.skills.login_bahar import login_bahar

async def test_with_new_selectors():
    result = await login_bahar(
        username="your_username",
        password="your_password", 
        bahar_url="https://bahr.sa"
    )
    print(result)

asyncio.run(test_with_new_selectors())
```

## 📞 **Next Steps**

1. **Install Rayrun extension**
2. **Record the login flow**
3. **Copy the selectors**
4. **Share them with me**
5. **I'll update the login_bahar.py file**
6. **Test the updated login functionality**

This approach is much more reliable than automated browser analysis for complex SSO websites!