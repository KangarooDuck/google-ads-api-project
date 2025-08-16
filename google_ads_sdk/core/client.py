"""Main Google Ads SDK client"""

from typing import Optional
from .auth import GoogleAdsCredentials
from .base_client import BaseGoogleAdsClient
from ..managers.campaign_manager import CampaignManager
from ..managers.ad_group_manager import AdGroupManager
from ..managers.keyword_manager import KeywordManager
from ..managers.reporting_manager import ReportingManager
from ..managers.bidding_manager import BiddingManager
from ..managers.extensions_manager import ExtensionsManager
from ..managers.conversion_manager import ConversionManager

class GoogleAdsSDK:
    """Main Google Ads SDK client"""
    
    def __init__(self, credentials: Optional[GoogleAdsCredentials] = None):
        """Initialize the Google Ads SDK
        
        Args:
            credentials: GoogleAdsCredentials object. If None, will load from environment.
        """
        if credentials is None:
            credentials = GoogleAdsCredentials()
        
        self.credentials = credentials
        self.base_client = BaseGoogleAdsClient(credentials)
        
        # Initialize managers
        self._campaigns = None
        self._ad_groups = None
        self._keywords = None
        self._reporting = None
        self._bidding = None
        self._extensions = None
        self._conversions = None
    
    @property
    def campaigns(self) -> CampaignManager:
        """Get the campaign manager"""
        if self._campaigns is None:
            self._campaigns = CampaignManager(self.base_client)
        return self._campaigns
    
    @property
    def ad_groups(self) -> AdGroupManager:
        """Get the ad group manager"""
        if self._ad_groups is None:
            self._ad_groups = AdGroupManager(self.base_client)
        return self._ad_groups
    
    @property
    def keywords(self) -> KeywordManager:
        """Get the keyword manager"""
        if self._keywords is None:
            self._keywords = KeywordManager(self.base_client)
        return self._keywords
    
    @property
    def reporting(self) -> ReportingManager:
        """Get the reporting manager"""
        if self._reporting is None:
            self._reporting = ReportingManager(self.base_client)
        return self._reporting
    
    @property
    def bidding(self) -> BiddingManager:
        """Get the bidding manager"""
        if self._bidding is None:
            self._bidding = BiddingManager(self.base_client)
        return self._bidding
    
    @property
    def extensions(self) -> ExtensionsManager:
        """Get the extensions manager"""
        if self._extensions is None:
            self._extensions = ExtensionsManager(self.base_client)
        return self._extensions
    
    @property
    def conversions(self) -> ConversionManager:
        """Get the conversions manager"""
        if self._conversions is None:
            self._conversions = ConversionManager(self.base_client)
        return self._conversions
    
    @property
    def customer_id(self) -> str:
        """Get the customer ID"""
        return self.base_client.customer_id