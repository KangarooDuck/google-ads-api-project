#!/usr/bin/env python3
"""
Focused test for campaign creation issue
"""

from datetime import datetime
from config import Config
from google_ads_client import GoogleAdsManager
from campaign_manager import CampaignManager

def test_campaign_creation():
    print("Testing campaign creation...")
    
    # Initialize
    ads_manager = GoogleAdsManager()
    success = ads_manager.initialize_client()
    if not success:
        print("FAIL: Failed to initialize client")
        return
    
    campaign_manager = CampaignManager(ads_manager)
    
    # Create budget first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    budget_name = f"Test_Budget_{timestamp}"
    print(f"Creating budget: {budget_name}")
    
    try:
        budget_resource_name = campaign_manager.create_campaign_budget(
            budget_name, 10000000  # $10 daily budget
        )
        if budget_resource_name:
            print(f"SUCCESS: Budget created: {budget_resource_name}")
        else:
            print("FAIL: Budget creation failed")
            return
    except Exception as e:
        print(f"FAIL: Budget creation error: {str(e)}")
        return
    
    # Create campaign
    campaign_name = f"Test_Campaign_{timestamp}"
    print(f"Creating campaign: {campaign_name}")
    
    try:
        campaign_resource_name = campaign_manager.create_campaign(
            campaign_name, budget_resource_name, "SEARCH", "PAUSED", "MANUAL_CPC"
        )
        if campaign_resource_name:
            print(f"SUCCESS: Campaign created: {campaign_resource_name}")
        else:
            print("FAIL: Campaign creation failed")
            return
    except Exception as e:
        print(f"FAIL: Campaign creation error: {str(e)}")
        return
    
    print("Campaign creation test completed successfully!")

if __name__ == "__main__":
    test_campaign_creation()