import json
import os
import time
import asyncio
from datetime import datetime, timedelta
import aiohttp
from dotenv import load_dotenv

class TokenManager:
    def __init__(self, token_file="bahar_token.json"):
        self.token_file = token_file
        self.token_data = None
        load_dotenv()
        
    def load_token(self):
        """Load token from file if it exists and is still valid"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    self.token_data = json.load(f)
                
                # Check if token is still valid (not expired)
                if self.token_data and self._is_token_valid():
                    print(f"✅ Loaded existing token (expires: {self.token_data.get('expires_at', 'unknown')})")
                    return self.token_data.get('token')
                else:
                    print("⚠️  Existing token is expired or invalid")
                    return None
            else:
                print("📁 No existing token file found")
                return None
        except Exception as e:
            print(f"❌ Error loading token: {str(e)}")
            return None
    
    def _is_token_valid(self):
        """Check if the stored token is still valid"""
        if not self.token_data:
            return False
        
        expires_at = self.token_data.get('expires_at')
        if not expires_at:
            return False
        
        try:
            # Parse the expiration time
            if isinstance(expires_at, str):
                expires_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expires_time = datetime.fromtimestamp(expires_at)
            
            # Add 5 minute buffer before expiration
            buffer_time = timedelta(minutes=5)
            current_time = datetime.now()
            
            return current_time < (expires_time - buffer_time)
        except Exception as e:
            print(f"❌ Error checking token validity: {str(e)}")
            return False
    
    async def get_fresh_token(self):
        """Get a fresh token from the ESSO API"""
        try:
            username = os.getenv("BAHAR_USERNAME")
            password = os.getenv("BAHAR_PASSWORD")
            
            if not username or not password:
                print("❌ Missing credentials in environment variables")
                return None
            
            print("🔄 Fetching fresh token from ESSO API...")
            
            # ESSO API endpoint (corrected from the working login function)
            esso_url = "https://esso-api.910ths.sa/api/user/login"
            
            payload = {
                "email": username,
                "password": password
            }
            
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": "https://esso.910ths.sa",
                "Referer": "https://esso.910ths.sa/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
            }
            
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    esso_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_text = await response.text()
                    print(f"ESSO API response status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            response_data = json.loads(response_text)
                            
                            # Check for successful authentication (SID cookie)
                            if "SID" in response.headers.get("Set-Cookie", ""):
                                # Extract the SID token from cookies
                                cookies = response.headers.get("Set-Cookie", "")
                                sid_match = None
                                for cookie in cookies.split(';'):
                                    if 'SID=' in cookie:
                                        sid_match = cookie.strip()
                                        break
                                
                                if sid_match:
                                    # Calculate expiration time (tokens typically expire in 24 hours)
                                    expires_at = datetime.now() + timedelta(hours=23, minutes=55)  # 5 min buffer
                                    
                                    # Store token data
                                    self.token_data = {
                                        "token": sid_match,
                                        "cookies": cookies,
                                        "created_at": datetime.now().isoformat(),
                                        "expires_at": expires_at.isoformat(),
                                        "username": username,
                                        "response_data": response_data
                                    }
                                    
                                    # Save to file
                                    self.save_token()
                                    
                                    print(f"✅ Fresh token obtained successfully!")
                                    print(f"   Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                                    return sid_match
                                else:
                                    print("❌ SID token not found in cookies")
                                    return None
                            else:
                                print("❌ No authentication cookie received from ESSO API")
                                return None
                                
                        except json.JSONDecodeError:
                            print(f"❌ Invalid JSON response from ESSO API: {response_text}")
                            return None
                    else:
                        print(f"❌ ESSO API request failed with status {response.status}: {response_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ Error fetching fresh token: {str(e)}")
            return None
    
    def save_token(self):
        """Save token data to file"""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(self.token_data, f, indent=2)
            print(f"💾 Token saved to {self.token_file}")
        except Exception as e:
            print(f"❌ Error saving token: {str(e)}")
    
    async def get_valid_token(self):
        """Get a valid token (load existing or fetch fresh)"""
        # First try to load existing token
        token = self.load_token()
        
        if token:
            return token
        
        # If no valid token exists, fetch a fresh one
        return await self.get_fresh_token()
    
    def clear_token(self):
        """Clear stored token (useful for testing or logout)"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                print(f"🗑️  Token file {self.token_file} removed")
            self.token_data = None
        except Exception as e:
            print(f"❌ Error clearing token: {str(e)}")
    
    def get_token_info(self):
        """Get information about the current token"""
        if not self.token_data:
            return "No token data available"
        
        try:
            expires_at = self.token_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    expires_time = datetime.fromtimestamp(expires_at)
                
                current_time = datetime.now()
                time_remaining = expires_time - current_time
                
                return {
                    "username": self.token_data.get('username'),
                    "created_at": self.token_data.get('created_at'),
                    "expires_at": expires_at,
                    "is_valid": self._is_token_valid(),
                    "time_remaining": str(time_remaining) if time_remaining.total_seconds() > 0 else "Expired"
                }
            else:
                return "Token data incomplete"
        except Exception as e:
            return f"Error getting token info: {str(e)}"

# Convenience function for easy token access
async def get_bahar_token():
    """Get a valid Bahar authentication token"""
    token_manager = TokenManager()
    return await token_manager.get_valid_token()

# Test function
async def test_token_manager():
    """Test the token manager functionality"""
    print("🧪 Testing Token Manager")
    print("=" * 40)
    
    token_manager = TokenManager()
    
    # Get token info
    print("\n📊 Current token info:")
    info = token_manager.get_token_info()
    print(json.dumps(info, indent=2))
    
    # Get valid token
    print("\n🔑 Getting valid token...")
    token = await token_manager.get_valid_token()
    
    if token:
        print(f"✅ Token obtained: {token[:20]}...")
        
        # Show updated info
        print("\n📊 Updated token info:")
        info = token_manager.get_token_info()
        print(json.dumps(info, indent=2))
    else:
        print("❌ Failed to get token")

if __name__ == "__main__":
    asyncio.run(test_token_manager()) 