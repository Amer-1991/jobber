# Bahar Login Skill

This module provides automated login functionality for the Bahar website, integrated into the jobber_fsm framework.

## Features

- ✅ **Automated Login**: Handles complete login flow including form filling and submission
- ✅ **Smart Detection**: Automatically detects if already logged in
- ✅ **Error Handling**: Comprehensive error detection and reporting
- ✅ **Flexible Selectors**: Uses multiple selector strategies to find login elements
- ✅ **Verification**: Verifies login success through multiple indicators
- ✅ **Logout Support**: Includes logout functionality
- ✅ **Screenshot Capture**: Takes screenshots at each step for debugging

## Installation

The Bahar login skill is already integrated into the `jobber_fsm` framework. No additional installation is required.

## Configuration

### 1. Environment Variables

Create a `.env` file in your project root with your Bahar credentials:

```bash
BAHAR_USERNAME=your_username_or_email
BAHAR_PASSWORD=your_password
BAHAR_URL=https://bahar.com
```

### 2. User Preferences

Update `jobber_fsm/user_preferences/user_preferences.txt` with your Bahar settings:

```txt
Bahar Website Credentials:
Bahar URL: https://bahar.com
Bahar Username: [YOUR_BAHAR_USERNAME]
Bahar Password: [YOUR_BAHAR_PASSWORD]

Project Preferences:
Minimum Project Budget: 100
Maximum Project Budget: 5000
Preferred Project Categories: Web Development, Mobile Development, Data Analysis, AI/ML
Offer Template: "Hi, I'm interested in your project. I have experience in [RELEVANT_SKILLS] and can deliver high-quality results within your timeline. My rate is [RATE] per hour. Looking forward to discussing this project with you!"
```

## Usage

### Basic Login

```python
from jobber_fsm.core.skills.login_bahar import login_bahar

# Login to Bahar
result = await login_bahar(
    username="your_username",
    password="your_password",
    bahar_url="https://bahar.com",
    wait_time=3.0
)

print(result)  # "Success: Successfully logged in to Bahar as your_username"
```

### Logout

```python
from jobber_fsm.core.skills.login_bahar import logout_bahar

# Logout from Bahar
result = await logout_bahar()
print(result)  # "Success: Successfully logged out from Bahar"
```

### Integration with jobber_fsm

The login skill can be used within the jobber_fsm framework by calling it from the browser navigation agent:

```python
# In your browser navigation agent
if task.description == "Login to Bahar":
    result = await login_bahar(
        username=user_preferences["Bahar Username"],
        password=user_preferences["Bahar Password"],
        bahar_url=user_preferences["Bahar URL"]
    )
    return result
```

## Testing

Run the test script to verify the login functionality:

```bash
python test_bahar_login.py
```

The test script will:
1. Check for credentials in environment variables
2. Initialize the browser
3. Attempt login (if credentials provided)
4. Test logout functionality
5. Clean up resources

## How It Works

### 1. Navigation
- Navigates to the specified Bahar URL
- Waits for page to load completely

### 2. Login Status Check
- Checks if already logged in using multiple indicators:
  - User menu elements
  - Profile links
  - Dashboard URLs
  - Avatar elements

### 3. Form Filling
- Identifies username/email field using multiple selectors:
  - `input[name='email']`
  - `input[name='username']`
  - `input[type='email']`
  - And many more...
- Fills in the username
- Identifies password field using multiple selectors:
  - `input[name='password']`
  - `input[type='password']`
  - And many more...
- Fills in the password

### 4. Form Submission
- Finds and clicks the submit button using multiple selectors:
  - `button[type='submit']`
  - `button:contains('Login')`
  - `[data-testid='login-button']`
  - And many more...
- Falls back to pressing Enter if no submit button found

### 5. Verification
- Waits for page changes/redirects
- Checks for success indicators:
  - User menu elements
  - Profile links
  - Dashboard URLs
- Checks for error indicators:
  - Error messages
  - Alert boxes
- Verifies URL changes

## Error Handling

The skill handles various error scenarios:

- **Already Logged In**: Detects and reports if already logged in
- **Form Not Found**: Reports if login form elements cannot be found
- **Invalid Credentials**: Detects and reports login errors
- **Network Issues**: Handles navigation and connection errors
- **Element Not Found**: Gracefully handles missing UI elements

## Screenshots

The skill automatically takes screenshots at key points:
- `login_bahar_start`: Before login attempt
- `login_bahar_already_logged_in`: If already logged in
- `login_bahar_success`: After successful login
- `login_bahar_failed`: If login fails
- `login_bahar_error`: If an exception occurs

## Security Notes

- **Never hardcode credentials** in your code
- **Use environment variables** for sensitive information
- **Consider using a password manager** for credential storage
- **Regularly rotate passwords** for security
- **Use HTTPS URLs** only for login

## Troubleshooting

### Common Issues

1. **"Could not find or fill username field"**
   - The website might use different selectors
   - Check the DOM structure of the login page
   - Add new selectors to the `username_selectors` list

2. **"Could not find or click submit button"**
   - The submit button might have a different structure
   - Check if the button is disabled or hidden
   - Add new selectors to the `submit_selectors` list

3. **"Login verification failed"**
   - The success indicators might be different
   - Check what elements appear after successful login
   - Add new selectors to the `success_indicators` list

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After implementing the login skill, you can:

1. **Create project discovery skills** to find available projects
2. **Implement offer crafting** using AI to generate personalized offers
3. **Add project monitoring** to check for new projects periodically
4. **Create offer submission** skills to submit offers automatically
5. **Add success tracking** to learn from accepted/rejected offers

## Contributing

To improve the Bahar login skill:

1. **Add new selectors** for different website layouts
2. **Improve error detection** for specific error messages
3. **Add support for 2FA** if required
4. **Optimize wait times** for different network conditions
5. **Add support for captcha** if implemented

## License

This skill is part of the jobber_fsm framework and follows the same license terms. 