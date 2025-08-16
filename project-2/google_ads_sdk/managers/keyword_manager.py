"""Keyword management functionality"""

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

class KeywordManager:
    """Manager for Google Ads keyword operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    @audit_log("CREATE", "KEYWORD")
    def add_keywords(self, ad_group_resource_name: str, keywords_data: List[Dict[str, Any]]) -> List[str]:
        """Add multiple keywords to an ad group"""
        try:
            ad_group_criterion_service = self.base_client.get_ad_group_criterion_service()
            operations = []
            
            for keyword_data in keywords_data:
                ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
                ad_group_criterion = ad_group_criterion_operation.create
                
                ad_group_criterion.ad_group = ad_group_resource_name
                ad_group_criterion.status = self.client.enums.AdGroupCriterionStatusEnum[
                    keyword_data.get('status', 'ENABLED')
                ]
                
                # Set keyword and match type
                ad_group_criterion.keyword.text = keyword_data['text']
                ad_group_criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum[
                    keyword_data.get('match_type', 'BROAD')
                ]
                
                # Set CPC bid if provided
                if 'cpc_bid_micros' in keyword_data and keyword_data['cpc_bid_micros']:
                    ad_group_criterion.cpc_bid_micros = keyword_data['cpc_bid_micros']
                
                operations.append(ad_group_criterion_operation)
            
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=operations
            )
            
            return [result.resource_name for result in response.results]
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def add_negative_keywords_to_campaign(self, campaign_resource_name: str, negative_keywords_data: List[Dict[str, Any]]) -> bool:
        """Add negative keywords to a campaign"""
        try:
            campaign_criterion_service = self.base_client.get_campaign_criterion_service()
            operations = []
            
            for keyword_data in negative_keywords_data:
                campaign_criterion_operation = self.client.get_type("CampaignCriterionOperation")
                campaign_criterion = campaign_criterion_operation.create
                
                campaign_criterion.campaign = campaign_resource_name
                campaign_criterion.negative = True
                campaign_criterion.keyword.text = keyword_data['text']
                campaign_criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum[
                    keyword_data.get('match_type', 'BROAD')
                ]
                
                operations.append(campaign_criterion_operation)
            
            response = campaign_criterion_service.mutate_campaign_criteria(
                customer_id=self.customer_id,
                operations=operations
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "KEYWORD")
    def update_keyword_status(self, keyword_resource_name: str, status: str) -> Optional[str]:
        """Update keyword status"""
        try:
            ad_group_criterion_service = self.base_client.get_ad_group_criterion_service()
            
            ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            ad_group_criterion = ad_group_criterion_operation.update
            
            ad_group_criterion.resource_name = keyword_resource_name
            ad_group_criterion.status = self.client.enums.AdGroupCriterionStatusEnum[status]
            
            field_mask = field_mask_pb2.FieldMask()
            field_mask.paths.append("status")
            ad_group_criterion_operation.update_mask = field_mask
            
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=[ad_group_criterion_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def update_keyword_bid(self, keyword_resource_name: str, cpc_bid_micros: int) -> Optional[str]:
        """Update keyword bid"""
        try:
            ad_group_criterion_service = self.base_client.get_ad_group_criterion_service()
            
            ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            ad_group_criterion = ad_group_criterion_operation.update
            
            ad_group_criterion.resource_name = keyword_resource_name
            ad_group_criterion.cpc_bid_micros = cpc_bid_micros
            
            field_mask = field_mask_pb2.FieldMask()
            field_mask.paths.append("cpc_bid_micros")
            ad_group_criterion_operation.update_mask = field_mask
            
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=[ad_group_criterion_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def remove_keyword(self, keyword_resource_name: str) -> Optional[str]:
        """Remove a keyword"""
        try:
            ad_group_criterion_service = self.base_client.get_ad_group_criterion_service()
            
            ad_group_criterion_operation = self.client.get_type("AdGroupCriterionOperation")
            ad_group_criterion_operation.remove = keyword_resource_name
            
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=[ad_group_criterion_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_keywords(self, ad_group_id: Optional[str] = None, include_removed: bool = False) -> List[Dict[str, Any]]:
        """List keywords"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    ad_group_criterion.criterion_id,
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group_criterion.status,
                    ad_group_criterion.cpc_bid_micros,
                    ad_group_criterion.quality_info.quality_score,
                    ad_group.id,
                    ad_group.name,
                    campaign.id,
                    campaign.name
                FROM ad_group_criterion
                WHERE ad_group_criterion.type = 'KEYWORD'
            """
            
            conditions = []
            if not include_removed:
                conditions.append("ad_group_criterion.status != 'REMOVED'")
            
            if ad_group_id:
                # Convert ad group ID to resource name if needed
                if ad_group_id.startswith("customers/"):
                    ad_group_resource_name = ad_group_id
                else:
                    ad_group_resource_name = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
                conditions.append(f"ad_group_criterion.ad_group = '{ad_group_resource_name}'")
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            keywords = []
            for row in response:
                keywords.append({
                    'criterion_id': row.ad_group_criterion.criterion_id,
                    'text': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'status': row.ad_group_criterion.status.name,
                    'cpc_bid_micros': row.ad_group_criterion.cpc_bid_micros,
                    'quality_score': row.ad_group_criterion.quality_info.quality_score,
                    'ad_group_id': row.ad_group.id,
                    'ad_group_name': row.ad_group.name,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'resource_name': f"customers/{self.customer_id}/adGroupCriteria/{row.ad_group.id}~{row.ad_group_criterion.criterion_id}"
                })
            
            return keywords
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_campaign_negative_keywords(self) -> List[Dict[str, Any]]:
        """List negative keywords for campaigns"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    campaign_criterion.criterion_id,
                    campaign_criterion.keyword.text,
                    campaign_criterion.keyword.match_type,
                    campaign.id,
                    campaign.name
                FROM campaign_criterion
                WHERE campaign_criterion.type = 'KEYWORD'
                AND campaign_criterion.negative = TRUE
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            negative_keywords = []
            for row in response:
                negative_keywords.append({
                    'criterion_id': row.campaign_criterion.criterion_id,
                    'text': row.campaign_criterion.keyword.text,
                    'match_type': row.campaign_criterion.keyword.match_type.name,
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'resource_name': f"customers/{self.customer_id}/campaignCriteria/{row.campaign_criterion.criterion_id}"
                })
            
            return negative_keywords
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_keyword_performance(self, date_range: str) -> List[Dict[str, Any]]:
        """Get keyword performance data"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    ad_group_criterion.keyword.text,
                    ad_group_criterion.keyword.match_type,
                    ad_group.name,
                    campaign.name,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM keyword_view
                WHERE segments.date DURING {date_range}
                AND ad_group_criterion.status = 'ENABLED'
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            performance_data = []
            for row in response:
                performance_data.append({
                    'keyword_text': row.ad_group_criterion.keyword.text,
                    'match_type': row.ad_group_criterion.keyword.match_type.name,
                    'ad_group_name': row.ad_group.name,
                    'campaign_name': row.campaign.name,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc,
                    'cost_per_conversion': row.metrics.cost_per_conversion
                })
            
            return performance_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)