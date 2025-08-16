"""Bidding strategy management functionality"""

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

class BiddingManager:
    """Manager for Google Ads bidding strategy operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    def create_target_cpa_bidding_strategy(self, name: str, target_cpa_micros: int) -> Optional[str]:
        """Create a Target CPA bidding strategy"""
        try:
            bidding_strategy_service = self.base_client.get_bidding_strategy_service()
            
            bidding_strategy_operation = self.client.get_type("BiddingStrategyOperation")
            bidding_strategy = bidding_strategy_operation.create
            
            bidding_strategy.name = name
            bidding_strategy.target_cpa.target_cpa_micros = target_cpa_micros
            
            response = bidding_strategy_service.mutate_bidding_strategies(
                customer_id=self.customer_id,
                operations=[bidding_strategy_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def create_target_roas_bidding_strategy(self, name: str, target_roas: float) -> Optional[str]:
        """Create a Target ROAS bidding strategy"""
        try:
            bidding_strategy_service = self.base_client.get_bidding_strategy_service()
            
            bidding_strategy_operation = self.client.get_type("BiddingStrategyOperation")
            bidding_strategy = bidding_strategy_operation.create
            
            bidding_strategy.name = name
            bidding_strategy.target_roas.target_roas = target_roas
            
            response = bidding_strategy_service.mutate_bidding_strategies(
                customer_id=self.customer_id,
                operations=[bidding_strategy_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    @audit_log("UPDATE", "BIDDING_STRATEGY")
    def apply_bidding_strategy_to_campaign(self, campaign_resource_name: str, bidding_strategy_type: str, **kwargs) -> bool:
        """Apply a bidding strategy to a campaign"""
        try:
            campaign_service = self.base_client.get_campaign_service()
            
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            
            campaign.resource_name = campaign_resource_name
            
            # Apply different bidding strategy types
            if bidding_strategy_type == "TARGET_CPA":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.TARGET_CPA
                if 'target_cpa_micros' in kwargs:
                    campaign.target_cpa.target_cpa_micros = kwargs['target_cpa_micros']
                
                field_mask = field_mask_pb2.FieldMask()
                field_mask.paths.append("bidding_strategy_type")
                field_mask.paths.append("target_cpa.target_cpa_micros")
                campaign_operation.update_mask = field_mask
                
            elif bidding_strategy_type == "TARGET_ROAS":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.TARGET_ROAS
                if 'target_roas' in kwargs:
                    campaign.target_roas.target_roas = kwargs['target_roas']
                
                field_mask = field_mask_pb2.FieldMask()
                field_mask.paths.append("bidding_strategy_type")
                field_mask.paths.append("target_roas.target_roas")
                campaign_operation.update_mask = field_mask
                
            elif bidding_strategy_type == "MAXIMIZE_CONVERSIONS":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
                if 'target_spend_micros' in kwargs:
                    campaign.maximize_conversions.target_spend_micros = kwargs['target_spend_micros']
                
                field_mask = field_mask_pb2.FieldMask()
                field_mask.paths.append("bidding_strategy_type")
                if 'target_spend_micros' in kwargs:
                    field_mask.paths.append("maximize_conversions.target_spend_micros")
                campaign_operation.update_mask = field_mask
                
            elif bidding_strategy_type == "MANUAL_CPC":
                campaign.bidding_strategy_type = self.client.enums.BiddingStrategyTypeEnum.MANUAL_CPC
                enhanced_cpc_enabled = kwargs.get('enhanced_cpc_enabled', False)
                campaign.manual_cpc.enhanced_cpc_enabled = enhanced_cpc_enabled
                
                field_mask = field_mask_pb2.FieldMask()
                field_mask.paths.append("bidding_strategy_type")
                field_mask.paths.append("manual_cpc.enhanced_cpc_enabled")
                campaign_operation.update_mask = field_mask
            
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation]
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_bidding_strategies(self) -> List[Dict[str, Any]]:
        """List all bidding strategies"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    bidding_strategy.id,
                    bidding_strategy.name,
                    bidding_strategy.type,
                    bidding_strategy.target_cpa.target_cpa_micros,
                    bidding_strategy.target_roas.target_roas
                FROM bidding_strategy
                WHERE bidding_strategy.type IN ('TARGET_CPA', 'TARGET_ROAS', 'MAXIMIZE_CONVERSIONS')
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            strategies = []
            for row in response:
                strategy_data = {
                    'id': row.bidding_strategy.id,
                    'name': row.bidding_strategy.name,
                    'type': row.bidding_strategy.type_.name,
                    'resource_name': f"customers/{self.customer_id}/biddingStrategies/{row.bidding_strategy.id}"
                }
                
                # Add type-specific data
                if row.bidding_strategy.type_.name == 'TARGET_CPA':
                    strategy_data['target_cpa_micros'] = row.bidding_strategy.target_cpa.target_cpa_micros
                elif row.bidding_strategy.type_.name == 'TARGET_ROAS':
                    strategy_data['target_roas'] = row.bidding_strategy.target_roas.target_roas
                
                strategies.append(strategy_data)
            
            return strategies
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def update_bidding_strategy(self, strategy_resource_name: str, **kwargs) -> bool:
        """Update a bidding strategy"""
        try:
            bidding_strategy_service = self.base_client.get_bidding_strategy_service()
            
            bidding_strategy_operation = self.client.get_type("BiddingStrategyOperation")
            bidding_strategy = bidding_strategy_operation.update
            
            bidding_strategy.resource_name = strategy_resource_name
            
            field_mask = field_mask_pb2.FieldMask()
            
            # Update name if provided
            if 'name' in kwargs:
                bidding_strategy.name = kwargs['name']
                field_mask.paths.append("name")
            
            # Update Target CPA
            if 'target_cpa_micros' in kwargs:
                bidding_strategy.target_cpa.target_cpa_micros = kwargs['target_cpa_micros']
                field_mask.paths.append("target_cpa.target_cpa_micros")
            
            # Update Target ROAS
            if 'target_roas' in kwargs:
                bidding_strategy.target_roas.target_roas = kwargs['target_roas']
                field_mask.paths.append("target_roas.target_roas")
            
            bidding_strategy_operation.update_mask = field_mask
            
            response = bidding_strategy_service.mutate_bidding_strategies(
                customer_id=self.customer_id,
                operations=[bidding_strategy_operation]
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)