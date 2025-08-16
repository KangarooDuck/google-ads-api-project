"""Base Google Ads client implementation"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from .auth import GoogleAdsCredentials
from .exceptions import APIError

# Import audit logger from the project root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
try:
    from audit_logger import audit_logger
except ImportError as e:
    print(f"Warning: Could not import audit_logger: {e}")
    audit_logger = None

class BaseGoogleAdsClient:
    """Base client for Google Ads API operations"""
    
    def __init__(self, credentials: GoogleAdsCredentials):
        self.credentials = credentials
        self.client = None
        self.customer_id = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Ads client"""
        self.credentials.validate()
        
        credentials_dict = {
            "developer_token": self.credentials.developer_token,
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "refresh_token": self.credentials.refresh_token,
            "login_customer_id": self.credentials.login_customer_id,
            "use_proto_plus": True
        }
        
        self.client = GoogleAdsClient.load_from_dict(credentials_dict)
        self.customer_id = self.credentials.customer_id
    
    def get_service(self, service_name: str):
        """Get a Google Ads service by name"""
        if not self.client:
            raise Exception("Client not initialized")
        return self.client.get_service(service_name)
    
    def get_customer_service(self):
        return self.get_service("CustomerService")
    
    def get_campaign_service(self):
        return self.get_service("CampaignService")
    
    def get_ad_group_service(self):
        return self.get_service("AdGroupService")
    
    def get_keyword_view_service(self):
        return self.get_service("KeywordViewService")
    
    def get_ad_group_ad_service(self):
        return self.get_service("AdGroupAdService")
    
    def get_campaign_budget_service(self):
        return self.get_service("CampaignBudgetService")
    
    def get_ad_group_criterion_service(self):
        return self.get_service("AdGroupCriterionService")
    
    def get_campaign_criterion_service(self):
        return self.get_service("CampaignCriterionService")
    
    def get_conversion_action_service(self):
        return self.get_service("ConversionActionService")
    
    def get_campaign_extension_setting_service(self):
        return self.get_service("CampaignExtensionSettingService")
    
    def get_asset_service(self):
        return self.get_service("AssetService")
    
    def get_bidding_strategy_service(self):
        return self.get_service("BiddingStrategyService")
    
    def get_google_ads_service(self):
        return self.get_service("GoogleAdsService")
    
    def handle_exception(self, exception: GoogleAdsException) -> APIError:
        """Convert Google Ads exception to SDK exception"""
        error_details = []
        
        for error in exception.failure.errors:
            error_details.append({
                'error_code': error.error_code,
                'message': error.message,
                'trigger': error.trigger.value if error.trigger else None,
                'location': error.location
            })
        
        api_error = APIError(
            message=f"Google Ads API error: {exception.error.code().name}",
            error_code=exception.error.code().name,
            api_errors=error_details
        )
        
        # Log the error with enhanced details if audit logger is available
        if audit_logger:
            audit_logger.log_error(
                operation_type="API_CALL",
                resource_type="GOOGLE_ADS_API", 
                function_name="handle_exception",
                error=exception,
                parameters={"customer_id": self.customer_id}
            )
        
        return api_error