import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from google_ads_sdk import GoogleAdsSDK, GoogleAdsCredentials
from audit_logger import audit_logger

# Page configuration
st.set_page_config(
    page_title="Google Ads API Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'ads_sdk' not in st.session_state:
    st.session_state.ads_sdk = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def initialize_managers():
    if st.session_state.ads_sdk and st.session_state.authenticated:
        return {
            'campaign_manager': st.session_state.ads_sdk.campaigns,
            'ad_group_manager': st.session_state.ads_sdk.ad_groups,
            'keyword_manager': st.session_state.ads_sdk.keywords,
            'conversion_manager': st.session_state.ads_sdk.conversions,
            'extensions_manager': st.session_state.ads_sdk.extensions,
            'bidding_manager': st.session_state.ads_sdk.bidding,
            'reporting_manager': st.session_state.ads_sdk.reporting
        }
    return None

def authenticate():
    st.header("🔐 Google Ads API Authentication")
    
    with st.form("auth_form"):
        st.write("Please ensure your .env file is configured with the following variables:")
        st.code("""
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_client_account_id_here
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_manager_account_id_here
        """)
        
        submitted = st.form_submit_button("Connect to Google Ads API")
        
        if submitted:
            try:
                credentials = GoogleAdsCredentials()
                ads_sdk = GoogleAdsSDK(credentials)
                st.session_state.ads_sdk = ads_sdk
                st.session_state.customer_id = ads_sdk.customer_id
                st.session_state.authenticated = True
                st.success("Successfully connected to Google Ads API!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to connect to Google Ads API: {str(e)}")

def campaign_management_page():
    st.header("📊 Campaign Management")
    managers = initialize_managers()
    if not managers:
        return
    
    campaign_manager = managers['campaign_manager']
    
    tab1, tab2, tab3 = st.tabs(["Create Campaign", "Manage Campaigns", "Campaign Settings"])
    
    with tab1:
        st.subheader("Create New Campaign")
        with st.form("create_campaign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                campaign_name = st.text_input("Campaign Name", placeholder="Enter campaign name")
                budget_name = st.text_input("Budget Name", placeholder="Enter budget name")
                daily_budget = st.number_input("Daily Budget ($)", min_value=0.01, value=10.0, step=0.01)
                campaign_type = st.selectbox("Campaign Type", ["SEARCH", "DISPLAY", "SHOPPING", "VIDEO"])
            
            with col2:
                bidding_strategy = st.selectbox("Bidding Strategy", 
                    ["MANUAL_CPC", "TARGET_CPA", "TARGET_ROAS", "MAXIMIZE_CONVERSIONS"])
                
                # Geo targeting
                st.subheader("Geo Targeting")
                geo_locations = st.text_area("Location IDs (comma-separated)", 
                    placeholder="e.g., 2840 (United States), 2124 (Canada)")
                
                # Language targeting
                st.subheader("Language Targeting")
                languages = st.text_area("Language Codes (comma-separated)", 
                    placeholder="e.g., 1000 (English), 1003 (Spanish)")
            
            submitted = st.form_submit_button("Create Campaign")
            
            if submitted and campaign_name and budget_name:
                # Create budget
                budget_resource_name = campaign_manager.create_campaign_budget(
                    budget_name, int(daily_budget * 1000000)
                )
                
                if budget_resource_name:
                    # Create campaign
                    campaign_resource_name = campaign_manager.create_campaign(
                        campaign_name, budget_resource_name, campaign_type, 
                        "PAUSED", bidding_strategy
                    )
                    
                    if campaign_resource_name:
                        # Add geo targeting
                        if geo_locations:
                            location_ids = [loc.strip() for loc in geo_locations.split(',')]
                            campaign_manager.add_geo_targeting(campaign_resource_name, location_ids)
                        
                        # Add language targeting
                        if languages:
                            language_codes = [lang.strip() for lang in languages.split(',')]
                            campaign_manager.add_language_targeting(campaign_resource_name, language_codes)
                        
                        st.success(f"Campaign '{campaign_name}' created successfully!")
    
    with tab2:
        st.subheader("Existing Campaigns")
        campaigns = campaign_manager.list_campaigns()
        
        if campaigns:
            df = pd.DataFrame(campaigns)
            st.dataframe(df)
            
            # Campaign actions
            selected_campaign = st.selectbox("Select Campaign", 
                options=[f"{c['name']} (ID: {c['id']})" for c in campaigns])
            
            if selected_campaign:
                campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Enable Campaign"):
                        result = campaign_manager.update_campaign_status(campaign_resource_name, "ENABLED")
                        if result:
                            st.success("Campaign enabled successfully!")
                        st.rerun()
                
                with col2:
                    if st.button("Pause Campaign"):
                        result = campaign_manager.update_campaign_status(campaign_resource_name, "PAUSED")
                        if result:
                            st.success("Campaign paused successfully!")
                        st.rerun()
                
                with col3:
                    if st.button("Remove Campaign"):
                        result = campaign_manager.remove_campaign(campaign_resource_name)
                        if result:
                            st.success("Campaign removed successfully!")
                        st.rerun()
        else:
            st.info("No campaigns found. Create your first campaign above.")
    
    with tab3:
        st.subheader("Campaign Settings")
        campaigns = campaign_manager.list_campaigns()
        
        if campaigns:
            selected_campaign = st.selectbox("Select Campaign to Edit", 
                options=[f"{c['name']} (ID: {c['id']})" for c in campaigns])
            
            if selected_campaign:
                campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                
                # Get campaign details
                campaign_details = campaign_manager.get_campaign_details(campaign_resource_name)
                
                if campaign_details:
                    st.write("**Current Campaign Settings:**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {campaign_details['name']}")
                        st.write(f"**Status:** {campaign_details['status']}")
                        st.write(f"**Type:** {campaign_details['type']}")
                        budget_display = campaign_details['budget_micros'] / 1000000
                        st.write(f"**Budget:** ${budget_display:.2f}" + (" (No budget set)" if budget_display == 0 else ""))
                    
                    with col2:
                        st.write(f"**Start Date:** {campaign_details['start_date']}")
                        st.write(f"**End Date:** {campaign_details['end_date'] if campaign_details['end_date'] else 'No end date'}")
                        st.write(f"**Google Search:** {campaign_details['target_google_search']}")
                        st.write(f"**Search Network:** {campaign_details['target_search_network']}")
                    
                    st.divider()
                    
                    # Edit campaign name
                    with st.expander("📝 Edit Campaign Name"):
                        with st.form("edit_campaign_name"):
                            new_name = st.text_input("New Campaign Name", value=campaign_details['name'])
                            if st.form_submit_button("Update Name"):
                                if new_name and new_name != campaign_details['name']:
                                    result = campaign_manager.update_campaign_name(campaign_resource_name, new_name)
                                    if result:
                                        st.success("Campaign name updated successfully!")
                                        st.rerun()
                    
                    # Edit campaign budget
                    with st.expander("💰 Edit Campaign Budget"):
                        with st.form("edit_campaign_budget"):
                            current_budget = campaign_details['budget_micros'] / 1000000
                            # Handle zero or very small budget values
                            default_budget = max(current_budget, 0.01)
                            
                            if current_budget == 0:
                                st.info("⚠️ This campaign currently has no budget set (${:.2f}). Please set a budget to enable the campaign.".format(current_budget))
                            else:
                                st.info("Current budget: ${:.2f}".format(current_budget))
                            
                            new_budget = st.number_input("New Daily Budget ($)", 
                                min_value=0.01, value=default_budget, step=0.01)
                            if st.form_submit_button("Update Budget"):
                                # Compare against the actual current budget, not the default value
                                if abs(new_budget - current_budget) > 0.001:  # Small tolerance for floating point comparison
                                    result = campaign_manager.update_campaign_budget(
                                        campaign_resource_name, int(new_budget * 1000000)
                                    )
                                    if result:
                                        st.success("Campaign budget updated successfully!")
                                        st.rerun()
                    
                    # Edit network settings
                    with st.expander("🌐 Edit Network Settings"):
                        with st.form("edit_network_settings"):
                            st.write("Select which networks to target:")
                            
                            target_google_search = st.checkbox("Google Search", 
                                value=campaign_details['target_google_search'])
                            target_search_network = st.checkbox("Search Network", 
                                value=campaign_details['target_search_network'])
                            target_content_network = st.checkbox("Display Network", 
                                value=campaign_details['target_content_network'])
                            target_partner_search_network = st.checkbox("Search Partners", 
                                value=campaign_details['target_partner_search_network'])
                            
                            if st.form_submit_button("Update Network Settings"):
                                network_settings = {
                                    'target_google_search': target_google_search,
                                    'target_search_network': target_search_network,
                                    'target_content_network': target_content_network,
                                    'target_partner_search_network': target_partner_search_network
                                }
                                result = campaign_manager.update_campaign_network_settings(
                                    campaign_resource_name, network_settings
                                )
                                if result:
                                    st.success("Network settings updated successfully!")
                                    st.rerun()
                    
                    # Edit bidding strategy
                    with st.expander("🎯 Edit Bidding Strategy"):
                        st.write("**Current Bidding Strategy:** Based on campaign type")
                        
                        bidding_strategy = st.selectbox("Select New Bidding Strategy", [
                            "MANUAL_CPC", 
                            "MAXIMIZE_CLICKS",
                            "TARGET_CPA", 
                            "TARGET_ROAS", 
                            "MAXIMIZE_CONVERSIONS",
                            "MAXIMIZE_CONVERSION_VALUE",
                            "TARGET_CPM",
                            "TARGET_IMPRESSION_SHARE",
                            "MANUAL_CPM",
                            "MANUAL_CPV",
                            "COMMISSION",
                            "PERCENT_CPC"
                        ])
                        
                        if bidding_strategy == "TARGET_CPA":
                            target_cpa = st.number_input("Target CPA ($)", min_value=0.01, value=10.0, step=0.01)
                            if st.button("Apply Target CPA"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "TARGET_CPA", target_cpa_micros=int(target_cpa * 1000000)
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "TARGET_ROAS":
                            target_roas = st.number_input("Target ROAS", min_value=0.01, value=4.0, step=0.01)
                            if st.button("Apply Target ROAS"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "TARGET_ROAS", target_roas=target_roas
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MAXIMIZE_CONVERSIONS":
                            if st.button("Apply Maximize Conversions"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MAXIMIZE_CONVERSIONS"
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MAXIMIZE_CONVERSION_VALUE":
                            target_roas = st.number_input("Target ROAS (Optional)", min_value=0.01, value=4.0, step=0.01)
                            use_target_roas = st.checkbox("Set Target ROAS", value=False)
                            if st.button("Apply Maximize Conversion Value"):
                                bidding_manager = managers['bidding_manager']
                                kwargs = {}
                                if use_target_roas:
                                    kwargs["target_roas"] = target_roas
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MAXIMIZE_CONVERSION_VALUE", **kwargs
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MAXIMIZE_CLICKS":
                            col1, col2 = st.columns(2)
                            with col1:
                                max_cpc = st.number_input("Max CPC ($, Optional)", min_value=0.01, value=5.0, step=0.01)
                                use_max_cpc = st.checkbox("Set Max CPC Limit", value=False)
                            with col2:
                                min_cpc = st.number_input("Min CPC ($, Optional)", min_value=0.01, value=0.10, step=0.01)
                                use_min_cpc = st.checkbox("Set Min CPC Limit", value=False)
                            if st.button("Apply Maximize Clicks"):
                                bidding_manager = managers['bidding_manager']
                                kwargs = {}
                                if use_max_cpc:
                                    kwargs["cpc_bid_ceiling_micros"] = int(max_cpc * 1000000)
                                if use_min_cpc:
                                    kwargs["cpc_bid_floor_micros"] = int(min_cpc * 1000000)
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MAXIMIZE_CLICKS", **kwargs
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "TARGET_CPM":
                            target_cpm = st.number_input("Target CPM ($)", min_value=0.01, value=2.0, step=0.01)
                            st.info("💡 Target CPM works with Display and Video campaigns only")
                            if st.button("Apply Target CPM"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "TARGET_CPM", target_cpm_micros=int(target_cpm * 1000000)
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "TARGET_IMPRESSION_SHARE":
                            col1, col2 = st.columns(2)
                            with col1:
                                location = st.selectbox("Target Location", [
                                    "ANYWHERE_ON_PAGE",
                                    "TOP_OF_PAGE", 
                                    "ABSOLUTE_TOP_OF_PAGE"
                                ])
                                impression_share = st.number_input("Target Impression Share (%)", 
                                    min_value=1, max_value=100, value=50, step=1)
                            with col2:
                                max_cpc = st.number_input("Max CPC ($, Optional)", min_value=0.01, value=5.0, step=0.01)
                                use_max_cpc = st.checkbox("Set Max CPC Limit", value=False, key="tis_max_cpc")
                            st.info("💡 Target Impression Share works with Search campaigns only")
                            if st.button("Apply Target Impression Share"):
                                bidding_manager = managers['bidding_manager']
                                kwargs = {
                                    "location": getattr(bidding_manager.client.enums.TargetImpressionShareLocationEnum, location),
                                    "location_fraction_micros": int(impression_share * 10000)  # Convert % to micros
                                }
                                if use_max_cpc:
                                    kwargs["cpc_bid_ceiling_micros"] = int(max_cpc * 1000000)
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "TARGET_IMPRESSION_SHARE", **kwargs
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MANUAL_CPM":
                            st.info("💡 Manual CPM works with Display campaigns only")
                            if st.button("Apply Manual CPM"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MANUAL_CPM"
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MANUAL_CPV":
                            st.info("💡 Manual CPV works with Video campaigns only")
                            if st.button("Apply Manual CPV"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MANUAL_CPV"
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "COMMISSION":
                            commission_rate = st.number_input("Commission Rate (%)", min_value=0.01, max_value=100.0, value=10.0, step=0.01)
                            st.info("💡 Commission bidding works with Hotel campaigns only")
                            if st.button("Apply Commission"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "COMMISSION", 
                                    commission_rate_micros=int(commission_rate * 10000)  # Convert % to micros
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "PERCENT_CPC":
                            max_cpc = st.number_input("Max CPC ($)", min_value=0.01, value=5.0, step=0.01)
                            st.info("💡 Percent CPC works with Hotel campaigns only")
                            if st.button("Apply Percent CPC"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "PERCENT_CPC", 
                                    cpc_bid_ceiling_micros=int(max_cpc * 1000000)
                                )
                                if result:
                                    st.rerun()
                        
                        elif bidding_strategy == "MANUAL_CPC":
                            enhanced_cpc = st.checkbox("Enhanced CPC", value=False)
                            if enhanced_cpc:
                                st.info("ℹ️ Enhanced CPC requires conversion tracking. If unavailable, the system will automatically fall back to regular Manual CPC.")
                            if st.button("Apply Manual CPC"):
                                bidding_manager = managers['bidding_manager']
                                result = bidding_manager.apply_bidding_strategy_to_campaign(
                                    campaign_resource_name, "MANUAL_CPC", enhanced_cpc_enabled=enhanced_cpc
                                )
                                if result:
                                    st.rerun()
                    
                    # Edit geo targeting
                    with st.expander("🌍 Edit Geographic Targeting"):
                        # Get current targeting
                        current_criteria = campaign_manager.get_campaign_criteria(campaign_resource_name)
                        current_geo_targets = current_criteria['geo_targets']
                        
                        if current_geo_targets:
                            st.write("**Current Geographic Targets:**")
                            for geo in current_geo_targets:
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"• Location ID: {geo['location_id']}")
                                with col2:
                                    if st.button(f"❌", key=f"remove_geo_{geo['location_id']}", 
                                                help="Remove this geo target"):
                                        if campaign_manager.remove_campaign_criteria([geo['resource_name']]):
                                            st.rerun()
                        else:
                            st.info("No geographic targeting currently set")
                        
                        st.write("**Add New Geographic Targets:**")
                        with st.form("edit_geo_targeting"):
                            new_geo_locations = st.text_area(
                                "Location IDs (comma-separated)", 
                                placeholder="e.g., 2840 (United States), 2124 (Canada), 2276 (Germany)",
                                help="Common Location IDs: US=2840, Canada=2124, UK=2826, Germany=2276, France=2250, Japan=2392"
                            )
                            
                            if st.form_submit_button("Add Geographic Targets"):
                                if new_geo_locations:
                                    location_ids = [loc.strip() for loc in new_geo_locations.split(',') if loc.strip()]
                                    if location_ids:
                                        result = campaign_manager.add_geo_targeting(campaign_resource_name, location_ids)
                                        if result:
                                            st.rerun()
                    
                    # Edit language targeting
                    with st.expander("🗣️ Edit Language Targeting"):
                        # Get current language targeting
                        current_language_targets = current_criteria['language_targets']
                        
                        if current_language_targets:
                            st.write("**Current Language Targets:**")
                            for lang in current_language_targets:
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"• Language Code: {lang['language_code']}")
                                with col2:
                                    if st.button(f"❌", key=f"remove_lang_{lang['language_code']}", 
                                                help="Remove this language target"):
                                        if campaign_manager.remove_campaign_criteria([lang['resource_name']]):
                                            st.rerun()
                        else:
                            st.info("No language targeting currently set")
                        
                        st.write("**Add New Language Targets:**")
                        with st.form("edit_language_targeting"):
                            new_languages = st.text_area(
                                "Language Codes (comma-separated)", 
                                placeholder="e.g., 1000 (English), 1003 (Spanish), 1005 (French)",
                                help="Common Language Codes: English=1000, Spanish=1003, French=1005, German=1001, Italian=1004, Japanese=1013, Chinese=1002"
                            )
                            
                            if st.form_submit_button("Add Language Targets"):
                                if new_languages:
                                    language_codes = [lang.strip() for lang in new_languages.split(',') if lang.strip()]
                                    if language_codes:
                                        result = campaign_manager.add_language_targeting(campaign_resource_name, language_codes)
                                        if result:
                                            st.rerun()
                else:
                    st.error("Could not load campaign details")
        else:
            st.info("No campaigns found. Create your first campaign in the 'Create Campaign' tab.")

def ad_group_management_page():
    st.header("📝 Ad Group & Ad Management")
    managers = initialize_managers()
    if not managers:
        return
    
    ad_group_manager = managers['ad_group_manager']
    campaign_manager = managers['campaign_manager']
    
    tab1, tab2, tab3 = st.tabs(["Create Ad Group", "Create Ads", "Manage Ad Groups & Ads"])
    
    with tab1:
        st.subheader("Create New Ad Group")
        campaigns = campaign_manager.list_campaigns()
        
        if campaigns:
            with st.form("create_ad_group_form"):
                selected_campaign = st.selectbox("Select Campaign", 
                    options=[f"{c['name']} (ID: {c['id']})" for c in campaigns])
                
                ad_group_name = st.text_input("Ad Group Name", placeholder="Enter ad group name")
                default_bid = st.number_input("Default CPC Bid ($)", min_value=0.01, value=1.0, step=0.01)
                
                submitted = st.form_submit_button("Create Ad Group")
                
                if submitted and ad_group_name and selected_campaign:
                    campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                    campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                    
                    ad_group_resource_name = ad_group_manager.create_ad_group(
                        ad_group_name, campaign_resource_name, int(default_bid * 1000000)
                    )
                    
                    if ad_group_resource_name:
                        st.success(f"Ad Group '{ad_group_name}' created successfully!")
        else:
            st.warning("No campaigns found. Please create a campaign first.")
    
    with tab2:
        st.subheader("Create Ads")
        ad_groups = ad_group_manager.list_ad_groups()
        
        if ad_groups:
            ad_type = st.selectbox("Ad Type", ["Expanded Text Ad", "Responsive Search Ad"])
            
            if ad_type == "Expanded Text Ad":
                st.info("⚠️ Note: This creates a Responsive Search Ad (Expanded Text Ads are deprecated in Google Ads API v20)")
                with st.form("create_text_ad_form"):
                    selected_ad_group = st.selectbox("Select Ad Group", 
                        options=[f"{ag['name']} (Campaign: {ag['campaign_name']})" for ag in ad_groups])
                    
                    headline1 = st.text_input("Headline 1 *", max_chars=30)
                    headline2 = st.text_input("Headline 2 *", max_chars=30)
                    headline3 = st.text_input("Headline 3 * (Required for RSA)", max_chars=30)
                    description = st.text_area("Description 1 *", max_chars=90)
                    description2 = st.text_area("Description 2 * (Required for RSA)", max_chars=90)
                    final_url = st.text_input("Final URL *", placeholder="https://example.com")
                    
                    submitted = st.form_submit_button("Create Responsive Search Ad")
                    
                    if submitted:
                        # Validate all required fields
                        if not all([headline1, headline2, headline3, description, description2, final_url]):
                            st.error("All fields marked with * are required for Responsive Search Ads.")
                        else:
                            ad_group_id = None
                            for ag in ad_groups:
                                if f"{ag['name']} (Campaign: {ag['campaign_name']})" == selected_ad_group:
                                    ad_group_id = ag['id']
                                    break
                            
                            if ad_group_id:
                                ad_group_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/adGroups/{ad_group_id}"
                                
                                ad_resource_name = ad_group_manager.create_text_ad(
                                    ad_group_resource_name, headline1, headline2, description, 
                                    final_url, headline3, description2
                                )
                                
                                if ad_resource_name:
                                    st.success("Responsive Search Ad created successfully!")
            
            elif ad_type == "Responsive Search Ad":
                with st.form("create_rsa_form"):
                    selected_ad_group = st.selectbox("Select Ad Group", 
                        options=[f"{ag['name']} (Campaign: {ag['campaign_name']})" for ag in ad_groups])
                    
                    st.write("Headlines (minimum 3, maximum 15)")
                    headlines = []
                    for i in range(5):
                        headline = st.text_input(f"Headline {i+1}", max_chars=30, 
                            key=f"headline_{i}")
                        if headline:
                            headlines.append(headline)
                    
                    st.write("Descriptions (minimum 2, maximum 4)")
                    descriptions = []
                    for i in range(4):
                        description = st.text_area(f"Description {i+1}", max_chars=90, 
                            key=f"description_{i}")
                        if description:
                            descriptions.append(description)
                    
                    final_url = st.text_input("Final URL", placeholder="https://example.com")
                    
                    submitted = st.form_submit_button("Create Responsive Search Ad")
                    
                    if submitted and len(headlines) >= 3 and len(descriptions) >= 2 and final_url:
                        ad_group_id = None
                        for ag in ad_groups:
                            if f"{ag['name']} (Campaign: {ag['campaign_name']})" == selected_ad_group:
                                ad_group_id = ag['id']
                                break
                        
                        if ad_group_id:
                            ad_group_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/adGroups/{ad_group_id}"
                            
                            ad_resource_name = ad_group_manager.create_responsive_search_ad(
                                ad_group_resource_name, headlines, descriptions, final_url
                            )
                            
                            if ad_resource_name:
                                st.success("Responsive search ad created successfully!")
        else:
            st.warning("No ad groups found. Please create an ad group first.")
    
    with tab3:
        st.subheader("Manage Ad Groups & Ads")
        
        # Ad Groups management
        st.write("**Ad Groups**")
        ad_groups = ad_group_manager.list_ad_groups()
        if ad_groups:
            df_ad_groups = pd.DataFrame(ad_groups)
            st.dataframe(df_ad_groups)
        
        # Ads management
        st.write("**Ads Management**")
        ads = ad_group_manager.list_ads()
        if ads:
            st.write(f"Found {len(ads)} ads")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "ENABLED", "PAUSED"], key="ad_status_filter")
            with col2:
                # Get unique ad groups for filtering
                unique_ad_groups = list(set([ad.get('ad_group_name', 'Unknown') for ad in ads]))
                ad_group_filter = st.selectbox("Filter by Ad Group", ["All"] + unique_ad_groups, key="ad_ag_filter")
            
            # Apply filters
            filtered_ads = ads
            if status_filter != "All":
                filtered_ads = [ad for ad in filtered_ads if ad.get('status') == status_filter]
            if ad_group_filter != "All":
                filtered_ads = [ad for ad in filtered_ads if ad.get('ad_group_name') == ad_group_filter]
            
            st.write(f"Showing {len(filtered_ads)} ads")
            
            if filtered_ads:
                # Display ads with management controls
                for i, ad in enumerate(filtered_ads):
                    with st.expander(f"Ad {i+1}: {ad.get('headline1', 'No headline')} - {ad.get('status', 'Unknown Status')}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Ad Group:** {ad.get('ad_group_name', 'Unknown')}")
                            st.write(f"**Campaign:** {ad.get('campaign_name', 'Unknown')}")
                            st.write(f"**Status:** {ad.get('status', 'Unknown')}")
                            st.write(f"**Type:** {ad.get('type', 'Unknown')}")
                            if ad.get('headline1'):
                                st.write(f"**Headlines:** {ad.get('headline1', '')}")
                                if ad.get('headline2'):
                                    st.write(f"**Headline 2:** {ad.get('headline2', '')}")
                                if ad.get('headline3'):
                                    st.write(f"**Headline 3:** {ad.get('headline3', '')}")
                            if ad.get('description1'):
                                st.write(f"**Description:** {ad.get('description1', '')}")
                            if ad.get('final_url'):
                                st.write(f"**Final URL:** {ad.get('final_url', '')}")
                        
                        with col2:
                            # Pause/Enable buttons
                            if ad.get('status') == 'ENABLED':
                                if st.button(f"⏸️ Pause", key=f"pause_ad_{i}"):
                                    result = ad_group_manager.update_ad_status(ad['resource_name'], "PAUSED")
                                    if result:
                                        st.success("Ad paused!")
                                        st.rerun()
                            elif ad.get('status') == 'PAUSED':
                                if st.button(f"▶️ Enable", key=f"enable_ad_{i}"):
                                    result = ad_group_manager.update_ad_status(ad['resource_name'], "ENABLED")
                                    if result:
                                        st.success("Ad enabled!")
                                        st.rerun()
                        
                        with col3:
                            # Remove button
                            if st.button(f"🗑️ Remove", key=f"remove_ad_{i}"):
                                result = ad_group_manager.remove_ad(ad['resource_name'])
                                if result:
                                    st.success("Ad removed!")
                                    st.rerun()
                
                # Bulk actions
                st.divider()
                st.write("**Bulk Actions:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("⏸️ Pause All Filtered"):
                        success_count = 0
                        for ad in filtered_ads:
                            if ad.get('status') == 'ENABLED':
                                if ad_group_manager.update_ad_status(ad['resource_name'], "PAUSED"):
                                    success_count += 1
                        st.success(f"Paused {success_count} ads!")
                        st.rerun()
                
                with col2:
                    if st.button("▶️ Enable All Filtered"):
                        success_count = 0
                        for ad in filtered_ads:
                            if ad.get('status') == 'PAUSED':
                                if ad_group_manager.update_ad_status(ad['resource_name'], "ENABLED"):
                                    success_count += 1
                        st.success(f"Enabled {success_count} ads!")
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Remove All Filtered", type="secondary"):
                        success_count = 0
                        for ad in filtered_ads:
                            if ad.get('status') != 'REMOVED':
                                if ad_group_manager.remove_ad(ad['resource_name']):
                                    success_count += 1
                        st.success(f"Removed {success_count} ads!")
                        st.rerun()
        else:
            st.info("No ads found. Create some ads first.")

def keyword_management_page():
    st.header("🔍 Keyword Management")
    managers = initialize_managers()
    if not managers:
        return
    
    keyword_manager = managers['keyword_manager']
    ad_group_manager = managers['ad_group_manager']
    campaign_manager = managers['campaign_manager']
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Keywords", "Manage Keywords", "Negative Keywords", "Keyword Performance"])
    
    with tab1:
        st.subheader("Add Keywords to Ad Group")
        ad_groups = ad_group_manager.list_ad_groups()
        
        if ad_groups:
            with st.form("add_keywords_form"):
                selected_ad_group = st.selectbox("Select Ad Group", 
                    options=[f"{ag['name']} (Campaign: {ag['campaign_name']})" for ag in ad_groups])
                
                keywords_input = st.text_area("Keywords (one per line)", 
                    placeholder="Enter keywords, one per line")
                
                match_type = st.selectbox("Match Type", ["BROAD", "PHRASE", "EXACT"])
                default_bid = st.number_input("Default CPC Bid ($)", min_value=0.01, value=1.0, step=0.01)
                
                submitted = st.form_submit_button("Add Keywords")
                
                if submitted and keywords_input and selected_ad_group:
                    ad_group_id = None
                    for ag in ad_groups:
                        if f"{ag['name']} (Campaign: {ag['campaign_name']})" == selected_ad_group:
                            ad_group_id = ag['id']
                            break
                    
                    if ad_group_id:
                        ad_group_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/adGroups/{ad_group_id}"
                        
                        keywords_list = keywords_input.strip().split('\n')
                        keywords_data = []
                        for keyword in keywords_list:
                            if keyword.strip():
                                keywords_data.append({
                                    'text': keyword.strip(),
                                    'match_type': match_type,
                                    'cpc_bid_micros': int(default_bid * 1000000)
                                })
                        
                        if keywords_data:
                            result = keyword_manager.add_keywords(ad_group_resource_name, keywords_data)
                            if result:
                                st.success(f"Added {len(keywords_data)} keywords successfully!")
        else:
            st.warning("No ad groups found. Please create an ad group first.")
    
    with tab2:
        st.subheader("Manage Existing Keywords")
        
        # Get all keywords
        all_keywords = keyword_manager.list_keywords()
        
        if all_keywords:
            # Filter options
            st.write("**Filter Keywords:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "ENABLED", "PAUSED"], key="status_filter")
            with col2:
                # Get unique ad groups for filtering
                unique_ad_groups = list(set([kw.get('ad_group_name', 'Unknown') for kw in all_keywords]))
                ad_group_filter = st.selectbox("Filter by Ad Group", ["All"] + unique_ad_groups, key="ag_filter")
            with col3:
                match_type_filter = st.selectbox("Filter by Match Type", ["All", "BROAD", "PHRASE", "EXACT"], key="match_filter")
            
            # Apply filters
            filtered_keywords = all_keywords
            if status_filter != "All":
                filtered_keywords = [kw for kw in filtered_keywords if kw.get('status') == status_filter]
            if ad_group_filter != "All":
                filtered_keywords = [kw for kw in filtered_keywords if kw.get('ad_group_name') == ad_group_filter]
            if match_type_filter != "All":
                filtered_keywords = [kw for kw in filtered_keywords if kw.get('match_type') == match_type_filter]
            
            if filtered_keywords:
                st.write(f"**Found {len(filtered_keywords)} keywords:**")
                
                # Create a more detailed view with action buttons
                for i, keyword in enumerate(filtered_keywords):
                    with st.expander(f"🔑 {keyword.get('text', 'Unknown')} ({keyword.get('match_type', 'Unknown')})"):
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**Ad Group:** {keyword.get('ad_group_name', 'Unknown')}")
                            st.write(f"**Campaign:** {keyword.get('campaign_name', 'Unknown')}")
                            st.write(f"**Status:** {keyword.get('status', 'Unknown')}")
                            st.write(f"**CPC Bid:** ${keyword.get('cpc_bid_micros', 0) / 1000000:.2f}")
                        
                        with col2:
                            # Pause/Enable buttons
                            if keyword.get('status') == 'ENABLED':
                                if st.button(f"⏸️ Pause", key=f"pause_{i}"):
                                    result = keyword_manager.update_keyword_status(keyword['resource_name'], "PAUSED")
                                    if result:
                                        st.success("Keyword paused!")
                                        st.rerun()
                            elif keyword.get('status') == 'PAUSED':
                                if st.button(f"▶️ Enable", key=f"enable_{i}"):
                                    result = keyword_manager.update_keyword_status(keyword['resource_name'], "ENABLED")
                                    if result:
                                        st.success("Keyword enabled!")
                                        st.rerun()
                        
                        with col3:
                            # Bid adjustment
                            current_bid_dollars = max(0.01, keyword.get('cpc_bid_micros', 1000000) / 1000000)  # Ensure minimum 0.01
                            new_bid = st.number_input(f"New Bid ($)", min_value=0.01, value=current_bid_dollars, step=0.01, key=f"bid_{i}")
                            if st.button(f"💰 Update Bid", key=f"update_bid_{i}"):
                                result = keyword_manager.update_keyword_bid(keyword['resource_name'], int(new_bid * 1000000))
                                if result:
                                    st.success("Bid updated!")
                                    st.rerun()
                        
                        with col4:
                            # Remove button with confirmation
                            if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                                # Add a confirmation step
                                st.session_state[f'confirm_remove_{i}'] = True
                            
                            # Show confirmation if button was clicked
                            if st.session_state.get(f'confirm_remove_{i}', False):
                                st.warning(f"⚠️ Confirm removal of '{keyword.get('text')}'?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button(f"✅ Yes", key=f"confirm_yes_{i}"):
                                        result = keyword_manager.remove_keyword(keyword['resource_name'])
                                        if result:
                                            st.success("Keyword removed!")
                                            # Clear confirmation state
                                            if f'confirm_remove_{i}' in st.session_state:
                                                del st.session_state[f'confirm_remove_{i}']
                                            st.rerun()
                                with col_no:
                                    if st.button(f"❌ Cancel", key=f"confirm_no_{i}"):
                                        # Clear confirmation state
                                        if f'confirm_remove_{i}' in st.session_state:
                                            del st.session_state[f'confirm_remove_{i}']
                                        st.rerun()
                
                # Bulk operations
                st.write("---")
                st.subheader("🔧 Bulk Operations")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("⏸️ Pause All Filtered"):
                        success_count = 0
                        for keyword in filtered_keywords:
                            if keyword.get('status') == 'ENABLED':
                                if keyword_manager.update_keyword_status(keyword['resource_name'], "PAUSED"):
                                    success_count += 1
                        st.success(f"Paused {success_count} keywords!")
                        st.rerun()
                
                with col2:
                    if st.button("▶️ Enable All Filtered"):
                        success_count = 0
                        for keyword in filtered_keywords:
                            if keyword.get('status') == 'PAUSED':
                                if keyword_manager.update_keyword_status(keyword['resource_name'], "ENABLED"):
                                    success_count += 1
                        st.success(f"Enabled {success_count} keywords!")
                        st.rerun()
                
                with col3:
                    new_bulk_bid = st.number_input("Bulk Bid Update ($)", min_value=0.01, value=1.0, step=0.01, key="bulk_bid")
                    if st.button(f"💰 Update All Bids to ${new_bulk_bid}"):
                        success_count = 0
                        for keyword in filtered_keywords:
                            if keyword_manager.update_keyword_bid(keyword['resource_name'], int(new_bulk_bid * 1000000)):
                                success_count += 1
                        st.success(f"Updated {success_count} keyword bids!")
                        st.rerun()
                
            else:
                st.info("No keywords match the selected filters.")
        else:
            st.info("No keywords found. Add keywords in the 'Add Keywords' tab.")
    
    with tab3:
        st.subheader("Negative Keywords")
        
        # Campaign negative keywords
        st.write("**Campaign Negative Keywords**")
        campaigns = campaign_manager.list_campaigns()
        
        if campaigns:
            with st.form("add_campaign_negative_keywords_form"):
                selected_campaign = st.selectbox("Select Campaign", 
                    options=[f"{c['name']} (ID: {c['id']})" for c in campaigns])
                
                negative_keywords_input = st.text_area("Negative Keywords (one per line)", 
                    placeholder="Enter negative keywords, one per line")
                
                match_type = st.selectbox("Match Type", ["BROAD", "PHRASE", "EXACT"], key="neg_match_type")
                
                submitted = st.form_submit_button("Add Campaign Negative Keywords")
                
                if submitted and negative_keywords_input and selected_campaign:
                    campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                    campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                    
                    negative_keywords_list = negative_keywords_input.strip().split('\n')
                    negative_keywords_data = []
                    for keyword in negative_keywords_list:
                        if keyword.strip():
                            negative_keywords_data.append({
                                'text': keyword.strip(),
                                'match_type': match_type
                            })
                    
                    if negative_keywords_data:
                        result = keyword_manager.add_negative_keywords_to_campaign(
                            campaign_resource_name, negative_keywords_data
                        )
                        if result:
                            st.success(f"Added {len(negative_keywords_data)} negative keywords to campaign!")
        
        # Display existing negative keywords
        st.write("**Existing Campaign Negative Keywords**")
        negative_keywords = keyword_manager.list_campaign_negative_keywords()
        if negative_keywords:
            df = pd.DataFrame(negative_keywords)
            st.dataframe(df)
    
    with tab4:
        st.subheader("Keyword Performance")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"])
        
        if st.button("Load Keyword Performance"):
            performance_data = keyword_manager.get_keyword_performance(date_range)
            
            if performance_data:
                df = pd.DataFrame(performance_data)
                
                # Convert micros to dollars
                df['cost'] = df['cost_micros'] / 1000000
                df['avg_cpc'] = df['average_cpc'] / 1000000
                df['cost_per_conv'] = df['cost_per_conversion'] / 1000000
                
                st.dataframe(df)
                
                # Performance charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_clicks = px.bar(df.head(10), x='keyword_text', y='clicks', 
                        title="Top 10 Keywords by Clicks")
                    st.plotly_chart(fig_clicks, use_container_width=True)
                
                with col2:
                    fig_cost = px.bar(df.head(10), x='keyword_text', y='cost', 
                        title="Top 10 Keywords by Cost")
                    st.plotly_chart(fig_cost, use_container_width=True)
            else:
                st.info("No keyword performance data available for the selected date range.")

def reporting_page():
    st.header("📊 Reporting & Analytics")
    managers = initialize_managers()
    if not managers:
        return
    
    reporting_manager = managers['reporting_manager']
    
    tab1, tab2, tab3, tab4 = st.tabs(["Customer Overview", "Campaign Performance", "Ad Performance", "Search Terms"])
    
    with tab1:
        st.subheader("Customer Level Metrics")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"], 
            key="customer_date_range")
        
        if st.button("Load Customer Metrics"):
            customer_data = reporting_manager.get_customer_metrics(date_range)
            
            if customer_data:
                df = reporting_manager.create_dataframe(customer_data, 'customer')
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Clicks", f"{df['clicks'].sum():,}")
                
                with col2:
                    st.metric("Total Impressions", f"{df['impressions'].sum():,}")
                
                with col3:
                    st.metric("Total Cost", f"${df['cost'].sum():,.2f}")
                
                with col4:
                    st.metric("Total Conversions", f"{df['conversions'].sum():.1f}")
                
                # Detailed data
                st.subheader("Detailed Customer Data")
                st.dataframe(df)
    
    with tab2:
        st.subheader("Campaign Performance")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"], 
            key="campaign_date_range")
        
        if st.button("Load Campaign Performance"):
            campaign_data = reporting_manager.get_campaign_metrics(date_range)
            
            if campaign_data:
                df = reporting_manager.create_dataframe(campaign_data, 'campaign')
                
                # Performance charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_clicks = px.bar(df, x='campaign_name', y='clicks', 
                        title="Clicks by Campaign")
                    st.plotly_chart(fig_clicks, use_container_width=True)
                
                with col2:
                    fig_cost = px.bar(df, x='campaign_name', y='cost', 
                        title="Cost by Campaign")
                    st.plotly_chart(fig_cost, use_container_width=True)
                
                # CTR vs CPC scatter plot
                if 'ctr' in df.columns and 'average_cpc_dollars' in df.columns:
                    fig_scatter = px.scatter(df, x='ctr', y='average_cpc_dollars', 
                        size='clicks', hover_data=['campaign_name'], 
                        title="CTR vs Average CPC")
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Detailed data
                st.subheader("Detailed Campaign Data")
                st.dataframe(df)
    
    with tab3:
        st.subheader("Ad Performance")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"], 
            key="ad_date_range")
        
        if st.button("Load Ad Performance"):
            ad_data = reporting_manager.get_ad_group_ad_metrics(date_range)
            
            if ad_data:
                df = reporting_manager.create_dataframe(ad_data, 'ad')
                
                # Performance by ad group
                ad_group_performance = df.groupby('ad_group_name').agg({
                    'clicks': 'sum',
                    'impressions': 'sum',
                    'cost': 'sum',
                    'conversions': 'sum'
                }).reset_index()
                
                fig_ad_group = px.bar(ad_group_performance, x='ad_group_name', y='clicks', 
                    title="Clicks by Ad Group")
                st.plotly_chart(fig_ad_group, use_container_width=True)
                
                # Detailed data
                st.subheader("Detailed Ad Data")
                st.dataframe(df)
    
    with tab4:
        st.subheader("Search Terms Analysis")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"], 
            key="search_terms_date_range")
        
        if st.button("Load Search Terms"):
            with st.spinner("Loading search terms data..."):
                search_terms_data = reporting_manager.get_search_term_view_metrics(date_range)
            
            if search_terms_data:
                st.success(f"Loaded {len(search_terms_data)} search terms records")
                df = reporting_manager.create_dataframe(search_terms_data, 'search_terms')
                
                # Top search terms by clicks
                top_terms = df.nlargest(20, 'clicks')
                fig_terms = px.bar(top_terms, x='search_term', y='clicks', 
                    title="Top 20 Search Terms by Clicks")
                fig_terms.update_xaxes(tickangle=45)
                st.plotly_chart(fig_terms, use_container_width=True)
                
                # Detailed data
                st.subheader("Detailed Search Terms Data")
            else:
                st.warning("No search terms data found for the selected date range. This could mean:")
                st.write("• No search queries were recorded in the selected period")
                st.write("• The account might not have enough search activity")
                st.write("• There might be an API access issue")
                st.write("• Try selecting a different date range")

def extensions_page():
    st.header("🔗 Extensions Management")
    managers = initialize_managers()
    if not managers:
        return
    
    extensions_manager = managers['extensions_manager']
    campaign_manager = managers['campaign_manager']
    
    tab1, tab2 = st.tabs(["Create Extensions", "Manage Extensions"])
    
    with tab1:
        st.subheader("Create Ad Extensions")
        
        extension_type = st.selectbox("Extension Type", ["Callout", "Sitelink"])
        
        if extension_type == "Callout":
            with st.form("create_callout_form"):
                callout_text = st.text_input("Callout Text", max_chars=25)
                
                # Option to add to campaign
                campaigns = campaign_manager.list_campaigns()
                selected_campaign = None
                if campaigns:
                    selected_campaign = st.selectbox("Add to Campaign (Optional)", 
                        options=[""] + [f"{c['name']} (ID: {c['id']})" for c in campaigns])
                
                submitted = st.form_submit_button("Create Callout Extension")
                
                if submitted and callout_text:
                    extension_resource_name = extensions_manager.create_callout_extension(callout_text)
                    
                    if extension_resource_name:
                        st.success("Callout extension created successfully!")
                        
                        # Add to campaign if selected
                        if selected_campaign and selected_campaign != "":
                            campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                            campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                            
                            result = extensions_manager.add_callout_extension_to_campaign(
                                campaign_resource_name, extension_resource_name
                            )
                            if result:
                                st.success("Extension added to campaign!")
        
        elif extension_type == "Sitelink":
            with st.form("create_sitelink_form"):
                link_text = st.text_input("Link Text", max_chars=25)
                final_url = st.text_input("Final URL", placeholder="https://example.com")
                description1 = st.text_input("Description 1 (Optional)", max_chars=35)
                description2 = st.text_input("Description 2 (Optional)", max_chars=35)
                
                # Option to add to campaign
                campaigns = campaign_manager.list_campaigns()
                selected_campaign = None
                if campaigns:
                    selected_campaign = st.selectbox("Add to Campaign (Optional)", 
                        options=[""] + [f"{c['name']} (ID: {c['id']})" for c in campaigns])
                
                submitted = st.form_submit_button("Create Sitelink Extension")
                
                if submitted and link_text and final_url:
                    extension_resource_name = extensions_manager.create_sitelink_extension(
                        link_text, final_url, description1 if description1 else None, 
                        description2 if description2 else None
                    )
                    
                    if extension_resource_name:
                        st.success("Sitelink extension created successfully!")
                        
                        # Add to campaign if selected
                        if selected_campaign and selected_campaign != "":
                            campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                            campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                            
                            result = extensions_manager.add_sitelink_extension_to_campaign(
                                campaign_resource_name, extension_resource_name
                            )
                            if result:
                                st.success("Extension added to campaign!")
    
    with tab2:
        st.subheader("Existing Extensions")
        
        extensions = extensions_manager.list_extensions()
        if extensions:
            df = pd.DataFrame(extensions)
            st.dataframe(df)
        else:
            st.info("No extensions found. Create your first extension above.")

def bidding_strategies_page():
    st.header("🎯 Bidding Strategies")
    managers = initialize_managers()
    if not managers:
        return
    
    bidding_manager = managers['bidding_manager']
    campaign_manager = managers['campaign_manager']
    reporting_manager = managers['reporting_manager']
    
    tab1, tab2, tab3 = st.tabs(["Create Bidding Strategy", "Manage Strategies", "Performance"])
    
    with tab1:
        st.subheader("Create Portfolio Bidding Strategy")
        
        strategy_type = st.selectbox("Strategy Type", [
            "Target CPA", 
            "Target ROAS", 
            "Maximize Clicks",
            "Target Spend",
            "Maximize Conversions (Portfolio)",
            "Maximize Conversion Value (Portfolio)"
        ])
        
        if strategy_type == "Target CPA":
            with st.form("create_target_cpa_form"):
                strategy_name = st.text_input("Strategy Name")
                target_cpa = st.number_input("Target CPA ($)", min_value=0.01, value=10.0, step=0.01)
                
                submitted = st.form_submit_button("Create Target CPA Strategy")
                
                if submitted and strategy_name:
                    strategy_resource_name = bidding_manager.create_target_cpa_bidding_strategy(
                        strategy_name, int(target_cpa * 1000000)
                    )
                    
                    if strategy_resource_name:
                        st.success("Target CPA bidding strategy created successfully!")
        
        elif strategy_type == "Target ROAS":
            with st.form("create_target_roas_form"):
                strategy_name = st.text_input("Strategy Name")
                target_roas = st.number_input("Target ROAS", min_value=0.01, value=4.0, step=0.01)
                
                submitted = st.form_submit_button("Create Target ROAS Strategy")
                
                if submitted and strategy_name:
                    strategy_resource_name = bidding_manager.create_target_roas_bidding_strategy(
                        strategy_name, target_roas
                    )
                    
                    if strategy_resource_name:
                        st.success("Target ROAS bidding strategy created successfully!")
        
        elif strategy_type == "Maximize Clicks":
            with st.form("create_maximize_clicks_form"):
                strategy_name = st.text_input("Strategy Name")
                max_cpc = st.number_input("Max CPC ($, Optional)", min_value=0.01, value=5.0, step=0.01)
                use_max_cpc = st.checkbox("Set Max CPC Limit", value=False)
                
                submitted = st.form_submit_button("Create Maximize Clicks Strategy")
                
                if submitted and strategy_name:
                    kwargs = {}
                    if use_max_cpc:
                        kwargs["cpc_bid_ceiling_micros"] = int(max_cpc * 1000000)
                    
                    strategy_resource_name = bidding_manager.create_maximize_clicks_bidding_strategy(
                        strategy_name, **kwargs
                    )
                    
                    if strategy_resource_name:
                        st.success("Maximize Clicks bidding strategy created successfully!")
        
        elif strategy_type == "Target Spend":
            with st.form("create_target_spend_form"):
                strategy_name = st.text_input("Strategy Name")
                max_cpc = st.number_input("Max CPC ($, Optional)", min_value=0.01, value=5.0, step=0.01)
                use_max_cpc = st.checkbox("Set Max CPC Limit", value=False)
                
                submitted = st.form_submit_button("Create Target Spend Strategy")
                
                if submitted and strategy_name:
                    kwargs = {}
                    if use_max_cpc:
                        kwargs["cpc_bid_ceiling_micros"] = int(max_cpc * 1000000)
                    
                    strategy_resource_name = bidding_manager.create_target_spend_bidding_strategy(
                        strategy_name, **kwargs
                    )
                    
                    if strategy_resource_name:
                        st.success("Target Spend bidding strategy created successfully!")
        
        elif strategy_type == "Maximize Conversions (Portfolio)":
            with st.form("create_maximize_conversions_portfolio_form"):
                strategy_name = st.text_input("Strategy Name")
                target_cpa = st.number_input("Target CPA ($, Optional)", min_value=0.01, value=10.0, step=0.01)
                use_target_cpa = st.checkbox("Set Target CPA", value=False)
                
                submitted = st.form_submit_button("Create Maximize Conversions Portfolio Strategy")
                
                if submitted and strategy_name:
                    kwargs = {}
                    if use_target_cpa:
                        kwargs["target_cpa_micros"] = int(target_cpa * 1000000)
                    
                    strategy_resource_name = bidding_manager.create_maximize_conversions_portfolio_strategy(
                        strategy_name, **kwargs
                    )
                    
                    if strategy_resource_name:
                        st.success("Maximize Conversions portfolio strategy created successfully!")
        
        elif strategy_type == "Maximize Conversion Value (Portfolio)":
            with st.form("create_maximize_conversion_value_portfolio_form"):
                strategy_name = st.text_input("Strategy Name")
                target_roas = st.number_input("Target ROAS (Optional)", min_value=0.01, value=4.0, step=0.01)
                use_target_roas = st.checkbox("Set Target ROAS", value=False)
                
                submitted = st.form_submit_button("Create Maximize Conversion Value Portfolio Strategy")
                
                if submitted and strategy_name:
                    kwargs = {}
                    if use_target_roas:
                        kwargs["target_roas"] = target_roas
                    
                    strategy_resource_name = bidding_manager.create_maximize_conversion_value_portfolio_strategy(
                        strategy_name, **kwargs
                    )
                    
                    if strategy_resource_name:
                        st.success("Maximize Conversion Value portfolio strategy created successfully!")
    
    with tab2:
        st.subheader("Existing Bidding Strategies")
        
        strategies = bidding_manager.list_bidding_strategies()
        if strategies:
            df = pd.DataFrame(strategies)
            st.dataframe(df)
            
            # Edit existing strategy
            st.subheader("Edit Bidding Strategy")
            with st.form("edit_strategy_form"):
                selected_strategy = st.selectbox("Select Strategy to Edit", 
                    options=[f"{s['name']} ({s['type']})" for s in strategies])
                
                # Get current strategy details
                current_strategy = None
                for s in strategies:
                    if f"{s['name']} ({s['type']})" == selected_strategy:
                        current_strategy = s
                        break
                
                if current_strategy:
                    new_name = st.text_input("Strategy Name", value=current_strategy['name'])
                    
                    if current_strategy['type'] == 'TARGET_CPA':
                        current_target_cpa = current_strategy.get('target_cpa_micros', 0) / 1000000
                        new_target_cpa = st.number_input("Target CPA ($)", 
                            min_value=0.01, value=float(current_target_cpa), step=0.01)
                        
                        submitted = st.form_submit_button("Update Target CPA Strategy")
                        
                        if submitted:
                            result = bidding_manager.update_bidding_strategy(
                                current_strategy['resource_name'],
                                name=new_name,
                                target_cpa_micros=int(new_target_cpa * 1000000)
                            )
                            if result:
                                st.success("Bidding strategy updated successfully!")
                                st.rerun()
                    
                    elif current_strategy['type'] == 'TARGET_ROAS':
                        current_target_roas = current_strategy.get('target_roas', 0)
                        new_target_roas = st.number_input("Target ROAS", 
                            min_value=0.01, value=float(current_target_roas), step=0.01)
                        
                        submitted = st.form_submit_button("Update Target ROAS Strategy")
                        
                        if submitted:
                            result = bidding_manager.update_bidding_strategy(
                                current_strategy['resource_name'],
                                name=new_name,
                                target_roas=new_target_roas
                            )
                            if result:
                                st.success("Bidding strategy updated successfully!")
                                st.rerun()
            
            # Apply strategy to campaign
            st.subheader("Apply Strategy to Campaign")
            campaigns = campaign_manager.list_campaigns()
            
            if campaigns:
                with st.form("apply_strategy_form"):
                    selected_campaign = st.selectbox("Select Campaign", 
                        options=[f"{c['name']} (ID: {c['id']})" for c in campaigns])
                    
                    selected_strategy = st.selectbox("Select Strategy", 
                        options=[f"{s['name']} ({s['type']})" for s in strategies])
                    
                    submitted = st.form_submit_button("Apply Strategy to Campaign")
                    
                    if submitted and selected_campaign and selected_strategy:
                        campaign_id = selected_campaign.split("ID: ")[1].split(")")[0]
                        campaign_resource_name = f"customers/{st.session_state.ads_sdk.customer_id}/campaigns/{campaign_id}"
                        
                        strategy_resource_name = None
                        strategy_type = None
                        for s in strategies:
                            if f"{s['name']} ({s['type']})" == selected_strategy:
                                strategy_resource_name = s['resource_name']
                                strategy_type = s['type']
                                break
                        
                        if strategy_resource_name and strategy_type:
                            result = bidding_manager.apply_bidding_strategy_to_campaign(
                                campaign_resource_name, strategy_type, 
                                portfolio_bidding_strategy=strategy_resource_name
                            )
                            if result:
                                st.success("Bidding strategy applied to campaign!")
        else:
            st.info("No bidding strategies found. Create your first strategy above.")
    
    with tab3:
        st.subheader("Bidding Strategy Performance")
        
        date_range = st.selectbox("Date Range", 
            ["TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS"], 
            key="bidding_date_range")
        
        if st.button("Load Bidding Strategy Performance"):
            performance_data = reporting_manager.get_bidding_strategy_performance(date_range)
            
            if performance_data:
                df = reporting_manager.create_dataframe(performance_data, 'bidding_strategy')
                
                # Performance metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Clicks", f"{df['clicks'].sum():,}")
                
                with col2:
                    st.metric("Total Cost", f"${df['cost'].sum():,.2f}")
                
                with col3:
                    st.metric("Total Conversions", f"{df['conversions'].sum():.1f}")
                
                # Detailed data
                st.subheader("Detailed Strategy Performance")
                st.dataframe(df)
            else:
                st.info("No bidding strategy performance data available.")

def main():
    st.title("🚀 Google Ads API Management Tool")
    st.write("Complete Google Ads management solution with Required Minimum Functionality")
    
    # Authentication check
    if not st.session_state.authenticated:
        authenticate()
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Campaign Management",
        "Ad Group & Ad Management", 
        "Keyword Management",
        "Reporting & Analytics",
        "Extensions Management",
        "Bidding Strategies",
        "Conversion Tracking",
        "Audit Logs"
    ])
    
    # Account info
    if st.session_state.ads_sdk:
        st.sidebar.write(f"**Customer ID:** {st.session_state.ads_sdk.customer_id}")
        if st.sidebar.button("Disconnect"):
            st.session_state.authenticated = False
            st.session_state.ads_sdk = None
            st.session_state.customer_id = None
            st.rerun()
    
    # Route to appropriate page
    if page == "Campaign Management":
        campaign_management_page()
    elif page == "Ad Group & Ad Management":
        ad_group_management_page()
    elif page == "Keyword Management":
        keyword_management_page()
    elif page == "Reporting & Analytics":
        reporting_page()
    elif page == "Extensions Management":
        extensions_page()
    elif page == "Bidding Strategies":
        bidding_strategies_page()
    elif page == "Conversion Tracking":
        conversion_tracking_page()
    elif page == "Audit Logs":
        audit_logs_page()

def conversion_tracking_page():
    st.header("📊 Conversion Tracking")
    managers = initialize_managers()
    if not managers:
        return
    
    conversion_manager = managers['conversion_manager']
    
    # Check conversion tracking status
    st.subheader("🔍 Conversion Tracking Status")
    tracking_status = conversion_manager.get_conversion_tracking_status()
    
    if tracking_status['status'] == 'configured':
        st.success(f"✅ {tracking_status['message']}")
    elif tracking_status['status'] == 'configured_but_disabled':
        st.warning(f"⚠️ {tracking_status['message']}")
    elif tracking_status['status'] == 'not_configured':
        st.error(f"❌ {tracking_status['message']}")
    else:
        st.error(f"🚨 {tracking_status['message']}")
    
    # Show recommendations
    if tracking_status.get('recommendations'):
        st.write("**Recommendations:**")
        for rec in tracking_status['recommendations']:
            st.write(f"• {rec}")
    
    # Tabs for different functionality
    tab1, tab2, tab3, tab4 = st.tabs(["Create Conversion Action", "Generate Code Snippets", "Manage Conversions", "Installation Guide"])
    
    with tab1:
        st.subheader("Create New Conversion Action")
        with st.form("create_conversion_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Conversion Name", placeholder="e.g., Purchase, Sign-up, Contact Form")
                category = st.selectbox("Category", [
                    "DEFAULT", "PAGE_VIEW", "PURCHASE", "SIGNUP", "LEAD", 
                    "DOWNLOAD", "ADD_TO_CART", "BEGIN_CHECKOUT", "SUBSCRIBE"
                ])
                count_type = st.selectbox("Count", [
                    "ONE_PER_CLICK", "EVERY", "MANY_PER_CLICK"
                ])
            
            with col2:
                default_value = st.number_input("Default Value ($)", min_value=0.0, value=0.0, step=0.01)
                always_use_default = st.checkbox("Always use default value", value=False)
                attribution_model = st.selectbox("Attribution Model", [
                    "LAST_CLICK", "FIRST_CLICK", "LINEAR", "TIME_DECAY", "POSITION_BASED"
                ])
            
            submitted = st.form_submit_button("Create Conversion Action")
            
            if submitted and name:
                value_settings = None
                if default_value > 0:
                    value_settings = {
                        'default_value': default_value,
                        'always_use_default': always_use_default
                    }
                
                result = conversion_manager.create_conversion_action(
                    name=name,
                    category=category, 
                    value_settings=value_settings,
                    count_type=count_type,
                    attribution_model=attribution_model
                )
                
                if result:
                    st.success(f"Conversion action '{name}' created successfully!")
                    st.rerun()
    
    with tab2:
        st.subheader("Generate Tracking Code Snippets")
        
        # Get existing conversions for selection
        conversions = conversion_manager.list_conversion_actions()
        
        if conversions:
            conversion_options = [f"{c['name']} (ID: {c['id']})" for c in conversions if c.get('status') == 'ENABLED']
            
            if conversion_options:
                selected_conversion = st.selectbox("Select Conversion Action", conversion_options)
                
                if selected_conversion:
                    conversion_id = selected_conversion.split("ID: ")[1].split(")")[0]
                    conversion_name = selected_conversion.split(" (ID:")[0]
                    
                    # Generate a simple label (in real implementation, this would come from the API)
                    conversion_label = f"conv{conversion_id[-6:]}"  # Use last 6 digits as label
                    
                    snippet_type = st.radio("Select Snippet Type", ["Website Conversion", "Call Conversion"])
                    
                    if snippet_type == "Website Conversion":
                        st.subheader("🌐 Website Conversion Tracking")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            conversion_value = st.number_input("Conversion Value (Optional)", min_value=0.0, value=0.0, step=0.01)
                        with col2:
                            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "AUD"])
                        
                        if st.button("Generate Website Snippet"):
                            snippets = conversion_manager.generate_website_conversion_snippet(
                                conversion_id, conversion_label, conversion_value if conversion_value > 0 else None
                            )
                            
                            st.success("✅ Website conversion tracking code generated!")
                            
                            st.subheader("📋 Base Tracking Code")
                            st.info("Install this code on ALL pages of your website (in the <head> section)")
                            st.code(snippets['base_snippet'], language='html')
                            
                            st.subheader("📋 Conversion Event Code")
                            st.info("Install this code on your conversion/thank-you pages only")
                            st.code(snippets['conversion_snippet'], language='html')
                            
                            st.subheader("📚 Installation Instructions")
                            for i, instruction in enumerate(snippets['installation_instructions'], 1):
                                st.write(f"{instruction}")
                    
                    elif snippet_type == "Call Conversion":
                        st.subheader("📞 Call Conversion Tracking")
                        
                        phone_number = st.text_input("Your Phone Number", placeholder="+1-555-123-4567")
                        
                        if st.button("Generate Call Snippet") and phone_number:
                            snippets = conversion_manager.generate_call_conversion_snippet(
                                conversion_id, conversion_label, phone_number
                            )
                            
                            st.success("✅ Call conversion tracking code generated!")
                            
                            st.subheader("📋 Call Tracking Code")
                            st.info("Install this code on ALL pages of your website (in the <head> section)")
                            st.code(snippets['call_snippet'], language='html')
                            
                            st.subheader("📚 Installation Instructions")
                            for instruction in snippets['installation_instructions']:
                                st.write(f"{instruction}")
            else:
                st.warning("No enabled conversion actions found. Create and enable a conversion action first.")
        else:
            st.info("No conversion actions found. Create your first conversion action in the 'Create Conversion Action' tab.")
    
    with tab3:
        st.subheader("Manage Existing Conversions")
        
        if conversions:
            df = pd.DataFrame(conversions)
            st.dataframe(df)
            
            # Enable/Disable conversions
            st.subheader("Enable/Disable Conversion Actions")
            conversion_to_manage = st.selectbox("Select Conversion to Manage", 
                [f"{c['name']} (Status: {c.get('status', 'Unknown')})" for c in conversions])
            
            if conversion_to_manage:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Enable Conversion"):
                        # Extract conversion details for resource name construction
                        selected_conv = [c for c in conversions if c['name'] in conversion_to_manage][0]
                        resource_name = f"customers/{conversion_manager.customer_id}/conversionActions/{selected_conv['id']}"
                        result = conversion_manager.update_conversion_action_status(resource_name, "ENABLED")
                        if result:
                            st.rerun()
                
                with col2:
                    if st.button("Disable Conversion"):
                        selected_conv = [c for c in conversions if c['name'] in conversion_to_manage][0]
                        resource_name = f"customers/{conversion_manager.customer_id}/conversionActions/{selected_conv['id']}"
                        result = conversion_manager.update_conversion_action_status(resource_name, "PAUSED")
                        if result:
                            st.rerun()
        else:
            st.info("No conversion actions found. Create your first conversion action above.")
    
    with tab4:
        st.subheader("📚 Conversion Tracking Installation Guide")
        
        st.markdown("""
        ### What is Conversion Tracking?
        Conversion tracking helps you measure the actions that matter most to your business (purchases, sign-ups, calls, etc.) 
        that result from your Google Ads campaigns.
        
        ### Setup Process:
        1. **Create Conversion Actions** - Define what actions you want to track
        2. **Generate Code Snippets** - Get the tracking codes for your website
        3. **Install Tracking Codes** - Add the codes to your website
        4. **Test & Verify** - Make sure tracking is working properly
        
        ### Types of Conversions:
        - **Website Conversions**: Track actions on your website (purchases, form submissions, etc.)
        - **Call Conversions**: Track phone calls from your ads
        - **App Conversions**: Track app installs and in-app actions
        - **Import Conversions**: Upload offline conversion data
        
        ### Testing Your Implementation:
        - Use Google Tag Assistant Chrome extension
        - Check Chrome DevTools Console for errors
        - Look for conversion data in your Google Ads account (may take 24-48 hours)
        - Test actual conversions to verify tracking
        
        ### Common Issues:
        - **Code not firing**: Check if JavaScript is properly loaded
        - **No conversions recorded**: Verify code is on the correct pages
        - **Duplicate tracking**: Don't install the same code multiple times
        - **Wrong values**: Make sure dynamic values are properly passed
        """)

def audit_logs_page():
    st.header("📋 Audit Logs & Job History")
    st.write("Track all changes made to your Google Ads account with timestamps and user information.")
    
    # User identification section
    st.subheader("👤 User Identification")
    col1, col2 = st.columns(2)
    
    with col1:
        current_user = audit_logger.get_user_id()
        st.write(f"**Current User ID:** `{current_user}`")
        
        # Allow user to set a custom user ID
        new_user_id = st.text_input("Set Custom User ID", value=current_user, 
                                   help="This will identify you in all future operations")
        if st.button("Update User ID") and new_user_id != current_user:
            st.session_state.user_id = new_user_id
            st.success(f"User ID updated to: {new_user_id}")
            st.rerun()
    
    with col2:
        customer_id = audit_logger.get_customer_id()
        session_id = audit_logger.get_session_id()
        st.write(f"**Customer ID:** `{customer_id}`")
        st.write(f"**Session ID:** `{session_id}`")
    
    # Statistics Dashboard
    st.subheader("📊 Operation Statistics")
    stats = audit_logger.get_operation_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Operations", stats.get('total_operations', 0))
    with col2:
        st.metric("Operations (24h)", stats.get('operations_last_24h', 0))
    with col3:
        successful_ops = stats.get('status_breakdown', {}).get('SUCCESS', 0)
        st.metric("Successful Operations", successful_ops)
    with col4:
        failed_ops = stats.get('status_breakdown', {}).get('ERROR', 0)
        st.metric("Failed Operations", failed_ops)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if stats.get('operations_by_type'):
            st.subheader("Operations by Type")
            op_types = list(stats['operations_by_type'].keys())
            op_counts = list(stats['operations_by_type'].values())
            fig = px.pie(values=op_counts, names=op_types, title="Distribution of Operation Types")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if stats.get('operations_by_resource'):
            st.subheader("Operations by Resource")
            resource_types = list(stats['operations_by_resource'].keys())
            resource_counts = list(stats['operations_by_resource'].values())
            fig = px.bar(x=resource_types, y=resource_counts, title="Operations by Resource Type")
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Filter Controls
    st.subheader("🔍 Filter Audit Logs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_user = st.selectbox("Filter by User", 
                                 ["All Users"] + list(stats.get('most_active_users', {}).keys()))
        filter_user = None if filter_user == "All Users" else filter_user
    
    with col2:
        operation_types = ["All Operations"] + list(stats.get('operations_by_type', {}).keys())
        filter_operation = st.selectbox("Filter by Operation", operation_types)
        filter_operation = None if filter_operation == "All Operations" else filter_operation
    
    with col3:
        resource_types = ["All Resources"] + list(stats.get('operations_by_resource', {}).keys())
        filter_resource = st.selectbox("Filter by Resource", resource_types)
        filter_resource = None if filter_resource == "All Resources" else filter_resource
    
    with col4:
        log_limit = st.number_input("Number of Records", min_value=10, max_value=1000, value=100)
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)
    
    # Load and display logs
    if st.button("🔄 Load Audit Logs", type="primary"):
        logs = audit_logger.get_audit_logs(
            limit=log_limit,
            user_id=filter_user,
            operation_type=filter_operation,
            resource_type=filter_resource,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None
        )
        
        if logs:
            st.subheader("📄 Audit Log Records")
            
            # Create a DataFrame for better display
            df_data = []
            for log in logs:
                df_data.append({
                    'Timestamp': log['timestamp'],
                    'User': log['user_id'],
                    'Operation': log['operation_type'],
                    'Resource': log['resource_type'],
                    'Function': log['function_name'],
                    'Status': log['result_status'],
                    'Execution Time (ms)': log['execution_time_ms'],
                    'Resource ID': log['resource_id'] or 'N/A',
                    'Error': log['error_message'] or 'None'
                })
            
            df = pd.DataFrame(df_data)
            
            # Display summary
            st.write(f"**Showing {len(df)} records**")
            
            # Color code status
            def highlight_status(val):
                if val == 'SUCCESS':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'ERROR':
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            # Display the dataframe with styling
            styled_df = df.style.applymap(highlight_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Expandable details for each log entry
            st.subheader("📋 Detailed Log Entries")
            for i, log in enumerate(logs[:10]):  # Show details for first 10 entries
                with st.expander(f"🔍 {log['timestamp']} - {log['operation_type']} {log['resource_type']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Basic Information:**")
                        st.json({
                            'ID': log['id'],
                            'Timestamp': log['timestamp'],
                            'User ID': log['user_id'],
                            'Customer ID': log['customer_id'],
                            'Session ID': log['session_id'],
                            'Function Name': log['function_name'],
                            'Execution Time (ms)': log['execution_time_ms']
                        })
                    
                    with col2:
                        st.write("**Operation Details:**")
                        if log['parameters']:
                            st.write("**Parameters:**")
                            st.json(log['parameters'])
                        
                        if log['result_data']:
                            st.write("**Result Data:**")
                            st.json(log['result_data'])
                        
                        if log['error_message']:
                            st.write("**Error Message:**")
                            st.error(log['error_message'])
            
            # Export functionality
            st.subheader("📤 Export Audit Logs")
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("No audit logs found with the specified filters.")
    
    # Clear logs functionality (with confirmation)
    st.subheader("🗑️ Database Management")
    st.warning("⚠️ **Danger Zone** - These operations cannot be undone!")
    
    if st.button("🗑️ Clear All Audit Logs", type="secondary"):
        if st.session_state.get('confirm_clear_logs'):
            # Actually clear the logs
            try:
                import sqlite3
                conn = sqlite3.connect(audit_logger.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM audit_logs")
                conn.commit()
                conn.close()
                st.success("✅ All audit logs have been cleared.")
                st.session_state.confirm_clear_logs = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing logs: {str(e)}")
        else:
            st.session_state.confirm_clear_logs = True
            st.error("⚠️ Click again to confirm deletion of ALL audit logs!")

if __name__ == "__main__":
    main()