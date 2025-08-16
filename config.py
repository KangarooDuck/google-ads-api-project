import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
    GOOGLE_ADS_CLIENT_ID = os.getenv('GOOGLE_ADS_CLIENT_ID')
    GOOGLE_ADS_CLIENT_SECRET = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
    GOOGLE_ADS_REFRESH_TOKEN = os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
    GOOGLE_ADS_CUSTOMER_ID = os.getenv('GOOGLE_ADS_CUSTOMER_ID')
    GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID')
    
    @classmethod
    def validate_config(cls):
        required_vars = [
            'GOOGLE_ADS_DEVELOPER_TOKEN',
            'GOOGLE_ADS_CLIENT_ID',
            'GOOGLE_ADS_CLIENT_SECRET',
            'GOOGLE_ADS_REFRESH_TOKEN',
            'GOOGLE_ADS_CUSTOMER_ID'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Auto-configure LOGIN_CUSTOMER_ID for both manager and non-manager accounts
        if not cls.GOOGLE_ADS_LOGIN_CUSTOMER_ID:
            # If no login customer ID provided, assume non-manager account
            cls.GOOGLE_ADS_LOGIN_CUSTOMER_ID = cls.GOOGLE_ADS_CUSTOMER_ID
            print(f"INFO: Using customer ID as login customer ID (non-manager account mode)")
        else:
            print(f"INFO: Using provided login customer ID (manager account mode)")
        
        return True