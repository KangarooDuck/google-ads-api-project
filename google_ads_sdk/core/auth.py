"""Authentication and configuration for Google Ads SDK"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class GoogleAdsCredentials:
    """Google Ads API credentials configuration"""
    
    def __init__(self,
                 developer_token: str = None,
                 client_id: str = None, 
                 client_secret: str = None,
                 refresh_token: str = None,
                 customer_id: str = None,
                 login_customer_id: str = None):
        
        # Use provided values or fall back to environment variables
        self.developer_token = developer_token or os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
        self.client_id = client_id or os.getenv('GOOGLE_ADS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('GOOGLE_ADS_CLIENT_SECRET')
        self.refresh_token = refresh_token or os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
        self.customer_id = customer_id or os.getenv('GOOGLE_ADS_CUSTOMER_ID')
        self.login_customer_id = login_customer_id or os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID')
        
        # Auto-configure LOGIN_CUSTOMER_ID for both manager and non-manager accounts
        if not self.login_customer_id:
            self.login_customer_id = self.customer_id
    
    def validate(self):
        """Validate that all required credentials are present"""
        required_fields = [
            ('developer_token', self.developer_token),
            ('client_id', self.client_id),
            ('client_secret', self.client_secret),
            ('refresh_token', self.refresh_token),
            ('customer_id', self.customer_id)
        ]
        
        missing = [field for field, value in required_fields if not value]
        
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")
        
        return True