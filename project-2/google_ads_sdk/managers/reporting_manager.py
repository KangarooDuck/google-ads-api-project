"""Reporting and analytics functionality"""

from typing import Optional, List, Dict, Any
import pandas as pd
from google.ads.googleads.errors import GoogleAdsException
from ..core.base_client import BaseGoogleAdsClient
from ..core.exceptions import APIError

class ReportingManager:
    """Manager for Google Ads reporting operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    def get_customer_metrics(self, date_range: str) -> List[Dict[str, Any]]:
        """Get customer-level metrics"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    customer.id,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM customer
                WHERE segments.date DURING {date_range}
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            metrics_data = []
            for row in response:
                metrics_data.append({
                    'customer_id': row.customer.id,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc,
                    'cost_per_conversion': row.metrics.cost_per_conversion
                })
            
            return metrics_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_campaign_metrics(self, date_range: str) -> List[Dict[str, Any]]:
        """Get campaign-level metrics"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM campaign
                WHERE segments.date DURING {date_range}
                AND campaign.status != 'REMOVED'
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            metrics_data = []
            for row in response:
                metrics_data.append({
                    'campaign_id': row.campaign.id,
                    'campaign_name': row.campaign.name,
                    'campaign_status': row.campaign.status.name,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc,
                    'cost_per_conversion': row.metrics.cost_per_conversion
                })
            
            return metrics_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_ad_group_ad_metrics(self, date_range: str) -> List[Dict[str, Any]]:
        """Get ad group ad metrics"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    campaign.name,
                    ad_group.name,
                    ad_group_ad.ad.id,
                    ad_group_ad.status,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM ad_group_ad
                WHERE segments.date DURING {date_range}
                AND ad_group_ad.status != 'REMOVED'
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            metrics_data = []
            for row in response:
                metrics_data.append({
                    'campaign_name': row.campaign.name,
                    'ad_group_name': row.ad_group.name,
                    'ad_id': row.ad_group_ad.ad.id,
                    'ad_status': row.ad_group_ad.status.name,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc,
                    'cost_per_conversion': row.metrics.cost_per_conversion
                })
            
            return metrics_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_search_term_view_metrics(self, date_range: str) -> List[Dict[str, Any]]:
        """Get search term view metrics"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    campaign.name,
                    ad_group.name,
                    search_term_view.search_term,
                    search_term_view.status,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc
                FROM search_term_view
                WHERE segments.date DURING {date_range}
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            metrics_data = []
            for row in response:
                metrics_data.append({
                    'campaign_name': row.campaign.name,
                    'ad_group_name': row.ad_group.name,
                    'search_term': row.search_term_view.search_term,
                    'search_term_status': row.search_term_view.status.name,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc
                })
            
            return metrics_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_bidding_strategy_performance(self, date_range: str) -> List[Dict[str, Any]]:
        """Get bidding strategy performance metrics"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = f"""
                SELECT
                    bidding_strategy.id,
                    bidding_strategy.name,
                    bidding_strategy.type,
                    metrics.clicks,
                    metrics.impressions,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.ctr,
                    metrics.average_cpc,
                    metrics.cost_per_conversion
                FROM bidding_strategy
                WHERE segments.date DURING {date_range}
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            metrics_data = []
            for row in response:
                metrics_data.append({
                    'strategy_id': row.bidding_strategy.id,
                    'strategy_name': row.bidding_strategy.name,
                    'strategy_type': row.bidding_strategy.type_.name,
                    'clicks': row.metrics.clicks,
                    'impressions': row.metrics.impressions,
                    'cost_micros': row.metrics.cost_micros,
                    'conversions': row.metrics.conversions,
                    'ctr': row.metrics.ctr,
                    'average_cpc': row.metrics.average_cpc,
                    'cost_per_conversion': row.metrics.cost_per_conversion
                })
            
            return metrics_data
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def create_dataframe(self, data: List[Dict[str, Any]], report_type: str) -> pd.DataFrame:
        """Create a pandas DataFrame from report data with cost conversions"""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert cost from micros to dollars
        if 'cost_micros' in df.columns:
            df['cost'] = df['cost_micros'] / 1000000
        
        # Convert average CPC from micros to dollars
        if 'average_cpc' in df.columns:
            df['average_cpc_dollars'] = df['average_cpc'] / 1000000
        
        # Convert cost per conversion from micros to dollars
        if 'cost_per_conversion' in df.columns:
            df['cost_per_conversion_dollars'] = df['cost_per_conversion'] / 1000000
        
        return df