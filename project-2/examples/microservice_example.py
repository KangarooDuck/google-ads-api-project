#!/usr/bin/env python3
"""
Microservice integration example for mai_ads_toolkit

This example shows how to integrate the SDK into a microservice architecture.
Demonstrates:
1. Service class pattern
2. Dependency injection
3. Error handling
4. Response formatting
5. Configuration management
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from mai_ads_toolkit import GoogleAdsSDK, APIError, ValidationError, ConfigurationError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServiceResponse:
    """Standard service response format"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class GoogleAdsService:
    """
    Service class for Google Ads operations
    
    This demonstrates how to wrap the SDK in a service layer
    for use in microservices, APIs, or other applications.
    """
    
    def __init__(self, sdk: GoogleAdsSDK):
        """
        Initialize the service
        
        Args:
            sdk: Configured GoogleAdsSDK instance
        """
        self.sdk = sdk
        self.logger = logger
    
    def create_campaign_with_budget(self, 
                                   campaign_name: str,
                                   budget_name: str,
                                   budget_micros: int,
                                   campaign_type: str = "SEARCH",
                                   geo_location_ids: Optional[list] = None) -> ServiceResponse:
        """
        Complete campaign creation with budget and targeting
        
        Args:
            campaign_name: Name for the campaign
            budget_name: Name for the budget
            budget_micros: Budget amount in micros
            campaign_type: Campaign type
            geo_location_ids: Geographic targeting location IDs
            
        Returns:
            ServiceResponse with campaign details or error
        """
        try:
            self.logger.info(f"Creating campaign: {campaign_name}")
            
            # Step 1: Create budget
            budget_resource_name = self.sdk.campaigns.create_campaign_budget(
                budget_name=budget_name,
                amount_micros=budget_micros
            )
            
            # Step 2: Create campaign
            campaign_resource_name = self.sdk.campaigns.create_campaign(
                campaign_name=campaign_name,
                budget_resource_name=budget_resource_name,
                campaign_type=campaign_type,
                status="PAUSED"  # Start paused for safety
            )
            
            # Step 3: Add geographic targeting if specified
            geo_criteria = []
            if geo_location_ids:
                geo_criteria = self.sdk.campaigns.add_geo_targeting(
                    campaign_resource_name=campaign_resource_name,
                    location_ids=geo_location_ids
                )
            
            # Prepare response data
            response_data = {
                "campaign_resource_name": campaign_resource_name,
                "budget_resource_name": budget_resource_name,
                "geo_criteria_count": len(geo_criteria),
                "status": "PAUSED"
            }
            
            self.logger.info(f"Successfully created campaign: {campaign_resource_name}")
            
            return ServiceResponse(success=True, data=response_data)
            
        except ValidationError as e:
            self.logger.error(f"Validation error creating campaign: {e.message}")
            return ServiceResponse(
                success=False,
                error=f"Validation error: {e.message}",
                error_code="VALIDATION_ERROR",
                details={"field": e.field}
            )
            
        except APIError as e:
            self.logger.error(f"API error creating campaign: {e.message}")
            return ServiceResponse(
                success=False,
                error=f"Google Ads API error: {e.message}",
                error_code=e.error_code,
                details={"api_errors": e.api_errors}
            )
            
        except Exception as e:
            self.logger.error(f"Unexpected error creating campaign: {e}")
            return ServiceResponse(
                success=False,
                error=f"Internal error: {str(e)}",
                error_code="INTERNAL_ERROR"
            )
    
    def list_campaigns(self, include_removed: bool = False) -> ServiceResponse:
        """
        List all campaigns
        
        Args:
            include_removed: Whether to include removed campaigns
            
        Returns:
            ServiceResponse with campaign list or error
        """
        try:
            campaigns = self.sdk.campaigns.list_campaigns(include_removed=include_removed)
            
            # Format response data
            formatted_campaigns = []
            for campaign in campaigns:
                formatted_campaigns.append({
                    "id": campaign["id"],
                    "name": campaign["name"],
                    "status": campaign["status"],
                    "type": campaign["type"],
                    "budget_amount_usd": campaign["budget_amount_micros"] / 1_000_000
                })
            
            return ServiceResponse(
                success=True,
                data={
                    "campaigns": formatted_campaigns,
                    "total_count": len(formatted_campaigns)
                }
            )
            
        except APIError as e:
            self.logger.error(f"API error listing campaigns: {e.message}")
            return ServiceResponse(
                success=False,
                error=f"Failed to list campaigns: {e.message}",
                error_code=e.error_code
            )
    
    def update_campaign_status(self, 
                              campaign_resource_name: str,
                              status: str) -> ServiceResponse:
        """
        Update campaign status
        
        Args:
            campaign_resource_name: Campaign resource name
            status: New status (PAUSED, ENABLED, REMOVED)
            
        Returns:
            ServiceResponse with updated campaign or error
        """
        try:
            updated_resource = self.sdk.campaigns.update_campaign_status(
                campaign_resource_name=campaign_resource_name,
                status=status
            )
            
            return ServiceResponse(
                success=True,
                data={
                    "campaign_resource_name": updated_resource,
                    "new_status": status
                }
            )
            
        except ValidationError as e:
            return ServiceResponse(
                success=False,
                error=f"Invalid status: {e.message}",
                error_code="VALIDATION_ERROR"
            )
            
        except APIError as e:
            return ServiceResponse(
                success=False,
                error=f"Failed to update campaign: {e.message}",
                error_code=e.error_code
            )
    
    def get_audit_summary(self) -> ServiceResponse:
        """
        Get audit log summary (if audit logging is enabled)
        
        Returns:
            ServiceResponse with audit summary or error
        """
        try:
            if not self.sdk._audit_logger:
                return ServiceResponse(
                    success=False,
                    error="Audit logging is not enabled",
                    error_code="AUDIT_DISABLED"
                )
            
            # Get statistics
            stats = self.sdk._audit_logger.get_statistics()
            
            # Get recent logs
            recent_logs = self.sdk._audit_logger.get_logs(limit=10)
            
            return ServiceResponse(
                success=True,
                data={
                    "statistics": stats,
                    "recent_operations": len(recent_logs),
                    "recent_logs": [
                        {
                            "timestamp": log["timestamp"],
                            "operation": f"{log['operation_type']} {log['resource_type']}",
                            "success": log["success"]
                        }
                        for log in recent_logs
                    ]
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                success=False,
                error=f"Failed to get audit summary: {str(e)}",
                error_code="AUDIT_ERROR"
            )


# Example Flask integration (commented out to avoid Flask dependency)
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize service
sdk = GoogleAdsSDK(enable_audit_logging=True, audit_backend="database")
ads_service = GoogleAdsService(sdk)

@app.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.get_json()
    
    response = ads_service.create_campaign_with_budget(
        campaign_name=data.get('name'),
        budget_name=data.get('budget_name'),
        budget_micros=data.get('budget_micros'),
        campaign_type=data.get('type', 'SEARCH'),
        geo_location_ids=data.get('geo_locations')
    )
    
    status_code = 200 if response.success else 400
    return jsonify(response.__dict__), status_code

@app.route('/campaigns', methods=['GET'])
def list_campaigns():
    include_removed = request.args.get('include_removed', 'false').lower() == 'true'
    
    response = ads_service.list_campaigns(include_removed=include_removed)
    
    status_code = 200 if response.success else 400
    return jsonify(response.__dict__), status_code

@app.route('/campaigns/<path:campaign_resource_name>/status', methods=['PUT'])
def update_campaign_status(campaign_resource_name):
    data = request.get_json()
    status = data.get('status')
    
    response = ads_service.update_campaign_status(campaign_resource_name, status)
    
    status_code = 200 if response.success else 400
    return jsonify(response.__dict__), status_code

if __name__ == '__main__':
    app.run(debug=True)
"""


def main():
    """Demonstrate the service usage"""
    print("🏗️  Google Ads Microservice Example")
    print("=" * 40)
    
    try:
        # Initialize SDK
        print("🚀 Initializing SDK...")
        sdk = GoogleAdsSDK(
            enable_audit_logging=True,
            audit_backend="database",
            audit_database_path="microservice_audit.db"
        )
        
        # Initialize service
        service = GoogleAdsService(sdk)
        print("✅ Service initialized")
        
        # Example 1: Create campaign with budget
        print("\n💰 Creating campaign with budget...")
        response = service.create_campaign_with_budget(
            campaign_name="Microservice Test Campaign",
            budget_name="Microservice Test Budget",
            budget_micros=10000000,  # $10.00
            campaign_type="SEARCH",
            geo_location_ids=[2840]  # United States
        )
        
        if response.success:
            print("✅ Campaign created successfully")
            print(f"   Resource: {response.data['campaign_resource_name']}")
            campaign_resource = response.data['campaign_resource_name']
        else:
            print(f"❌ Failed to create campaign: {response.error}")
            return
        
        # Example 2: List campaigns
        print("\n📋 Listing campaigns...")
        response = service.list_campaigns()
        
        if response.success:
            print(f"✅ Found {response.data['total_count']} campaigns")
            for campaign in response.data['campaigns'][:3]:  # Show first 3
                print(f"   • {campaign['name']} - {campaign['status']}")
        else:
            print(f"❌ Failed to list campaigns: {response.error}")
        
        # Example 3: Update campaign status
        print("\n🔄 Updating campaign status...")
        response = service.update_campaign_status(campaign_resource, "ENABLED")
        
        if response.success:
            print("✅ Campaign status updated")
            print(f"   New status: {response.data['new_status']}")
        else:
            print(f"❌ Failed to update status: {response.error}")
        
        # Example 4: Get audit summary
        print("\n📊 Getting audit summary...")
        response = service.get_audit_summary()
        
        if response.success:
            stats = response.data['statistics']
            print("✅ Audit summary:")
            print(f"   • Total operations: {stats.get('total_operations', 0)}")
            print(f"   • Success rate: {stats.get('success_rate', 0)}%")
            print(f"   • Recent operations: {response.data['recent_operations']}")
        else:
            print(f"❌ Failed to get audit summary: {response.error}")
        
        print("\n🎉 Microservice example completed!")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()