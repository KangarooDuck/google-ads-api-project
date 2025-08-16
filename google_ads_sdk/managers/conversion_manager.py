"""Conversion tracking management functionality"""

from typing import Optional, List, Dict, Any
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2
from ..core.base_client import BaseGoogleAdsClient
from ..core.exceptions import APIError, ValidationError

class ConversionManager:
    """Manager for Google Ads conversion tracking operations"""
    
    def __init__(self, client: BaseGoogleAdsClient):
        self.client = client.client
        self.customer_id = client.customer_id
        self.base_client = client
    
    def create_conversion_action(self, name: str, category: str = "DEFAULT", 
                               value_settings: Optional[Dict] = None, 
                               count_type: str = "ONE_PER_CLICK",
                               attribution_model: str = "LAST_CLICK") -> Optional[str]:
        """Create a conversion action"""
        try:
            conversion_action_service = self.base_client.get_conversion_action_service()
            
            conversion_action_operation = self.client.get_type("ConversionActionOperation")
            conversion_action = conversion_action_operation.create
            
            conversion_action.name = name
            conversion_action.category = self.client.enums.ConversionActionCategoryEnum[category]
            conversion_action.type_ = self.client.enums.ConversionActionTypeEnum.WEBPAGE
            conversion_action.status = self.client.enums.ConversionActionStatusEnum.ENABLED
            conversion_action.counting_type = self.client.enums.ConversionActionCountingTypeEnum[count_type]
            
            # Set attribution model
            conversion_action.attribution_model_settings.attribution_model = self.client.enums.AttributionModelEnum[attribution_model]
            
            # Set value settings
            if value_settings:
                if value_settings.get('default_value'):
                    conversion_action.value_settings.default_value = value_settings['default_value']
                    conversion_action.value_settings.always_use_default_value = value_settings.get('always_use_default', False)
            
            response = conversion_action_service.mutate_conversion_actions(
                customer_id=self.customer_id,
                operations=[conversion_action_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def list_conversion_actions(self) -> List[Dict[str, Any]]:
        """List all conversion actions"""
        try:
            ga_service = self.base_client.get_google_ads_service()
            
            query = """
                SELECT
                    conversion_action.id,
                    conversion_action.name,
                    conversion_action.type,
                    conversion_action.category,
                    conversion_action.status,
                    conversion_action.counting_type
                FROM conversion_action
                WHERE conversion_action.type = 'WEBPAGE'
            """
            
            response = ga_service.search(customer_id=self.customer_id, query=query)
            
            conversions = []
            for row in response:
                conversions.append({
                    'id': row.conversion_action.id,
                    'name': row.conversion_action.name,
                    'type': row.conversion_action.type_.name,
                    'category': row.conversion_action.category.name,
                    'status': row.conversion_action.status.name,
                    'counting_type': row.conversion_action.counting_type.name,
                    'resource_name': f"customers/{self.customer_id}/conversionActions/{row.conversion_action.id}"
                })
            
            return conversions
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def update_conversion_action_status(self, conversion_resource_name: str, status: str) -> bool:
        """Update conversion action status"""
        try:
            conversion_action_service = self.base_client.get_conversion_action_service()
            
            conversion_action_operation = self.client.get_type("ConversionActionOperation")
            conversion_action = conversion_action_operation.update
            
            conversion_action.resource_name = conversion_resource_name
            conversion_action.status = self.client.enums.ConversionActionStatusEnum[status]
            
            field_mask = field_mask_pb2.FieldMask()
            field_mask.paths.append("status")
            conversion_action_operation.update_mask = field_mask
            
            response = conversion_action_service.mutate_conversion_actions(
                customer_id=self.customer_id,
                operations=[conversion_action_operation]
            )
            
            return True
            
        except GoogleAdsException as ex:
            raise self.base_client.handle_exception(ex)
    
    def get_conversion_tracking_status(self) -> Dict[str, Any]:
        """Get conversion tracking status"""
        try:
            conversions = self.list_conversion_actions()
            
            if not conversions:
                return {
                    'status': 'not_configured',
                    'message': 'No conversion actions found',
                    'recommendations': [
                        'Create at least one conversion action',
                        'Install tracking code on your website'
                    ]
                }
            
            enabled_conversions = [c for c in conversions if c['status'] == 'ENABLED']
            if not enabled_conversions:
                return {
                    'status': 'configured_but_disabled',
                    'message': f'Found {len(conversions)} conversion actions but none are enabled',
                    'recommendations': [
                        'Enable at least one conversion action',
                        'Verify tracking code is properly installed'
                    ]
                }
            
            return {
                'status': 'configured',
                'message': f'Conversion tracking is active with {len(enabled_conversions)} enabled actions',
                'recommendations': []
            }
            
        except Exception as ex:
            return {
                'status': 'error',
                'message': f'Error checking conversion tracking: {str(ex)}',
                'recommendations': ['Check your API credentials and permissions']
            }
    
    def generate_website_conversion_snippet(self, conversion_id: str, conversion_label: str, 
                                          conversion_value: Optional[float] = None) -> Dict[str, Any]:
        """Generate website conversion tracking code snippet"""
        base_snippet = f"""
<!-- Global site tag (gtag.js) - Google Ads: {conversion_id} -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-{conversion_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'AW-{conversion_id}');
</script>
"""
        
        value_snippet = ""
        if conversion_value:
            value_snippet = f"""
  'value': {conversion_value},
  'currency': 'USD'"""
        
        conversion_snippet = f"""
<!-- Event snippet for {conversion_label} conversion page -->
<script>
  gtag('event', 'conversion', {{
      'send_to': 'AW-{conversion_id}/{conversion_label}',{value_snippet}
  }});
</script>
"""
        
        return {
            'base_snippet': base_snippet.strip(),
            'conversion_snippet': conversion_snippet.strip(),
            'installation_instructions': [
                '1. Add the base tracking code to ALL pages of your website in the <head> section',
                '2. Add the conversion event code ONLY to your conversion/thank-you pages',
                '3. Test the implementation using Google Tag Assistant',
                '4. Allow 24-48 hours for conversion data to appear in your account'
            ]
        }
    
    def generate_call_conversion_snippet(self, conversion_id: str, conversion_label: str, 
                                       phone_number: str) -> Dict[str, Any]:
        """Generate call conversion tracking code snippet"""
        call_snippet = f"""
<!-- Global site tag (gtag.js) - Google Ads: {conversion_id} -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-{conversion_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'AW-{conversion_id}');
</script>

<!-- Call tracking snippet -->
<script>
  gtag('config', 'AW-{conversion_id}/{conversion_label}', {{
    'phone_conversion_number': '{phone_number}'
  }});
</script>
"""
        
        return {
            'call_snippet': call_snippet.strip(),
            'installation_instructions': [
                '1. Add this code to ALL pages of your website in the <head> section',
                '2. Replace the phone numbers on your site with the Google forwarding number',
                '3. Test by calling the number and verifying it rings to your business',
                '4. Allow 24-48 hours for call conversion data to appear'
            ]
        }