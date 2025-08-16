"""
Google Ads SDK - A Python library for Google Ads API management
Based on the working Streamlit app implementation
"""

from .core.client import GoogleAdsSDK
from .core.auth import GoogleAdsCredentials
from .core.exceptions import GoogleAdsSDKError, ValidationError, APIError

__version__ = "1.0.0"
__all__ = ["GoogleAdsSDK", "GoogleAdsCredentials", "GoogleAdsSDKError", "ValidationError", "APIError"]