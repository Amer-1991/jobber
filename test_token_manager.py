#!/usr/bin/env python3
"""
Test Token Manager
=================

This script demonstrates the token manager functionality.
"""

import asyncio
import json
from token_manager import TokenManager

async def test_token_manager():
    """Test the token manager functionality"""
    print("🧪 Testing Token Manager")
    print("=" * 50)
    
    token_manager = TokenManager()
    
    # Show current token info
    print("\n📊 Current token info:")
    info = token_manager.get_token_info()
    if isinstance(info, dict):
        print(json.dumps(info, indent=2))
    else:
        print(info)
    
    # Get valid token (will load existing or fetch fresh)
    print("\n🔑 Getting valid token...")
    token = await token_manager.get_valid_token()
    
    if token:
        print(f"✅ Token obtained: {token[:30]}...")
        
        # Show updated info
        print("\n📊 Updated token info:")
        info = token_manager.get_token_info()
        if isinstance(info, dict):
            print(json.dumps(info, indent=2))
        else:
            print(info)
        
        # Test token reuse (should be instant)
        print("\n🔄 Testing token reuse (should be instant)...")
        token2 = await token_manager.get_valid_token()
        if token2:
            print("✅ Token reused successfully (no new API call)")
        else:
            print("❌ Failed to reuse token")
            
    else:
        print("❌ Failed to get token")

async def test_token_expiration():
    """Test token expiration handling"""
    print("\n🕐 Testing Token Expiration Handling")
    print("=" * 50)
    
    token_manager = TokenManager()
    
    # Clear any existing token
    token_manager.clear_token()
    
    # Get fresh token
    print("🔑 Getting fresh token...")
    token = await token_manager.get_valid_token()
    
    if token:
        print("✅ Fresh token obtained")
        
        # Simulate token expiration by modifying the stored data
        if token_manager.token_data:
            # Set expiration to past time
            import datetime
            token_manager.token_data["expires_at"] = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
            token_manager.save_token()
            print("⏰ Modified token to be expired")
        
        # Try to get token again (should fetch fresh)
        print("🔄 Getting token again (should fetch fresh due to expiration)...")
        token2 = await token_manager.get_valid_token()
        
        if token2:
            print("✅ Fresh token fetched after expiration")
        else:
            print("❌ Failed to fetch fresh token after expiration")
    else:
        print("❌ Failed to get initial token")

if __name__ == "__main__":
    print("🚀 Token Manager Test Suite")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_token_manager())
    asyncio.run(test_token_expiration())
    
    print("\n✨ Token Manager tests completed!") 