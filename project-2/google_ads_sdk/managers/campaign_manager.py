"""Campaign management functionality"""

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

class CampaignManager:
    """Manager for Google Ads campaign operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    @audit_log("CREATE", "BUDGET")
    def create_campaign_budget(self, budget_name: str, amount_micros: int, delivery_method: str = "STANDARD") -> Optional[str]:
        """Create a campaign budget"""
        try:
            budget_service = self.base_client.get_campaign_budget_service()
            
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.create
            
            budget.name = budget_name
            budget.amount_micros = amount_micros
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum[delivery_method]
            
            response = budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[budget_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("CREATE", "CAMPAIGN")
    def create_campaign(self, campaign_name: str, budget_resource_name: str, campaign_type: str = "SEARCH",
                       status: str = "PAUSED", bidding_strategy_type: str = "MANUAL_CPC") -> Optional[str]:
        """Create a campaign"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            
            campaign.name = campaign_name
            campaign.campaign_budget = budget_resource_name
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum[campaign_type]
            campaign.status = self.client.enums.CampaignStatusEnum[status]
            
            # Set bidding strategy
            if bidding_strategy_type == "MANUAL_CPC":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MANUAL_CPC
                campaign.manual_cpc.enhanced_cpc_enabled = False
            elif bidding_strategy_type == "MAXIMIZE_CONVERSIONS":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
                campaign.maximize_conversions = self.client.get_type("MaximizeConversions")
            elif bidding_strategy_type == "TARGET_CPA":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.TARGET_CPA
                campaign.target_cpa = self.client.get_type("TargetCpa")
            elif bidding_strategy_type == "TARGET_ROAS":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.TARGET_ROAS
                campaign.target_roas = self.client.get_type("TargetRoas")
            
            # Set network settings
            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = True
            campaign.network_settings.target_content_network = False
            campaign.network_settings.target_partner_search_network = False
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def add_geo_targeting(self, campaign_resource_name: str, location_ids: List[str]) -> Optional[List[str]]:
        """Add geographic targeting to a campaign"""
        try:
            campaign_criterion_service = self.base_client.get_campaign_criterion_service()
            operations = []
            
            for location_id in location_ids:
                criterion_operation = self.client.get_type("CampaignCriterionOperation")
                criterion = criterion_operation.create
                
                criterion.campaign = campaign_resource_name
                criterion.location.geo_target_constant = f"geoTargetConstants/{location_id}"
                
                operations.append(criterion_operation)
            
            response = campaign_criterion_service.mutate_campaign_criteria(
                customer_id=self.customer_id,
                operations=operations
            )
            
            return [result.resource_name for result in response.results]
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def add_language_targeting(self, campaign_resource_name: str, language_codes: List[str]) -> Optional[List[str]]:
        """Add language targeting to a campaign"""
        try:
            campaign_criterion_service = self.base_client.get_campaign_criterion_service()
            operations = []
            
            for language_code in language_codes:
                criterion_operation = self.client.get_type("CampaignCriterionOperation")
                criterion = criterion_operation.create
                
                criterion.campaign = campaign_resource_name
                criterion.language.language_constant = f"languageConstants/{language_code}"
                
                operations.append(criterion_operation)
            
            response = campaign_criterion_service.mutate_campaign_criteria(
                customer_id=self.customer_id,
                operations=operations
            )
            
            return [result.resource_name for result in response.results]
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_campaign_criteria(self, campaign_resource_name: str) -> Dict[str, List[Dict]]:
        """Retrieve all targeting criteria for a campaign"""
        try:
            googleads_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT 
                    campaign_criterion.resource_name,
                    campaign_criterion.criterion_id,
                    campaign_criterion.location.geo_target_constant,
                    campaign_criterion.language.language_constant,
                    campaign_criterion.type
                FROM campaign_criterion 
                WHERE campaign_criterion.campaign = '{campaign_resource_name}'
                AND campaign_criterion.status = 'ENABLED'
            """
            
            response = googleads_service.search(customer_id=self.customer_id, query=query)
            
            geo_targets = []
            language_targets = []
            
            for row in response:
                criterion = row.campaign_criterion
                if criterion.type.name == "LOCATION":
                    geo_constant = criterion.location.geo_target_constant
                    if geo_constant:
                        geo_id = geo_constant.split('/')[-1]
                        geo_targets.append({
                            'resource_name': criterion.resource_name,
                            'geo_target_constant': geo_constant,
                            'location_id': geo_id
                        })
                elif criterion.type.name == "LANGUAGE":
                    lang_constant = criterion.language.language_constant
                    if lang_constant:
                        lang_code = lang_constant.split('/')[-1]
                        language_targets.append({
                            'resource_name': criterion.resource_name,
                            'language_constant': lang_constant,
                            'language_code': lang_code
                        })
            
            return {
                'geo_targets': geo_targets,
                'language_targets': language_targets
            }
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def remove_campaign_criteria(self, criterion_resource_names: List[str]) -> bool:
        """Remove specific campaign criteria"""
        try:
            campaign_criterion_service = self.base_client.get_campaign_criterion_service()
            operations = []
            
            for resource_name in criterion_resource_names:
                operation = self.client.get_type("CampaignCriterionOperation")
                operation.remove = resource_name
                operations.append(operation)
            
            if operations:
                response = campaign_criterion_service.mutate_campaign_criteria(
                    customer_id=self.customer_id,
                    operations=operations
                )
                return True
            
            return False
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "CAMPAIGN")
    def update_campaign_status(self, campaign_resource_name: str, status: str) -> Optional[str]:
        """Update campaign status"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            
            campaign.resource_name = campaign_resource_name
            campaign.status = self.client.enums.CampaignStatusEnum[status]
            
            campaign_operation.update_mask = field_mask_pb2.FieldMask()
            campaign_operation.update_mask.paths.append("status")
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("REMOVE", "CAMPAIGN")
    def remove_campaign(self, campaign_resource_name: str) -> Optional[str]:
        """Remove a campaign"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign_operation.remove = campaign_resource_name
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_campaigns(self, include_removed: bool = False) -> List[Dict[str, Any]]:
        """List all campaigns"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    campaign_budget.amount_micros
                FROM campaign
            """
            
            if not include_removed:
                query += " WHERE campaign.status != 'REMOVED'"
            
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            campaigns = []
            for row in response:
                campaigns.append({
                    'id': row.campaign.id,
                    'name': row.campaign.name,
                    'status': row.campaign.status.name,
                    'type': row.campaign.advertising_channel_type.name,
                    'budget_micros': row.campaign_budget.amount_micros,
                    'resource_name': f"customers/{self.customer_id}/campaigns/{row.campaign.id}"
                })
            
            return campaigns
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_campaign_details(self, campaign_resource_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed campaign information"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    campaign_budget.amount_micros,
                    campaign.start_date,
                    campaign.end_date,
                    campaign.network_settings.target_google_search,
                    campaign.network_settings.target_search_network,
                    campaign.network_settings.target_content_network,
                    campaign.network_settings.target_partner_search_network
                FROM campaign
                WHERE campaign.resource_name = '{campaign_resource_name}'
            """
            
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            for row in response:
                return {
                    'id': row.campaign.id,
                    'name': row.campaign.name,
                    'status': row.campaign.status.name,
                    'type': row.campaign.advertising_channel_type.name,
                    'budget_micros': row.campaign_budget.amount_micros,
                    'start_date': row.campaign.start_date,
                    'end_date': row.campaign.end_date,
                    'target_google_search': row.campaign.network_settings.target_google_search,
                    'target_search_network': row.campaign.network_settings.target_search_network,
                    'target_content_network': row.campaign.network_settings.target_content_network,
                    'target_partner_search_network': row.campaign.network_settings.target_partner_search_network
                }
            
            return None
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "CAMPAIGN")
    def update_campaign_name(self, campaign_resource_name: str, new_name: str) -> Optional[str]:
        """Update campaign name"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            
            campaign.resource_name = campaign_resource_name
            campaign.name = new_name
            
            campaign_operation.update_mask = field_mask_pb2.FieldMask()
            campaign_operation.update_mask.paths.append("name")
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "BUDGET")
    def update_campaign_budget(self, campaign_resource_name: str, new_budget_micros: int) -> Optional[str]:
        """Update campaign budget"""
        try:
            # First get the campaign's budget resource name
            campaign_details = self.get_campaign_details(campaign_resource_name)
            if not campaign_details:
                raise ValidationError("Could not retrieve campaign details")
            
            # Get the budget resource name
            ga_service = self.base_client.get_google_ads_service()
            query = f"""
                SELECT campaign_budget.resource_name
                FROM campaign
                WHERE campaign.resource_name = '{campaign_resource_name}'
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            budget_resource_name = None
            for row in response:
                budget_resource_name = row.campaign_budget.resource_name
                break
            
            if not budget_resource_name:
                raise ValidationError("Could not find campaign budget")
            
            # Update the budget
            budget_service = self.base_client.get_campaign_budget_service()
            
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.update
            
            budget.resource_name = budget_resource_name
            budget.amount_micros = new_budget_micros
            
            budget_operation.update_mask = field_mask_pb2.FieldMask()
            budget_operation.update_mask.paths.append("amount_micros")
            
            response = budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[budget_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def update_campaign_network_settings(self, campaign_resource_name: str, network_settings: Dict[str, bool]) -> Optional[str]:
        """Update campaign network settings"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            
            campaign.resource_name = campaign_resource_name
            campaign.network_settings.target_google_search = network_settings.get('target_google_search', True)
            campaign.network_settings.target_search_network = network_settings.get('target_search_network', True)
            campaign.network_settings.target_content_network = network_settings.get('target_content_network', False)
            campaign.network_settings.target_partner_search_network = network_settings.get('target_partner_search_network', False)
            
            campaign_operation.update_mask = field_mask_pb2.FieldMask()
            campaign_operation.update_mask.paths.append("network_settings.target_google_search")
            campaign_operation.update_mask.paths.append("network_settings.target_search_network")
            campaign_operation.update_mask.paths.append("network_settings.target_content_network")
            campaign_operation.update_mask.paths.append("network_settings.target_partner_search_network")
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)