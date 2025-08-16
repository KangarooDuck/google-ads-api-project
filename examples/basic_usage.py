#!/usr/bin/env python3
"""
Basic usage example for mai_ads_toolkit

This example demonstrates how to use the SDK to:
1. Initialize the client
2. Create a campaign budget
3. Create a campaign
4. Add geographic targeting
5. List campaigns

Before running:
1. Set up your Google Ads API credentials in environment variables
2. Install the SDK: pip install mai_ads_toolkit
"""

import os
from mai_ads_toolkit import GoogleAdsSDK, APIError, ValidationError

def main():
    """Main example function"""
    
    # Initialize SDK with environment variables
    print("🚀 Initializing Google Ads SDK...")
    
    try:
        sdk = GoogleAdsSDK(
            # Credentials can be passed directly or loaded from environment
            enable_audit_logging=True,
            audit_backend="database",
            audit_database_path="example_audit.db"
        )
        print("✅ SDK initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize SDK: {e}")
        return
    
    try:
        # Step 1: Create a campaign budget
        print("\n💰 Creating campaign budget...")
        
        budget_resource_name = sdk.campaigns.create_campaign_budget(
            budget_name="Example Budget",
            amount_micros=5000000,  # $5.00 in micros
            delivery_method="STANDARD"
        )
        
        print(f"✅ Created budget: {budget_resource_name}")
        
        # Step 2: Create a campaign
        print("\n📢 Creating campaign...")
        
        campaign_resource_name = sdk.campaigns.create_campaign(
            campaign_name="Example Campaign",
            budget_resource_name=budget_resource_name,
            campaign_type="SEARCH",
            status="PAUSED",  # Start paused for safety
            bidding_strategy_type="MANUAL_CPC"
        )
        
        print(f"✅ Created campaign: {campaign_resource_name}")
        
        # Step 3: Add geographic targeting (United States)
        print("\n🌍 Adding geographic targeting...")
        
        geo_criteria = sdk.campaigns.add_geo_targeting(
            campaign_resource_name=campaign_resource_name,
            location_ids=[2840]  # United States geo target constant
        )
        
        print(f"✅ Added geo targeting: {len(geo_criteria)} locations")
        
        # Step 4: List all campaigns
        print("\n📋 Listing all campaigns...")
        
        campaigns = sdk.campaigns.list_campaigns()
        
        print(f"Found {len(campaigns)} campaigns:")
        for campaign in campaigns:
            print(f"  • {campaign['name']} - Status: {campaign['status']} - Type: {campaign['type']}")
        
        # Step 5: Demonstrate audit logging
        if sdk._audit_logger:
            print("\n📊 Audit log statistics:")
            stats = sdk._audit_logger.get_statistics()
            print(f"  • Total operations: {stats.get('total_operations', 0)}")
            print(f"  • Success rate: {stats.get('success_rate', 0)}%")
            print(f"  • Recent activity (24h): {stats.get('recent_activity_24h', 0)}")
            
            print("\n📝 Recent audit logs:")
            recent_logs = sdk._audit_logger.get_logs(limit=5)
            for log in recent_logs:
                timestamp = log['timestamp'][:19]  # Remove microseconds
                print(f"  • {timestamp} - {log['operation_type']} {log['resource_type']} - Success: {log['success']}")
        
        print("\n🎉 Example completed successfully!")
        print(f"\n💡 Your campaign '{campaign_resource_name}' is ready!")
        print("   Remember to enable it and add ad groups/keywords when ready.")
        
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        if e.field:
            print(f"   Field: {e.field}")
            
    except APIError as e:
        print(f"❌ API error: {e.message}")
        print(f"   Error code: {e.error_code}")
        
        if e.api_errors:
            print("   Details:")
            for error in e.api_errors[:3]:  # Show first 3 errors
                print(f"     • {error.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_CLIENT_ID', 
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_REFRESH_TOKEN',
        'GOOGLE_ADS_CUSTOMER_ID'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   • {var}")
        print("\nPlease set these variables before running the example.")
        print("You can use a .env file or export them directly.")
        return False
    
    return True


if __name__ == "__main__":
    print("🔧 mai_ads_toolkit - Basic Usage Example")
    print("=" * 50)
    
    if not check_environment():
        exit(1)
    
    main()