#!/usr/bin/env python3
"""
Test ad creation fix
"""

from datetime import datetime
from google_ads_client import GoogleAdsManager
from campaign_manager import CampaignManager
from ad_group_manager import AdGroupManager

def test_ad_creation():
    print("Testing ad creation...")
    
    # Initialize
    ads_manager = GoogleAdsManager()
    success = ads_manager.initialize_client()
    if not success:
        print("FAIL: Failed to initialize client")
        return
    
    campaign_manager = CampaignManager(ads_manager)
    ad_group_manager = AdGroupManager(ads_manager)
    
    # Create campaign and ad group first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    budget_name = f"Test_Budget_{timestamp}"
    budget_resource_name = campaign_manager.create_campaign_budget(budget_name, 10000000)
    
    if not budget_resource_name:
        print("FAIL: Budget creation failed")
        return
    
    campaign_name = f"Test_Campaign_{timestamp}"
    campaign_resource_name = campaign_manager.create_campaign(
        campaign_name, budget_resource_name, "SEARCH", "PAUSED", "MANUAL_CPC"
    )
    
    if not campaign_resource_name:
        print("FAIL: Campaign creation failed")
        return
    
    ad_group_name = f"Test_AdGroup_{timestamp}"
    ad_group_resource_name = ad_group_manager.create_ad_group(
        ad_group_name, campaign_resource_name, 1000000
    )
    
    if not ad_group_resource_name:
        print("FAIL: Ad group creation failed")
        return
    
    print("Created campaign and ad group, now testing ad creation...")
    
    # Test responsive search ad creation
    try:
        ad_resource_name = ad_group_manager.create_text_ad(
            ad_group_resource_name,
            "Test Headline 1",
            "Test Headline 2",
            "Test description for the ad",
            "https://example.com",
            "Test Headline 3",  # RSA needs at least 3 headlines
            "Test description 2"  # RSA needs at least 2 descriptions
        )
        
        if ad_resource_name:
            print(f"SUCCESS: Ad created: {ad_resource_name}")
            
            # Test ad status update
            result = ad_group_manager.update_ad_status(ad_resource_name, "ENABLED")
            if result:
                print("SUCCESS: Ad status updated")
            else:
                print("FAIL: Ad status update failed")
            
        else:
            print("FAIL: Ad creation failed")
            
    except Exception as e:
        print(f"FAIL: Ad creation error: {str(e)}")
        return
    
    print("Ad creation test completed!")

if __name__ == "__main__":
    test_ad_creation()