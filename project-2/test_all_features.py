#!/usr/bin/env python3
"""
Comprehensive Test Suite for Google Ads API Tool
Tests all functionality to ensure everything works without errors.
"""

import sys
import traceback
from datetime import datetime
from config import Config
from google_ads_client import GoogleAdsManager
from campaign_manager import CampaignManager
from ad_group_manager import AdGroupManager
from keyword_manager import KeywordManager
from conversion_manager import ConversionManager
from extensions_manager import ExtensionsManager
from bidding_manager import BiddingManager
from reporting_manager import ReportingManager

class TestResult:
    def __init__(self, test_name, passed=False, error=None):
        self.test_name = test_name
        self.passed = passed
        self.error = error
        self.timestamp = datetime.now()
    
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] - {self.test_name}"

class GoogleAdsAPITester:
    def __init__(self):
        self.results = []
        self.ads_manager = None
        self.managers = {}
        self.test_resources = {
            'campaign_resource_name': None,
            'ad_group_resource_name': None,
            'keyword_resource_name': None,
            'ad_resource_name': None,
            'extension_resource_name': None,
            'bidding_strategy_resource_name': None,
            'conversion_action_resource_name': None
        }
    
    def log_test(self, test_name, passed, error=None):
        result = TestResult(test_name, passed, error)
        self.results.append(result)
        print(f"{result}")
        if error:
            print(f"   Error: {error}")
    
    def run_test(self, test_function, test_name):
        try:
            test_function()
            self.log_test(test_name, True)
            return True
        except Exception as e:
            self.log_test(test_name, False, str(e))
            print(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def test_authentication(self):
        """Test Google Ads API authentication"""
        self.ads_manager = GoogleAdsManager()
        success = self.ads_manager.initialize_client()
        if not success:
            raise Exception("Failed to initialize Google Ads client")
        
        # Initialize all managers
        self.managers = {
            'campaign_manager': CampaignManager(self.ads_manager),
            'ad_group_manager': AdGroupManager(self.ads_manager),
            'keyword_manager': KeywordManager(self.ads_manager),
            'conversion_manager': ConversionManager(self.ads_manager),
            'extensions_manager': ExtensionsManager(self.ads_manager),
            'bidding_manager': BiddingManager(self.ads_manager),
            'reporting_manager': ReportingManager(self.ads_manager)
        }
    
    def test_campaign_listing(self):
        """Test listing existing campaigns"""
        campaigns = self.managers['campaign_manager'].list_campaigns()
        if not isinstance(campaigns, list):
            raise Exception("Campaign listing returned non-list")
        print(f"   Found {len(campaigns)} campaigns")
    
    def test_campaign_creation(self):
        """Test creating a new campaign"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        budget_name = f"Test_Budget_{timestamp}"
        campaign_name = f"Test_Campaign_{timestamp}"
        
        # Create budget
        budget_resource_name = self.managers['campaign_manager'].create_campaign_budget(
            budget_name, 10000000  # $10 daily budget
        )
        if not budget_resource_name:
            raise Exception("Failed to create campaign budget")
        
        # Create campaign
        campaign_resource_name = self.managers['campaign_manager'].create_campaign(
            campaign_name, budget_resource_name, "SEARCH", "PAUSED", "MANUAL_CPC"
        )
        if not campaign_resource_name:
            raise Exception("Failed to create campaign")
        
        self.test_resources['campaign_resource_name'] = campaign_resource_name
        print(f"   Created campaign: {campaign_resource_name}")
    
    def test_campaign_geo_targeting(self):
        """Test adding geo targeting to campaign"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        # Add geo targeting (United States)
        result = self.managers['campaign_manager'].add_geo_targeting(
            self.test_resources['campaign_resource_name'], ["2840"]
        )
        if not result:
            raise Exception("Failed to add geo targeting")
        print(f"   Added geo targeting: {len(result)} locations")
    
    def test_campaign_language_targeting(self):
        """Test adding language targeting to campaign"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        # Add language targeting (English)
        result = self.managers['campaign_manager'].add_language_targeting(
            self.test_resources['campaign_resource_name'], ["1000"]
        )
        if not result:
            raise Exception("Failed to add language targeting")
        print(f"   Added language targeting: {len(result)} languages")
    
    def test_campaign_status_update(self):
        """Test updating campaign status"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        # Enable campaign
        result = self.managers['campaign_manager'].update_campaign_status(
            self.test_resources['campaign_resource_name'], "ENABLED"
        )
        if not result:
            raise Exception("Failed to enable campaign")
        
        # Pause campaign
        result = self.managers['campaign_manager'].update_campaign_status(
            self.test_resources['campaign_resource_name'], "PAUSED"
        )
        if not result:
            raise Exception("Failed to pause campaign")
        print("   Campaign status updates successful")
    
    def test_campaign_details(self):
        """Test getting campaign details"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        details = self.managers['campaign_manager'].get_campaign_details(
            self.test_resources['campaign_resource_name']
        )
        if not details:
            raise Exception("Failed to get campaign details")
        print(f"   Retrieved campaign details: {details['name']}")
    
    def test_campaign_name_update(self):
        """Test updating campaign name"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"Test_Campaign_Updated_{timestamp}"
        
        result = self.managers['campaign_manager'].update_campaign_name(
            self.test_resources['campaign_resource_name'], new_name
        )
        if not result:
            raise Exception("Failed to update campaign name")
        print(f"   Updated campaign name to: {new_name}")
    
    def test_campaign_budget_update(self):
        """Test updating campaign budget"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        result = self.managers['campaign_manager'].update_campaign_budget(
            self.test_resources['campaign_resource_name'], 20000000  # $20 daily budget
        )
        if not result:
            raise Exception("Failed to update campaign budget")
        print("   Updated campaign budget to $20.00")
    
    def test_campaign_network_settings(self):
        """Test updating campaign network settings"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        network_settings = {
            'target_google_search': True,
            'target_search_network': True,
            'target_content_network': False,
            'target_partner_search_network': False
        }
        
        result = self.managers['campaign_manager'].update_campaign_network_settings(
            self.test_resources['campaign_resource_name'], network_settings
        )
        if not result:
            raise Exception("Failed to update network settings")
        print("   Updated campaign network settings")
    
    def test_ad_group_creation(self):
        """Test creating ad group"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ad_group_name = f"Test_AdGroup_{timestamp}"
        
        ad_group_resource_name = self.managers['ad_group_manager'].create_ad_group(
            ad_group_name, self.test_resources['campaign_resource_name'], 1000000  # $1 CPC
        )
        if not ad_group_resource_name:
            raise Exception("Failed to create ad group")
        
        self.test_resources['ad_group_resource_name'] = ad_group_resource_name
        print(f"   Created ad group: {ad_group_resource_name}")
    
    def test_ad_group_listing(self):
        """Test listing ad groups"""
        ad_groups = self.managers['ad_group_manager'].list_ad_groups()
        if not isinstance(ad_groups, list):
            raise Exception("Ad group listing returned non-list")
        print(f"   Found {len(ad_groups)} ad groups")
    
    def test_ad_group_status_update(self):
        """Test updating ad group status"""
        if not self.test_resources['ad_group_resource_name']:
            raise Exception("No test ad group available")
        
        result = self.managers['ad_group_manager'].update_ad_group_status(
            self.test_resources['ad_group_resource_name'], "ENABLED"
        )
        if not result:
            raise Exception("Failed to update ad group status")
        print("   Updated ad group status to ENABLED")
    
    def test_text_ad_creation(self):
        """Test creating text ad"""
        if not self.test_resources['ad_group_resource_name']:
            raise Exception("No test ad group available")
        
        ad_resource_name = self.managers['ad_group_manager'].create_text_ad(
            self.test_resources['ad_group_resource_name'],
            "Test Headline 1",
            "Test Headline 2", 
            "Test description for the ad",
            "https://example.com",
            "Test Headline 3",  # RSA needs at least 3 headlines
            "Test description 2"  # RSA needs at least 2 descriptions
        )
        if not ad_resource_name:
            raise Exception("Failed to create text ad")
        
        self.test_resources['ad_resource_name'] = ad_resource_name
        print(f"   Created text ad: {ad_resource_name}")
    
    def test_ad_listing(self):
        """Test listing ads"""
        ads = self.managers['ad_group_manager'].list_ads()
        if not isinstance(ads, list):
            raise Exception("Ad listing returned non-list")
        print(f"   Found {len(ads)} ads")
    
    def test_ad_status_update(self):
        """Test updating ad status"""
        if not self.test_resources['ad_resource_name']:
            raise Exception("No test ad available")
        
        result = self.managers['ad_group_manager'].update_ad_status(
            self.test_resources['ad_resource_name'], "ENABLED"
        )
        if not result:
            raise Exception("Failed to update ad status")
        print("   Updated ad status to ENABLED")
    
    def test_keyword_addition(self):
        """Test adding keywords"""
        if not self.test_resources['ad_group_resource_name']:
            raise Exception("No test ad group available")
        
        keywords_data = [
            {'text': 'test keyword', 'match_type': 'BROAD', 'cpc_bid_micros': 1000000},
            {'text': 'another test keyword', 'match_type': 'PHRASE', 'cpc_bid_micros': 1200000}
        ]
        
        result = self.managers['keyword_manager'].add_keywords(
            self.test_resources['ad_group_resource_name'], keywords_data
        )
        if not result:
            raise Exception("Failed to add keywords")
        
        self.test_resources['keyword_resource_name'] = result[0]
        print(f"   Added {len(result)} keywords")
    
    def test_keyword_listing(self):
        """Test listing keywords"""
        keywords = self.managers['keyword_manager'].list_keywords()
        if not isinstance(keywords, list):
            raise Exception("Keyword listing returned non-list")
        print(f"   Found {len(keywords)} keywords")
    
    def test_keyword_status_update(self):
        """Test updating keyword status"""
        if not self.test_resources['keyword_resource_name']:
            raise Exception("No test keyword available")
        
        result = self.managers['keyword_manager'].update_keyword_status(
            self.test_resources['keyword_resource_name'], "ENABLED"
        )
        if not result:
            raise Exception("Failed to update keyword status")
        print("   Updated keyword status to ENABLED")
    
    def test_keyword_bid_update(self):
        """Test updating keyword bid"""
        if not self.test_resources['keyword_resource_name']:
            raise Exception("No test keyword available")
        
        result = self.managers['keyword_manager'].update_keyword_bid(
            self.test_resources['keyword_resource_name'], 1500000  # $1.50
        )
        if not result:
            raise Exception("Failed to update keyword bid")
        print("   Updated keyword bid to $1.50")
    
    def test_negative_keywords(self):
        """Test adding negative keywords"""
        if not self.test_resources['campaign_resource_name']:
            raise Exception("No test campaign available")
        
        negative_keywords = [
            {'text': 'negative keyword', 'match_type': 'BROAD'},
            {'text': 'another negative', 'match_type': 'EXACT'}
        ]
        
        result = self.managers['keyword_manager'].add_negative_keywords_to_campaign(
            self.test_resources['campaign_resource_name'], negative_keywords
        )
        if not result:
            raise Exception("Failed to add negative keywords")
        print(f"   Added {len(result)} negative keywords")
    
    def test_callout_extension(self):
        """Test creating callout extension"""
        extension_resource_name = self.managers['extensions_manager'].create_callout_extension(
            "Test Callout"
        )
        if not extension_resource_name:
            raise Exception("Failed to create callout extension")
        
        self.test_resources['extension_resource_name'] = extension_resource_name
        print(f"   Created callout extension: {extension_resource_name}")
    
    def test_extension_listing(self):
        """Test listing extensions"""
        extensions = self.managers['extensions_manager'].list_extensions()
        if not isinstance(extensions, list):
            raise Exception("Extension listing returned non-list")
        print(f"   Found {len(extensions)} extensions")
    
    def test_conversion_action_creation(self):
        """Test creating conversion action"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversion_name = f"Test_Conversion_{timestamp}"
        
        conversion_resource_name = self.managers['conversion_manager'].create_conversion_action(
            conversion_name, "DEFAULT"
        )
        if not conversion_resource_name:
            raise Exception("Failed to create conversion action")
        
        self.test_resources['conversion_action_resource_name'] = conversion_resource_name
        print(f"   Created conversion action: {conversion_resource_name}")
    
    def test_conversion_listing(self):
        """Test listing conversion actions"""
        conversions = self.managers['conversion_manager'].list_conversion_actions()
        if not isinstance(conversions, list):
            raise Exception("Conversion listing returned non-list")
        print(f"   Found {len(conversions)} conversion actions")
    
    def test_bidding_strategy_creation(self):
        """Test creating bidding strategy"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name = f"Test_Strategy_{timestamp}"
        
        strategy_resource_name = self.managers['bidding_manager'].create_target_cpa_bidding_strategy(
            strategy_name, 10000000  # $10 target CPA
        )
        if not strategy_resource_name:
            raise Exception("Failed to create bidding strategy")
        
        self.test_resources['bidding_strategy_resource_name'] = strategy_resource_name
        print(f"   Created bidding strategy: {strategy_resource_name}")
    
    def test_bidding_strategy_listing(self):
        """Test listing bidding strategies"""
        strategies = self.managers['bidding_manager'].list_bidding_strategies()
        if not isinstance(strategies, list):
            raise Exception("Bidding strategy listing returned non-list")
        print(f"   Found {len(strategies)} bidding strategies")
    
    def test_customer_metrics(self):
        """Test customer-level metrics"""
        metrics = self.managers['reporting_manager'].get_customer_metrics("LAST_7_DAYS")
        if not isinstance(metrics, list):
            raise Exception("Customer metrics returned non-list")
        print(f"   Retrieved customer metrics: {len(metrics)} records")
    
    def test_campaign_metrics(self):
        """Test campaign-level metrics"""
        metrics = self.managers['reporting_manager'].get_campaign_metrics("LAST_7_DAYS")
        if not isinstance(metrics, list):
            raise Exception("Campaign metrics returned non-list")
        print(f"   Retrieved campaign metrics: {len(metrics)} records")
    
    def test_ad_group_ad_metrics(self):
        """Test ad group ad metrics"""
        metrics = self.managers['reporting_manager'].get_ad_group_ad_metrics("LAST_7_DAYS")
        if not isinstance(metrics, list):
            raise Exception("Ad group ad metrics returned non-list")
        print(f"   Retrieved ad group ad metrics: {len(metrics)} records")
    
    def test_keyword_performance(self):
        """Test keyword performance metrics"""
        metrics = self.managers['keyword_manager'].get_keyword_performance("LAST_7_DAYS")
        if not isinstance(metrics, list):
            raise Exception("Keyword performance returned non-list")
        print(f"   Retrieved keyword performance: {len(metrics)} records")
    
    def test_search_term_metrics(self):
        """Test search term view metrics"""
        metrics = self.managers['reporting_manager'].get_search_term_view_metrics("LAST_7_DAYS")
        if not isinstance(metrics, list):
            raise Exception("Search term metrics returned non-list")
        print(f"   Retrieved search term metrics: {len(metrics)} records")
    
    def cleanup_test_resources(self):
        """Clean up test resources"""
        print("\nCleaning up test resources...")
        
        # Remove test keyword
        if self.test_resources['keyword_resource_name']:
            try:
                self.managers['keyword_manager'].remove_keyword(self.test_resources['keyword_resource_name'])
                print("   Removed test keyword")
            except:
                print("   Failed to remove test keyword")
        
        # Remove test ad
        if self.test_resources['ad_resource_name']:
            try:
                self.managers['ad_group_manager'].remove_ad(self.test_resources['ad_resource_name'])
                print("   Removed test ad")
            except:
                print("   Failed to remove test ad")
        
        # Remove test ad group
        if self.test_resources['ad_group_resource_name']:
            try:
                self.managers['ad_group_manager'].remove_ad_group(self.test_resources['ad_group_resource_name'])
                print("   Removed test ad group")
            except:
                print("   Failed to remove test ad group")
        
        # Remove test campaign
        if self.test_resources['campaign_resource_name']:
            try:
                self.managers['campaign_manager'].remove_campaign(self.test_resources['campaign_resource_name'])
                print("   Removed test campaign")
            except:
                print("   Failed to remove test campaign")
        
        # Remove test extension
        if self.test_resources['extension_resource_name']:
            try:
                self.managers['extensions_manager'].remove_extension(self.test_resources['extension_resource_name'])
                print("   Removed test extension")
            except:
                print("   Failed to remove test extension")
        
        # Remove test bidding strategy
        if self.test_resources['bidding_strategy_resource_name']:
            try:
                self.managers['bidding_manager'].remove_bidding_strategy(self.test_resources['bidding_strategy_resource_name'])
                print("   Removed test bidding strategy")
            except:
                print("   Failed to remove test bidding strategy")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting comprehensive Google Ads API testing...")
        print("=" * 60)
        
        # Test sequence
        test_sequence = [
            (self.test_authentication, "Authentication & Client Setup"),
            (self.test_campaign_listing, "Campaign Listing"),
            (self.test_campaign_creation, "Campaign Creation"),
            (self.test_campaign_geo_targeting, "Campaign Geo Targeting"),
            (self.test_campaign_language_targeting, "Campaign Language Targeting"),
            (self.test_campaign_status_update, "Campaign Status Update"),
            (self.test_campaign_details, "Campaign Details Retrieval"),
            (self.test_campaign_name_update, "Campaign Name Update"),
            (self.test_campaign_budget_update, "Campaign Budget Update"),
            (self.test_campaign_network_settings, "Campaign Network Settings"),
            (self.test_ad_group_creation, "Ad Group Creation"),
            (self.test_ad_group_listing, "Ad Group Listing"),
            (self.test_ad_group_status_update, "Ad Group Status Update"),
            (self.test_text_ad_creation, "Text Ad Creation"),
            (self.test_ad_listing, "Ad Listing"),
            (self.test_ad_status_update, "Ad Status Update"),
            (self.test_keyword_addition, "Keyword Addition"),
            (self.test_keyword_listing, "Keyword Listing"),
            (self.test_keyword_status_update, "Keyword Status Update"),
            (self.test_keyword_bid_update, "Keyword Bid Update"),
            (self.test_negative_keywords, "Negative Keywords"),
            (self.test_callout_extension, "Callout Extension Creation"),
            (self.test_extension_listing, "Extension Listing"),
            (self.test_conversion_action_creation, "Conversion Action Creation"),
            (self.test_conversion_listing, "Conversion Action Listing"),
            (self.test_bidding_strategy_creation, "Bidding Strategy Creation"),
            (self.test_bidding_strategy_listing, "Bidding Strategy Listing"),
            (self.test_customer_metrics, "Customer Metrics"),
            (self.test_campaign_metrics, "Campaign Metrics"),
            (self.test_ad_group_ad_metrics, "Ad Group Ad Metrics"),
            (self.test_keyword_performance, "Keyword Performance"),
            (self.test_search_term_metrics, "Search Term Metrics"),
        ]
        
        # Run all tests
        for test_func, test_name in test_sequence:
            self.run_test(test_func, test_name)
        
        # Clean up
        self.cleanup_test_resources()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.results if r.passed])
        failed = len([r for r in self.results if not r.passed])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  FAIL - {result.test_name}: {result.error}")
        
        return failed == 0

if __name__ == "__main__":
    tester = GoogleAdsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)