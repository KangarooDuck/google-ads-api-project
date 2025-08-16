#!/usr/bin/env python3
"""
RMF (Required Minimum Functionality) Compliance Test Suite
Tests all 30 features required by Google Ads API for full-service tools.
Reference: https://developers.google.com/google-ads/api/docs/rmf
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Import SDK
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mai_ads_toolkit import GoogleAdsSDK, GoogleAdsSDKError
from mai_ads_toolkit.core.config import GoogleAdsCredentials

class RMFComplianceTest:
    """Comprehensive test suite for RMF compliance"""
    
    def __init__(self):
        self.sdk = None
        self.test_results = {}
        self.test_data = {
            'campaign_id': None,
            'budget_id': None,
            'ad_group_id': None,
            'ad_id': None,
            'keyword_id': None,
            'conversion_action_id': None,
            'bidding_strategy_id': None
        }
        
    def setup_sdk(self) -> bool:
        """Initialize SDK connection"""
        try:
            # Try to load credentials from environment or config
            from config import Config
            Config.validate_config()
            
            credentials = GoogleAdsCredentials(
                developer_token=Config.GOOGLE_ADS_DEVELOPER_TOKEN,
                client_id=Config.GOOGLE_ADS_CLIENT_ID,
                client_secret=Config.GOOGLE_ADS_CLIENT_SECRET,
                refresh_token=Config.GOOGLE_ADS_REFRESH_TOKEN,
                customer_id=Config.GOOGLE_ADS_CUSTOMER_ID,
                login_customer_id=Config.GOOGLE_ADS_LOGIN_CUSTOMER_ID
            )
            
            self.sdk = GoogleAdsSDK(credentials=credentials)
            print("[OK] SDK initialized successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize SDK: {e}")
            return False
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run individual test with error handling"""
        print(f"\n[TEST] Testing: {test_name}")
        try:
            result = test_func(*args, **kwargs)
            if result:
                print(f"[PASS] PASS: {test_name}")
                self.test_results[test_name] = {"status": "PASS", "error": None}
                return True
            else:
                print(f"[FAIL] FAIL: {test_name}")
                self.test_results[test_name] = {"status": "FAIL", "error": "Test returned False"}
                return False
        except Exception as e:
            print(f"[ERROR] ERROR in {test_name}: {str(e)}")
            self.test_results[test_name] = {"status": "ERROR", "error": str(e)}
            traceback.print_exc()
            return False
    
    # ==========================================
    # CREATION FUNCTIONALITY TESTS (Tests 1-15)
    # ==========================================
    
    def test_1_create_campaign(self) -> bool:
        """Test 1: Create campaign"""
        try:
            # First create a budget
            budget_name = f"RMF_Test_Budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            budget_id = self.sdk.campaigns.create_budget(
                budget_name=budget_name,
                amount_micros=1000000  # $1.00
            )
            
            if not budget_id:
                return False
                
            self.test_data['budget_id'] = budget_id
            
            # Now create campaign
            campaign_name = f"RMF_Test_Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            campaign_id = self.sdk.campaigns.create_campaign(
                campaign_name=campaign_name,
                budget_resource_name=budget_id,  # budget_id is already a full resource name
                campaign_type="SEARCH",
                status="PAUSED"
            )
            
            if campaign_id:
                self.test_data['campaign_id'] = campaign_id
                return True
            return False
            
        except Exception as e:
            print(f"Campaign creation error: {e}")
            return False
    
    def test_2_enable_geo_targeting(self) -> bool:
        """Test 2: Enable geo targeting"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for geo targeting test")
            return False
            
        try:
            # Add geo targeting (United States = 2840)
            result = self.sdk.campaigns.add_geo_targeting(
                campaign_id=self.test_data['campaign_id'],
                location_ids=[2840]  # United States
            )
            return result is not None
        except Exception as e:
            print(f"Geo targeting error: {e}")
            return False
    
    def test_3_enable_language_targeting(self) -> bool:
        """Test 3: Enable language targeting"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for language targeting test")
            return False
            
        try:
            # Add language targeting (English = 1000)
            result = self.sdk.campaigns.add_language_targeting(
                campaign_id=self.test_data['campaign_id'],
                language_ids=[1000]  # English
            )
            return result is not None
        except Exception as e:
            print(f"Language targeting error: {e}")
            return False
    
    def test_4_create_conversion_and_snippet(self) -> bool:
        """Test 4: Create website/call conversion and generate code snippet"""
        try:
            # Create website conversion action
            conversion_name = f"RMF_Test_Conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            conversion_id = self.sdk.conversions.create_conversion_action(
                name=conversion_name,
                category="PURCHASE",
                type_="WEBSITE",
                value_settings_default_value=10.0,
                counting_type="ONE_PER_CLICK"
            )
            
            if conversion_id:
                self.test_data['conversion_action_id'] = conversion_id
                
                # Generate tracking code snippet
                snippet = self.sdk.conversions.generate_tracking_snippet(conversion_id)
                return snippet is not None and len(snippet) > 0
            
            return False
        except Exception as e:
            print(f"Conversion creation error: {e}")
            return False
    
    def test_5_callout_extensions(self) -> bool:
        """Test 5: Callout extensions"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for callout extensions test")
            return False
            
        try:
            result = self.sdk.extensions.create_callout_extension(
                campaign_id=self.test_data['campaign_id'],
                callout_text="Free Shipping"
            )
            return result is not None
        except Exception as e:
            print(f"Callout extension error: {e}")
            return False
    
    def test_6_target_cpa_portfolio(self) -> bool:
        """Test 6: Set bidding - Target CPA (Portfolio)"""
        try:
            strategy_name = f"RMF_Test_Portfolio_CPA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            strategy_id = self.sdk.bidding.create_portfolio_bidding_strategy(
                name=strategy_name,
                type_="TARGET_CPA",
                target_cpa_micros=5000000  # $5.00
            )
            
            if strategy_id:
                self.test_data['bidding_strategy_id'] = strategy_id
                return True
            return False
        except Exception as e:
            print(f"Portfolio Target CPA error: {e}")
            return False
    
    def test_7_target_cpa_standard(self) -> bool:
        """Test 7: Set bidding - Target CPA (Standard)"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for standard Target CPA test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="TARGET_CPA",
                target_cpa_micros=3000000  # $3.00
            )
            return result
        except Exception as e:
            print(f"Standard Target CPA error: {e}")
            return False
    
    def test_8_target_roas_portfolio(self) -> bool:
        """Test 8: Set bidding - Target ROAS (Portfolio)"""
        try:
            strategy_name = f"RMF_Test_Portfolio_ROAS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            strategy_id = self.sdk.bidding.create_portfolio_bidding_strategy(
                name=strategy_name,
                type_="TARGET_ROAS",
                target_roas=3.0  # 300%
            )
            return strategy_id is not None
        except Exception as e:
            print(f"Portfolio Target ROAS error: {e}")
            return False
    
    def test_9_target_roas_standard(self) -> bool:
        """Test 9: Set bidding - Target ROAS (Standard)"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for standard Target ROAS test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="TARGET_ROAS",
                target_roas=2.5  # 250%
            )
            return result
        except Exception as e:
            print(f"Standard Target ROAS error: {e}")
            return False
    
    def test_10_maximize_conversions(self) -> bool:
        """Test 10: Set bidding - Maximize Conversions"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for Maximize Conversions test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="MAXIMIZE_CONVERSIONS",
                target_spend_micros=50000000  # $50.00 daily target
            )
            return result
        except Exception as e:
            print(f"Maximize Conversions error: {e}")
            return False
    
    def test_11_set_budget(self) -> bool:
        """Test 11: Set budget"""
        try:
            # This was already tested in test_1, but let's create another budget
            budget_name = f"RMF_Test_Budget_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            budget_id = self.sdk.campaigns.create_budget(
                budget_name=budget_name,
                amount_micros=2000000  # $2.00
            )
            return budget_id is not None
        except Exception as e:
            print(f"Budget creation error: {e}")
            return False
    
    def test_12_create_ad_group(self) -> bool:
        """Test 12: Create ad group"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for ad group test")
            return False
            
        try:
            ad_group_name = f"RMF_Test_AdGroup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ad_group_id = self.sdk.ad_groups.create_ad_group(
                campaign_id=self.test_data['campaign_id'],
                ad_group_name=ad_group_name,
                cpc_bid_micros=1000000  # $1.00
            )
            
            if ad_group_id:
                self.test_data['ad_group_id'] = ad_group_id
                return True
            return False
        except Exception as e:
            print(f"Ad group creation error: {e}")
            return False
    
    def test_13_add_keyword(self) -> bool:
        """Test 13: Add keyword"""
        if not self.test_data['ad_group_id']:
            print("[ERROR] No ad group ID available for keyword test")
            return False
            
        try:
            keyword_id = self.sdk.keywords.add_keyword(
                ad_group_id=self.test_data['ad_group_id'],
                keyword_text="test keyword",
                match_type="BROAD"
            )
            
            if keyword_id:
                self.test_data['keyword_id'] = keyword_id
                return True
            return False
        except Exception as e:
            print(f"Keyword addition error: {e}")
            return False
    
    def test_14_add_campaign_negative_keywords(self) -> bool:
        """Test 14: Add campaign negative keywords"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for negative keywords test")
            return False
            
        try:
            result = self.sdk.keywords.add_negative_keywords(
                campaign_id=self.test_data['campaign_id'],
                negative_keywords=["free", "cheap", "discount"],
                match_type="BROAD"
            )
            return result
        except Exception as e:
            print(f"Negative keywords error: {e}")
            return False
    
    def test_15_set_keyword_match_type(self) -> bool:
        """Test 15: Set keyword match type"""
        if not self.test_data['keyword_id']:
            print("[ERROR] No keyword ID available for match type test")
            return False
            
        try:
            result = self.sdk.keywords.update_keyword_match_type(
                keyword_id=self.test_data['keyword_id'],
                match_type="EXACT"
            )
            return result
        except Exception as e:
            print(f"Keyword match type error: {e}")
            return False
    
    # ==========================================
    # MANAGEMENT FUNCTIONALITY TESTS (Tests 16-24)
    # ==========================================
    
    def test_16_edit_campaign_settings(self) -> bool:
        """Test 16: Edit campaign settings"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for campaign edit test")
            return False
            
        try:
            result = self.sdk.campaigns.update_campaign(
                campaign_id=self.test_data['campaign_id'],
                name=f"Updated_RMF_Campaign_{datetime.now().strftime('%H%M%S')}",
                status="ENABLED"
            )
            return result
        except Exception as e:
            print(f"Campaign edit error: {e}")
            return False
    
    def test_17_edit_bidding_target_cpa_portfolio(self) -> bool:
        """Test 17: Edit bidding - Target CPA (Portfolio)"""
        if not self.test_data['bidding_strategy_id']:
            print("[ERROR] No bidding strategy ID available for portfolio CPA edit test")
            return False
            
        try:
            result = self.sdk.bidding.update_portfolio_bidding_strategy(
                strategy_id=self.test_data['bidding_strategy_id'],
                target_cpa_micros=6000000  # $6.00
            )
            return result
        except Exception as e:
            print(f"Portfolio CPA edit error: {e}")
            return False
    
    def test_18_edit_bidding_target_cpa_standard(self) -> bool:
        """Test 18: Edit bidding - Target CPA (Standard)"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for standard CPA edit test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="TARGET_CPA",
                target_cpa_micros=4000000  # $4.00
            )
            return result
        except Exception as e:
            print(f"Standard CPA edit error: {e}")
            return False
    
    def test_19_edit_bidding_target_roas_portfolio(self) -> bool:
        """Test 19: Edit bidding - Target ROAS (Portfolio)"""
        try:
            # Create a new portfolio ROAS strategy to edit
            strategy_name = f"RMF_Edit_Portfolio_ROAS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            strategy_id = self.sdk.bidding.create_portfolio_bidding_strategy(
                name=strategy_name,
                type_="TARGET_ROAS",
                target_roas=2.0
            )
            
            if strategy_id:
                result = self.sdk.bidding.update_portfolio_bidding_strategy(
                    strategy_id=strategy_id,
                    target_roas=2.8  # Update to 280%
                )
                return result
            return False
        except Exception as e:
            print(f"Portfolio ROAS edit error: {e}")
            return False
    
    def test_20_edit_bidding_target_roas_standard(self) -> bool:
        """Test 20: Edit bidding - Target ROAS (Standard)"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for standard ROAS edit test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="TARGET_ROAS",
                target_roas=3.2  # 320%
            )
            return result
        except Exception as e:
            print(f"Standard ROAS edit error: {e}")
            return False
    
    def test_21_edit_bidding_maximize_conversions(self) -> bool:
        """Test 21: Edit bidding - Maximize Conversions"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for Maximize Conversions edit test")
            return False
            
        try:
            result = self.sdk.bidding.set_campaign_bidding_strategy(
                campaign_id=self.test_data['campaign_id'],
                bidding_strategy_type="MAXIMIZE_CONVERSIONS",
                target_spend_micros=75000000  # $75.00 daily target
            )
            return result
        except Exception as e:
            print(f"Maximize Conversions edit error: {e}")
            return False
    
    def test_22_pause_enable_remove_campaign(self) -> bool:
        """Test 22: Pause/enable/remove campaign"""
        if not self.test_data['campaign_id']:
            print("[ERROR] No campaign ID available for campaign operations test")
            return False
            
        try:
            # Pause campaign
            pause_result = self.sdk.campaigns.update_campaign_status(
                campaign_id=self.test_data['campaign_id'],
                status="PAUSED"
            )
            
            # Enable campaign
            enable_result = self.sdk.campaigns.update_campaign_status(
                campaign_id=self.test_data['campaign_id'],
                status="ENABLED"
            )
            
            # Remove (set to REMOVED status)
            remove_result = self.sdk.campaigns.update_campaign_status(
                campaign_id=self.test_data['campaign_id'],
                status="REMOVED"
            )
            
            return pause_result and enable_result and remove_result
        except Exception as e:
            print(f"Campaign operations error: {e}")
            return False
    
    def test_23_pause_enable_remove_ad(self) -> bool:
        """Test 23: Pause/enable/remove ad"""
        if not self.test_data['ad_group_id']:
            print("[ERROR] No ad group ID available for ad operations test")
            return False
            
        try:
            # First create an ad
            ad_id = self.sdk.ad_groups.create_text_ad(
                ad_group_id=self.test_data['ad_group_id'],
                headline1="Test Headline 1",
                headline2="Test Headline 2",
                description="Test ad description",
                final_url="https://example.com"
            )
            
            if ad_id:
                self.test_data['ad_id'] = ad_id
                
                # Pause ad
                pause_result = self.sdk.ad_groups.update_ad_status(
                    ad_id=ad_id,
                    status="PAUSED"
                )
                
                # Enable ad
                enable_result = self.sdk.ad_groups.update_ad_status(
                    ad_id=ad_id,
                    status="ENABLED"
                )
                
                # Remove ad
                remove_result = self.sdk.ad_groups.update_ad_status(
                    ad_id=ad_id,
                    status="REMOVED"
                )
                
                return pause_result and enable_result and remove_result
            
            return False
        except Exception as e:
            print(f"Ad operations error: {e}")
            return False
    
    def test_24_pause_enable_remove_keyword(self) -> bool:
        """Test 24: Pause/enable/remove keyword"""
        if not self.test_data['keyword_id']:
            print("[ERROR] No keyword ID available for keyword operations test")
            return False
            
        try:
            # Pause keyword
            pause_result = self.sdk.keywords.update_keyword_status(
                keyword_id=self.test_data['keyword_id'],
                status="PAUSED"
            )
            
            # Enable keyword
            enable_result = self.sdk.keywords.update_keyword_status(
                keyword_id=self.test_data['keyword_id'],
                status="ENABLED"
            )
            
            # Remove keyword
            remove_result = self.sdk.keywords.update_keyword_status(
                keyword_id=self.test_data['keyword_id'],
                status="REMOVED"
            )
            
            return pause_result and enable_result and remove_result
        except Exception as e:
            print(f"Keyword operations error: {e}")
            return False
    
    # ==========================================
    # REPORTING FUNCTIONALITY TESTS (Tests 25-30)
    # ==========================================
    
    def test_25_customer_level_reporting(self) -> bool:
        """Test 25: Customer-level reporting (clicks, cost, impressions, conversions)"""
        try:
            report_data = self.sdk.reporting.get_customer_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Customer reporting error: {e}")
            return False
    
    def test_26_campaign_level_reporting(self) -> bool:
        """Test 26: Campaign-level reporting (clicks, cost, impressions, conversions)"""
        try:
            report_data = self.sdk.reporting.get_campaign_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Campaign reporting error: {e}")
            return False
    
    def test_27_ad_group_ad_reporting(self) -> bool:
        """Test 27: Ad Group Ad reporting"""
        try:
            report_data = self.sdk.reporting.get_ad_group_ad_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Ad Group Ad reporting error: {e}")
            return False
    
    def test_28_keyword_view_reporting(self) -> bool:
        """Test 28: Keyword View reporting"""
        try:
            report_data = self.sdk.reporting.get_keyword_view_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Keyword View reporting error: {e}")
            return False
    
    def test_29_search_term_view_reporting(self) -> bool:
        """Test 29: Search Term View reporting"""
        try:
            report_data = self.sdk.reporting.get_search_term_view_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Search Term View reporting error: {e}")
            return False
    
    def test_30_bidding_strategy_reporting(self) -> bool:
        """Test 30: Bidding Strategy reporting"""
        try:
            report_data = self.sdk.reporting.get_bidding_strategy_report(
                date_range="LAST_30_DAYS",
                metrics=["clicks", "cost_micros", "impressions", "conversions"]
            )
            
            return report_data is not None and len(report_data) >= 0
        except Exception as e:
            print(f"Bidding Strategy reporting error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all RMF compliance tests"""
        print("Starting RMF Compliance Test Suite")
        print("=" * 60)
        
        if not self.setup_sdk():
            return {"error": "Failed to initialize SDK"}
        
        # Creation Functionality Tests (1-15)
        print("\nCREATION FUNCTIONALITY TESTS")
        print("-" * 40)
        
        self.run_test("Test 1: Create campaign", self.test_1_create_campaign)
        self.run_test("Test 2: Enable geo targeting", self.test_2_enable_geo_targeting)
        self.run_test("Test 3: Enable language targeting", self.test_3_enable_language_targeting)
        self.run_test("Test 4: Create website/call conversion and generate code snippet", self.test_4_create_conversion_and_snippet)
        self.run_test("Test 5: Callout extensions", self.test_5_callout_extensions)
        self.run_test("Test 6: Set bidding - Target CPA (Portfolio)", self.test_6_target_cpa_portfolio)
        self.run_test("Test 7: Set bidding - Target CPA (Standard)", self.test_7_target_cpa_standard)
        self.run_test("Test 8: Set bidding - Target ROAS (Portfolio)", self.test_8_target_roas_portfolio)
        self.run_test("Test 9: Set bidding - Target ROAS (Standard)", self.test_9_target_roas_standard)
        self.run_test("Test 10: Set bidding - Maximize Conversions", self.test_10_maximize_conversions)
        self.run_test("Test 11: Set budget", self.test_11_set_budget)
        self.run_test("Test 12: Create ad group", self.test_12_create_ad_group)
        self.run_test("Test 13: Add keyword", self.test_13_add_keyword)
        self.run_test("Test 14: Add campaign negative keywords", self.test_14_add_campaign_negative_keywords)
        self.run_test("Test 15: Set keyword match type", self.test_15_set_keyword_match_type)
        
        # Management Functionality Tests (16-24)
        print("\nMANAGEMENT FUNCTIONALITY TESTS")
        print("-" * 40)
        
        self.run_test("Test 16: Edit campaign settings", self.test_16_edit_campaign_settings)
        self.run_test("Test 17: Edit bidding - Target CPA (Portfolio)", self.test_17_edit_bidding_target_cpa_portfolio)
        self.run_test("Test 18: Edit bidding - Target CPA (Standard)", self.test_18_edit_bidding_target_cpa_standard)
        self.run_test("Test 19: Edit bidding - Target ROAS (Portfolio)", self.test_19_edit_bidding_target_roas_portfolio)
        self.run_test("Test 20: Edit bidding - Target ROAS (Standard)", self.test_20_edit_bidding_target_roas_standard)
        self.run_test("Test 21: Edit bidding - Maximize Conversions", self.test_21_edit_bidding_maximize_conversions)
        self.run_test("Test 22: Pause/enable/remove campaign", self.test_22_pause_enable_remove_campaign)
        self.run_test("Test 23: Pause/enable/remove ad", self.test_23_pause_enable_remove_ad)
        self.run_test("Test 24: Pause/enable/remove keyword", self.test_24_pause_enable_remove_keyword)
        
        # Reporting Functionality Tests (25-30)
        print("\nREPORTING FUNCTIONALITY TESTS")
        print("-" * 40)
        
        self.run_test("Test 25: Customer-level reporting", self.test_25_customer_level_reporting)
        self.run_test("Test 26: Campaign-level reporting", self.test_26_campaign_level_reporting)
        self.run_test("Test 27: Ad Group Ad reporting", self.test_27_ad_group_ad_reporting)
        self.run_test("Test 28: Keyword View reporting", self.test_28_keyword_view_reporting)
        self.run_test("Test 29: Search Term View reporting", self.test_29_search_term_view_reporting)
        self.run_test("Test 30: Bidding Strategy reporting", self.test_30_bidding_strategy_reporting)
        
        # Summary
        print("\n" + "=" * 60)
        print("RMF COMPLIANCE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results.values() if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results.values() if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"[PASS] Passed: {passed_tests}")
        print(f"[FAIL] Failed: {failed_tests}")
        print(f"[ERROR] Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print("\nFAILED/ERROR TESTS:")
            for test_name, result in self.test_results.items():
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  {result['status']}: {test_name}")
                    if result["error"]:
                        print(f"    Error: {result['error']}")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results,
            "test_data": self.test_data
        }

def main():
    """Main execution function"""
    test_suite = RMFComplianceTest()
    results = test_suite.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"rmf_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_file}")
    
    # Return exit code based on success
    if "error" in results:
        return 1  # Setup error
    elif results["failed"] > 0 or results["errors"] > 0:
        return 1  # Test failures
    else:
        return 0  # All tests passed

if __name__ == "__main__":
    sys.exit(main())