"""Custom exceptions for the Google Ads SDK"""

class GoogleAdsSDKError(Exception):
    """Base exception for Google Ads SDK errors"""
    pass

class ValidationError(GoogleAdsSDKError):
    """Raised when input validation fails"""
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field

class APIError(GoogleAdsSDKError):
    """Raised when Google Ads API request fails"""
    def __init__(self, message, error_code=None, api_errors=None):
        super().__init__(message)
        self.error_code = error_code
        self.api_errors = api_errors or []