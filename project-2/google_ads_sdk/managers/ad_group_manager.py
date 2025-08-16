"""Ad group and ad management functionality"""

from typing import Optional, List, Dict, Any
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2
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

class AdGroupManager:
    """Manager for Google Ads ad group and ad operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    @audit_log("CREATE", "AD_GROUP")
    def create_ad_group(self, name: str, campaign_resource_name: str, cpc_bid_micros: Optional[int] = None, status: str = "ENABLED") -> Optional[str]:
        """Create an ad group"""
        try:
            ad_group_service = self.base_client.get_ad_group_service()
            
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.create
            
            ad_group.name = name
            ad_group.campaign = campaign_resource_name
            ad_group.status = self.client.enums.AdGroupStatusEnum[status]
            
            if cpc_bid_micros:
                ad_group.cpc_bid_micros = cpc_bid_micros
            
            response = ad_group_service.mutate_ad_groups(
                customer_id=self.customer_id,
                operations=[ad_group_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def create_text_ad(self, ad_group_resource_name: str, headline1: str, headline2: str, description: str, final_url: str, 
                      headline3: Optional[str] = None, description2: Optional[str] = None, status: str = "ENABLED") -> Optional[str]:
        """Create a responsive search ad (text ad)"""
        try:
            # Responsive Search Ads require minimum 3 headlines and 2 descriptions
            if not headline3:
                raise ValidationError("Responsive Search Ads require at least 3 headlines. Please provide headline3.")
            if not description2:
                raise ValidationError("Responsive Search Ads require at least 2 descriptions. Please provide description2.")
            
            ad_group_ad_service = self.base_client.get_ad_group_ad_service()
            
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.create
            
            ad_group_ad.ad_group = ad_group_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[status]
            
            # Create responsive search ad (Expanded Text Ads are deprecated in v20)
            responsive_search_ad = ad_group_ad.ad.responsive_search_ad
            
            # Add headlines (minimum 3 required)
            headline_asset1 = self.client.get_type("AdTextAsset")
            headline_asset1.text = headline1
            responsive_search_ad.headlines.append(headline_asset1)
            
            headline_asset2 = self.client.get_type("AdTextAsset")
            headline_asset2.text = headline2
            responsive_search_ad.headlines.append(headline_asset2)
            
            headline_asset3 = self.client.get_type("AdTextAsset")
            headline_asset3.text = headline3
            responsive_search_ad.headlines.append(headline_asset3)
            
            # Add descriptions (minimum 2 required)
            description_asset1 = self.client.get_type("AdTextAsset")
            description_asset1.text = description
            responsive_search_ad.descriptions.append(description_asset1)
            
            description_asset2 = self.client.get_type("AdTextAsset")
            description_asset2.text = description2
            responsive_search_ad.descriptions.append(description_asset2)
            
            ad_group_ad.ad.final_urls.append(final_url)
            
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=self.customer_id,
                operations=[ad_group_ad_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("CREATE", "AD")
    def create_responsive_search_ad(self, ad_group_resource_name: str, headlines: List[str], descriptions: List[str], final_url: str, status: str = "ENABLED") -> Optional[str]:
        """Create a responsive search ad with multiple headlines and descriptions"""
        try:
            ad_group_ad_service = self.base_client.get_ad_group_ad_service()
            
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.create
            
            ad_group_ad.ad_group = ad_group_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[status]
            
            # Create responsive search ad
            responsive_search_ad = ad_group_ad.ad.responsive_search_ad
            
            # Add headlines (minimum 3, maximum 15)
            for headline in headlines:
                headline_asset = self.client.get_type("AdTextAsset")
                headline_asset.text = headline
                responsive_search_ad.headlines.append(headline_asset)
            
            # Add descriptions (minimum 2, maximum 4)
            for description in descriptions:
                description_asset = self.client.get_type("AdTextAsset")
                description_asset.text = description
                responsive_search_ad.descriptions.append(description_asset)
            
            ad_group_ad.ad.final_urls.append(final_url)
            
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=self.customer_id,
                operations=[ad_group_ad_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "AD_GROUP")
    def update_ad_group_status(self, ad_group_resource_name: str, status: str) -> Optional[str]:
        """Update ad group status"""
        try:
            ad_group_service = self.base_client.get_ad_group_service()
            
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            
            ad_group.resource_name = ad_group_resource_name
            ad_group.status = self.client.enums.AdGroupStatusEnum[status]
            
            field_mask = field_mask_pb2.FieldMask()
            field_mask.paths.append("status")
            ad_group_operation.update_mask = field_mask
            
            response = ad_group_service.mutate_ad_groups(
                customer_id=self.customer_id,
                operations=[ad_group_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "AD")
    def update_ad_status(self, ad_resource_name: str, status: str) -> Optional[str]:
        """Update ad status"""
        try:
            ad_group_ad_service = self.base_client.get_ad_group_ad_service()
            
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.update
            
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum[status]
            
            field_mask = field_mask_pb2.FieldMask()
            field_mask.paths.append("status")
            ad_group_ad_operation.update_mask = field_mask
            
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=self.customer_id,
                operations=[ad_group_ad_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("REMOVE", "AD")
    def remove_ad(self, ad_resource_name: str) -> Optional[str]:
        """Remove an ad"""
        try:
            ad_group_ad_service = self.base_client.get_ad_group_ad_service()
            
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad_operation.remove = ad_resource_name
            
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=self.customer_id,
                operations=[ad_group_ad_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_ad_groups(self, campaign_id: Optional[str] = None, include_removed: bool = False) -> List[Dict[str, Any]]:
        """List ad groups"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    ad_group.id,
                    ad_group.name,
                    ad_group.status,
                    ad_group.cpc_bid_micros,
                    campaign.id,
                    campaign.name
                FROM ad_group
            """
            
            conditions = []
            if not include_removed:
                conditions.append("ad_group.status != 'REMOVED'")
            
            if campaign_id:
                # Convert campaign ID to resource name if needed
                if campaign_id.startswith("customers/"):
                    campaign_resource_name = campaign_id
                else:
                    campaign_resource_name = f"customers/{self.customer_id}/campaigns/{campaign_id}"
                conditions.append(f"ad_group.campaign = '{campaign_resource_name}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            ad_groups = []
            for row in response:
                ad_groups.append({
                    'id': row.ad_group.id,
                    'name': row.ad_group.name,
                    'status': row.ad_group.status.name,
                    'cpc_bid_micros': row.ad_group.cpc_bid_micros,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'resource_name': f"customers/{self.customer_id}/adGroups/{row.ad_group.id}"
                })
            
            return ad_groups
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_ads(self, ad_group_id: Optional[str] = None, include_removed: bool = False) -> List[Dict[str, Any]]:
        """List ads"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    ad_group_ad.ad.id,
                    ad_group_ad.status,
                    ad_group_ad.ad.type,
                    ad_group_ad.ad.responsive_search_ad.headlines,
                    ad_group_ad.ad.responsive_search_ad.descriptions,
                    ad_group_ad.ad.final_urls,
                    ad_group.id,
                    ad_group.name,
                    campaign.id,
                    campaign.name
                FROM ad_group_ad
            """
            
            conditions = []
            if not include_removed:
                conditions.append("ad_group_ad.status != 'REMOVED'")
            
            if ad_group_id:
                # Convert ad group ID to resource name if needed
                if ad_group_id.startswith("customers/"):
                    ad_group_resource_name = ad_group_id
                else:
                    ad_group_resource_name = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
                conditions.append(f"ad_group_ad.ad_group = '{ad_group_resource_name}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            ads = []
            for row in response:
                ad_data = {
                    'ad_id': row.ad_group_ad.ad.id,
                    'status': row.ad_group_ad.status.name,
                    'type': row.ad_group_ad.ad.type_.name,
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'resource_name': f"customers/{self.customer_id}/adGroupAds/{row.ad_group.id}~{row.ad_group_ad.ad.id}"
                }
                
                # Extract ad content if it's a responsive search ad
                if row.ad_group_ad.ad.type_.name == 'RESPONSIVE_SEARCH_AD' and row.ad_group_ad.ad.responsive_search_ad:
                    headlines = row.ad_group_ad.ad.responsive_search_ad.headlines
                    if headlines:
                        ad_data['headline1'] = headlines[0].text if len(headlines) > 0 else ''
                        ad_data['headline2'] = headlines[1].text if len(headlines) > 1 else ''
                        ad_data['headline3'] = headlines[2].text if len(headlines) > 2 else ''
                    
                    descriptions = row.ad_group_ad.ad.responsive_search_ad.descriptions
                    if descriptions:
                        ad_data['description1'] = descriptions[0].text if len(descriptions) > 0 else ''
                        ad_data['description2'] = descriptions[1].text if len(descriptions) > 1 else ''
                
                # Extract final URLs
                if row.ad_group_ad.ad.final_urls:
                    ad_data['final_url'] = row.ad_group_ad.ad.final_urls[0]
                
                ads.append(ad_data)
            
            return ads
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)