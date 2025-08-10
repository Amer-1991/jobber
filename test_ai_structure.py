#!/usr/bin/env python3
"""
Test script to verify the AI instruction structure returns complete format
"""

from jobber_fsm.core.skills.submit_offer_with_ai import generate_fallback_offer

def test_ai_structure():
    """Test the AI instruction structure."""
    print("🧪 Testing AI Instruction Structure")
    print("=" * 50)
    
    # Test data
    project = {
        'title': 'مشروع تطوير تطبيق جوال',
        'description': 'تطوير تطبيق جوال احترافي لنظام Android و iOS',
        'budget': '10000',
        'skills': ['تطوير التطبيقات', 'React Native', 'Flutter']
    }
    
    user = {
        'skills': ['تطوير التطبيقات', 'React Native', 'JavaScript', 'TypeScript'],
        'experience': '5 سنوات',
        'rate': '80 دولار/ساعة'
    }
    
    # Generate offer
    offer = generate_fallback_offer(project, user)
    
    print("✅ Complete Structured AI Offer Generated:")
    print(f"   Duration: {offer['duration']} days")
    print(f"   Milestone Number: {offer['milestone_number']} phases")
    print(f"   Total Price: {offer['total_price_sar']} ريال")
    print(f"   Platform Communication: {offer['platform_communication']}")
    print(f"   Brief Length: {len(offer['brief'])} characters")
    print(f"   Milestones: {len(offer['milestones'])} milestones")
    
    print("\n📋 Milestones:")
    for i, milestone in enumerate(offer['milestones'], 1):
        print(f"   {i}. {milestone['deliverable']} - {milestone['budget']} ريال")
    
    print(f"\n💬 Brief Preview:")
    print("=" * 50)
    print(offer['brief'][:300] + "..." if len(offer['brief']) > 300 else offer['brief'])
    print("=" * 50)
    
    # Verify all required fields are present
    required_fields = ['duration', 'milestone_number', 'brief', 'platform_communication', 'milestones', 'total_price_sar']
    missing_fields = [field for field in required_fields if field not in offer]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    else:
        print("✅ All required fields present!")
        return True

if __name__ == "__main__":
    success = test_ai_structure()
    if success:
        print("\n🎉 AI structure test passed!")
    else:
        print("\n❌ AI structure test failed!") 