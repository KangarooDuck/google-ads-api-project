#!/usr/bin/env python3
"""
Test minimal campaign creation to identify the issue
"""

from datetime import datetime
from google_ads_client import GoogleAdsManager
from campaign_manager import CampaignManager

def test_minimal_campaign():
    print("Testing minimal campaign creation...")
    
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
    budget_resource_name = campaign_manager.create_campaign_budget(budget_name, 10000000)
    
    if not budget_resource_name:
        print("FAIL: Budget creation failed")
        return
    
    print(f"Budget created: {budget_resource_name}")
    
    # Try minimal campaign creation
    campaign_name = f"Test_Campaign_{timestamp}"
    print(f"Creating minimal campaign: {campaign_name}")
    
    try:
        campaign_service = campaign_manager.ads_manager.get_campaign_service()
        campaign_operation = campaign_manager.client.get_type("CampaignOperation")
        campaign = campaign_operation.create
        
        # Set only the absolute minimum required fields
        campaign.name = campaign_name
        campaign.campaign_budget = budget_resource_name
        campaign.advertising_channel_type = campaign_manager.client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.status = campaign_manager.client.enums.CampaignStatusEnum.PAUSED
        
        print("Attempting to create campaign with minimal fields...")
        response = campaign_service.mutate_campaigns(
            customer_id=campaign_manager.customer_id,
            operations=[campaign_operation]
        )
        
        campaign_resource_name = response.results[0].resource_name
        print(f"SUCCESS: Minimal campaign created: {campaign_resource_name}")
        
    except Exception as e:
        print(f"FAIL: Minimal campaign creation error: {str(e)}")
        print("Now trying with bidding strategy...")
        
        # Try with bidding strategy
        try:
            campaign_operation = campaign_manager.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            
            campaign.name = campaign_name + "_with_bidding"
            campaign.campaign_budget = budget_resource_name
            campaign.advertising_channel_type = campaign_manager.client.enums.AdvertisingChannelTypeEnum.SEARCH
            campaign.status = campaign_manager.client.enums.CampaignStatusEnum.PAUSED
            
            # Add manual CPC bidding
            campaign.manual_cpc.enhanced_cpc_enabled = True
            
            response = campaign_service.mutate_campaigns(
                customer_id=campaign_manager.customer_id,
                operations=[campaign_operation]
            )
            
            campaign_resource_name = response.results[0].resource_name
            print(f"SUCCESS: Campaign with bidding created: {campaign_resource_name}")
            
        except Exception as e2:
            print(f"FAIL: Campaign with bidding error: {str(e2)}")
            print("Trying with network settings...")
            
            # Try with network settings
            try:
                campaign_operation = campaign_manager.client.get_type("CampaignOperation")
                campaign = campaign_operation.create
                
                campaign.name = campaign_name + "_with_network"
                campaign.campaign_budget = budget_resource_name
                campaign.advertising_channel_type = campaign_manager.client.enums.AdvertisingChannelTypeEnum.SEARCH
                campaign.status = campaign_manager.client.enums.CampaignStatusEnum.PAUSED
                
                # Add network settings
                campaign.network_settings.target_google_search = True
                campaign.network_settings.target_search_network = True
                campaign.network_settings.target_content_network = False
                campaign.network_settings.target_partner_search_network = False
                
                response = campaign_service.mutate_campaigns(
                    customer_id=campaign_manager.customer_id,
                    operations=[campaign_operation]
                )
                
                campaign_resource_name = response.results[0].resource_name
                print(f"SUCCESS: Campaign with network settings created: {campaign_resource_name}")
                
            except Exception as e3:
                print(f"FAIL: Campaign with network settings error: {str(e3)}")

if __name__ == "__main__":
    test_minimal_campaign()