"""Ad extensions management functionality"""

from typing import Optional, List, Dict, Any
from google.ads.googleads.errors import GoogleAdsException
from ..core.base_client import BaseGoogleAdsClient
from ..core.exceptions import APIError, ValidationError

# Import audit logger from the project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
try:
    from audit_logger import audit_log
except ImportError as e:
    print(f"Warning: Could not import audit_log: {e}")
    # Create a no-op decorator as fallback
    def audit_log(operation_type, resource_type):
        def decorator(func):
            return func
        return decorator

class ExtensionsManager:
    """Manager for Google Ads extensions operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    @audit_log("CREATE", "EXTENSION")
    def create_callout_extension(self, callout_text: str) -> Optional[str]:
        """Create a callout extension"""
        try:
            asset_service = self.base_client.get_asset_service()
            
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create
            
            asset.callout_asset.callout_text = callout_text
            
            response = asset_service.mutate_assets(
                customer_id=self.customer_id,
                operations=[asset_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("CREATE", "EXTENSION")
    def create_sitelink_extension(self, link_text: str, final_url: str, description1: Optional[str] = None, description2: Optional[str] = None) -> Optional[str]:
        """Create a sitelink extension"""
        try:
            asset_service = self.base_client.get_asset_service()
            
            asset_operation = self.client.get_type("AssetOperation")
            asset = asset_operation.create
            
            asset.sitelink_asset.link_text = link_text
            asset.sitelink_asset.final_urls.append(final_url)
            
            if description1:
                asset.sitelink_asset.description1 = description1
            if description2:
                asset.sitelink_asset.description2 = description2
            
            response = asset_service.mutate_assets(
                customer_id=self.customer_id,
                operations=[asset_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def add_callout_extension_to_campaign(self, campaign_resource_name: str, extension_resource_name: str) -> bool:
        """Add a callout extension to a campaign"""
        try:
            campaign_extension_setting_service = self.base_client.get_campaign_extension_setting_service()
            
            campaign_extension_setting_operation = self.client.get_type("CampaignExtensionSettingOperation")
            campaign_extension_setting = campaign_extension_setting_operation.create
            
            campaign_extension_setting.campaign = campaign_resource_name
            campaign_extension_setting.extension_type = self.client.enums.ExtensionTypeEnum.CALLOUT
            
            extension_feed_item = self.client.get_type("ExtensionFeedItem")
            extension_feed_item.extension_feed_item.callout_feed_item.callout_text = extension_resource_name
            campaign_extension_setting.extension_feed_items.append(extension_feed_item)
            
            response = campaign_extension_setting_service.mutate_campaign_extension_settings(
                customer_id=self.customer_id,
                operations=[campaign_extension_setting_operation]
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def add_sitelink_extension_to_campaign(self, campaign_resource_name: str, extension_resource_name: str) -> bool:
        """Add a sitelink extension to a campaign"""
        try:
            campaign_extension_setting_service = self.base_client.get_campaign_extension_setting_service()
            
            campaign_extension_setting_operation = self.client.get_type("CampaignExtensionSettingOperation")
            campaign_extension_setting = campaign_extension_setting_operation.create
            
            campaign_extension_setting.campaign = campaign_resource_name
            campaign_extension_setting.extension_type = self.client.enums.ExtensionTypeEnum.SITELINK
            
            extension_feed_item = self.client.get_type("ExtensionFeedItem")
            extension_feed_item.extension_feed_item.sitelink_feed_item.sitelink_text = extension_resource_name
            campaign_extension_setting.extension_feed_items.append(extension_feed_item)
            
            response = campaign_extension_setting_service.mutate_campaign_extension_settings(
                customer_id=self.customer_id,
                operations=[campaign_extension_setting_operation]
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_extensions(self) -> List[Dict[str, Any]]:
        """List all extensions"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    asset.id,
                    asset.type,
                    asset.callout_asset.callout_text,
                    asset.sitelink_asset.link_text
                FROM asset
                WHERE asset.type IN ('CALLOUT', 'SITELINK')
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            extensions = []
            for row in response:
                extension_data = {
                    'id': row.asset.id,
                    'type': row.asset.type_.name,
                    'resource_name': f"customers/{self.customer_id}/assets/{row.asset.id}"
                }
                
                if row.asset.type_.name == 'CALLOUT':
                    extension_data['text'] = row.asset.callout_asset.callout_text
                elif row.asset.type_.name == 'SITELINK':
                    extension_data['text'] = row.asset.sitelink_asset.link_text
                
                extensions.append(extension_data)
            
            return extensions
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)