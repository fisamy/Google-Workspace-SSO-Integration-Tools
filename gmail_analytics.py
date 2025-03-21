"""
Gmail Analytics Dashboard

A Streamlit application for visualizing and analyzing Gmail data to provide insights
into email patterns and usage.
"""
import os
import json
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from account_manager import GmailAccountManager
from data_processor import (
    process_emails,
    categorize_emails,
    get_email_metrics,
    analyze_response_times,
    extract_common_words
)
from visualizations import (
    plot_email_volume_over_time,
    plot_email_categories,
    plot_sender_distribution,
    plot_hourly_distribution,
    plot_word_cloud,
    plot_response_times,
    plot_importance_distribution
)
from gmail_api import (
    authenticate_gmail,
    get_gmail_service,
    get_messages,
    get_message_detail
)
from cookie_manager import CookieManager
from cookie_consent_ui import CookieConsentUI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize managers
account_manager = GmailAccountManager()
cookie_manager = CookieManager()
cookie_ui = CookieConsentUI(cookie_manager)

# Initialize business analyzer
from business_analyzer import BusinessAnalyzer
business_analyzer = None

# Set page configuration
st.set_page_config(
    page_title="Gmail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'email_data' not in st.session_state:
    st.session_state.email_data = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'connected_accounts' not in st.session_state:
    st.session_state.connected_accounts = []

# Display cookie banner
cookie_ui.display_cookie_banner()

# Handle cookie settings page if active
cookie_ui.handle_cookie_settings()

# Sidebar
st.sidebar.title("Gmail Analytics")

# Account selection/connection
st.sidebar.header("Gmail Accounts")

# Add a new account
with st.sidebar.expander("Add Gmail Account", expanded=len(st.session_state.connected_accounts) == 0):
    email_input = st.text_input("Gmail Address", placeholder="you@gmail.com")
    if st.button("Connect Account"):
        if not email_input:
            st.error("Please enter a Gmail address")
        else:
            with st.spinner(f"Connecting to {email_input}..."):
                success = account_manager.add_account(email_input)
                if success:
                    st.success(f"Successfully connected to {email_input}")
                    if email_input not in st.session_state.connected_accounts:
                        st.session_state.connected_accounts.append(email_input)
                    st.rerun()
                else:
                    st.error(f"Failed to connect to {email_input}. Please check your credentials and try again.")

# Select account to analyze
if st.session_state.connected_accounts:
    selected_account = st.sidebar.selectbox(
        "Select Account to Analyze",
        st.session_state.connected_accounts
    )
    
    # Show account status
    if selected_account:
        status = account_manager.get_account_status(selected_account)
        if status['status'] == 'Active':
            st.sidebar.success(f"Connected: {selected_account}")
            st.sidebar.info(f"Total Messages: {status.get('messages_total', 'Unknown')}")
        else:
            st.sidebar.error(f"Account Status: {status['status']}")

    # Data controls
    st.sidebar.header("Data Controls")
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    days_options = [
        ("Last 7 days", 7),
        ("Last 30 days", 30),
        ("Last 90 days", 90),
        ("Last year", 365),
        ("All time", 9999)
    ]
    selected_range = st.sidebar.radio("Select period", [opt[0] for opt in days_options])
    days_back = next(opt[1] for opt in days_options if opt[0] == selected_range)
    
    # Query filter
    st.sidebar.subheader("Email Filter")
    query_input = st.sidebar.text_input(
        "Search Query",
        placeholder="from:example@domain.com",
        help="Use Gmail search operators (e.g., from:, to:, subject:)"
    )
    
    # Load/refresh data button
    if st.sidebar.button("Load/Refresh Data"):
        if not selected_account:
            st.sidebar.error("Please select an account first")
        else:
            with st.spinner("Loading Gmail data..."):
                try:
                    # Calculate date for query
                    if days_back < 9999:  # Not "All time"
                        date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
                        if query_input:
                            query = f"{query_input} after:{date_filter}"
                        else:
                            query = f"after:{date_filter}"
                    else:
                        query = query_input
                    
                    # Get credentials for the account
                    creds = account_manager.accounts.get(selected_account)
                    if creds:
                        # Build Gmail service
                        gmail_service = get_gmail_service(creds)
                        
                        # Get messages with optional query
                        messages = get_messages(gmail_service, query=query)
                        
                        if messages:
                            # Process emails
                            df = process_emails(gmail_service, messages)
                            
                            # Categorize emails
                            df = categorize_emails(df)
                            
                            # Calculate metrics
                            metrics = get_email_metrics(df)
                            
                            # Store in session state
                            st.session_state.email_data = df
                            st.session_state.metrics = metrics
                            st.session_state.last_update = datetime.now()
                            
                            st.sidebar.success(f"Loaded {len(df)} emails")
                        else:
                            st.sidebar.warning("No emails found matching your criteria")
                    else:
                        st.sidebar.error(f"Could not find credentials for {selected_account}")
                except Exception as e:
                    st.sidebar.error(f"Error loading data: {str(e)}")
    
    # Show last update time
    if st.session_state.last_update:
        st.sidebar.info(f"Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Add cookie settings button to sidebar
cookie_ui.display_cookie_settings_button("Manage Cookie Settings", "sidebar")

# Main content area
st.title("Gmail Analytics Dashboard")

# If no account is connected, show welcome screen
if not st.session_state.connected_accounts:
    st.info("Welcome to Gmail Analytics! Please connect your Gmail account using the sidebar to get started.")
    
    st.header("Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Email Insights")
        st.write("""
        - Email volume over time
        - Categorization of emails
        - Top senders analysis
        - Time of day activity patterns
        """)
        
    with col2:
        st.subheader("⏱ Response Analytics")
        st.write("""
        - Response time analysis
        - Communication patterns
        - Subject word cloud
        - Email importance metrics
        """)
        
    st.subheader("🔒 Privacy First")
    st.write("""
    Your Gmail data never leaves your browser. All analysis happens locally, 
    and no data is stored on remote servers. Your privacy is our top priority.
    """)
    
    # Add cookie footer
    cookie_ui.add_cookie_footer()
    
elif st.session_state.email_data is None:
    st.info("Account connected! Use the 'Load/Refresh Data' button in the sidebar to fetch your Gmail data.")
    st.write("Select your desired date range and any filters before loading data.")
    
    # If account connected but no data, show usage instructions
    st.subheader("Usage Tips")
    st.markdown("""
    - **Date Range**: Select how far back to analyze emails
    - **Email Filter**: Use Gmail search operators for specific filtering
    - **Dashboard Tabs**: Once data is loaded, explore different analytics views
    """)
    
# If data is loaded, show the dashboard
else:
    df = st.session_state.email_data
    metrics = st.session_state.metrics
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Emails", metrics["total_emails"])
    
    with col2:
        st.metric("Sent", metrics["sent_emails"])
    
    with col3:
        st.metric("Received", metrics["received_emails"])
    
    with col4:
        st.metric("Avg. Daily Volume", f"{metrics['avg_daily_volume']:.1f}")
    
    # Create tabs for different visualizations
    tabs = st.tabs([
        "Email Volume", 
        "Categories", 
        "Senders", 
        "Time Patterns",
        "Content Analysis",
        "Response Times",
        "Business Insights"
    ])
    
    # Email Volume tab
    with tabs[0]:
        st.subheader("Email Volume Over Time")
        st.plotly_chart(plot_email_volume_over_time(df), use_container_width=True)
        
        # Additional information
        if "date_range_days" in metrics:
            st.info(f"Data shown for {metrics['date_range_days']} days")
    
    # Categories tab
    with tabs[1]:
        st.subheader("Email Categories")
        st.plotly_chart(plot_email_categories(df), use_container_width=True)
        
        # Show breakdown in a table
        if "category_counts" in metrics:
            st.subheader("Category Breakdown")
            
            # Convert dictionary to DataFrame
            categories_df = pd.DataFrame(
                list(metrics["category_counts"].items()),
                columns=["Category", "Count"]
            )
            categories_df["Percentage"] = categories_df["Count"] / categories_df["Count"].sum() * 100
            categories_df["Percentage"] = categories_df["Percentage"].apply(lambda x: f"{x:.1f}%")
            
            # Display table
            st.dataframe(categories_df, use_container_width=True)
    
    # Senders tab
    with tabs[2]:
        st.subheader("Top Email Senders")
        st.plotly_chart(plot_sender_distribution(df), use_container_width=True)
        
        # Show table of top senders
        if "top_senders" in metrics:
            st.subheader("Top Senders Breakdown")
            
            # Convert dictionary to DataFrame
            senders_df = pd.DataFrame(
                list(metrics["top_senders"].items()),
                columns=["Sender", "Count"]
            )
            senders_df["Percentage"] = senders_df["Count"] / metrics["total_emails"] * 100
            senders_df["Percentage"] = senders_df["Percentage"].apply(lambda x: f"{x:.1f}%")
            
            # Display table
            st.dataframe(senders_df, use_container_width=True)
    
    # Time Patterns tab
    with tabs[3]:
        st.subheader("Email Activity by Hour of Day")
        st.plotly_chart(plot_hourly_distribution(df), use_container_width=True)
        
        # Day of week analysis
        st.subheader("Email Activity by Day of Week")
        
        # Extract day of week
        if not df.empty and 'date' in df.columns:
            df['day_of_week'] = df['date'].dt.day_name()
            
            # Count emails by day of week and sent/received status
            day_counts = df.groupby(['day_of_week', 'is_sent']).size().unstack(fill_value=0).reset_index()
            
            # Reorder days of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if not day_counts.empty:
                day_counts['day_of_week'] = pd.Categorical(day_counts['day_of_week'], categories=day_order, ordered=True)
                day_counts = day_counts.sort_values('day_of_week')
                
                # Create DataFrame for display
                day_df = day_counts.copy()
                
                # Rename columns
                if True in day_df.columns:
                    day_df.rename(columns={True: 'Sent'}, inplace=True)
                else:
                    day_df['Sent'] = 0
                    
                if False in day_df.columns:
                    day_df.rename(columns={False: 'Received'}, inplace=True)
                else:
                    day_df['Received'] = 0
                
                # Add total column
                day_df['Total'] = day_df['Sent'] + day_df['Received']
                
                # Display table
                st.dataframe(day_df, use_container_width=True)
    
    # Content Analysis tab
    with tabs[4]:
        st.subheader("Word Cloud from Email Subjects")
        fig = plot_word_cloud(df, column='subject')
        st.pyplot(fig)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Email Importance")
            st.plotly_chart(plot_importance_distribution(df), use_container_width=True)
        
        with col2:
            st.subheader("Common Words in Subject Lines")
            
            # Get common words
            common_words = extract_common_words(df, column='subject', n=20)
            
            # Convert to DataFrame
            if common_words:
                words_df = pd.DataFrame(common_words, columns=["Word", "Count"])
                st.dataframe(words_df, use_container_width=True)
            else:
                st.info("No significant words found")
    
    # Response Times tab
    with tabs[5]:
        st.subheader("Email Response Time Analysis")
        st.plotly_chart(plot_response_times(df), use_container_width=True)
        
        # Additional response metrics
        response_df = analyze_response_times(df)
        
        if not response_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                my_responses = response_df[response_df['is_sent_by_me']]
                if not my_responses.empty:
                    st.metric(
                        "My Avg. Response Time", 
                        f"{my_responses['response_time_hours'].mean():.1f} hours"
                    )
                    st.metric(
                        "My Median Response Time", 
                        f"{my_responses['response_time_hours'].median():.1f} hours"
                    )
            
            with col2:
                others_responses = response_df[~response_df['is_sent_by_me']]
                if not others_responses.empty:
                    st.metric(
                        "Others' Avg. Response Time", 
                        f"{others_responses['response_time_hours'].mean():.1f} hours"
                    )
                    st.metric(
                        "Others' Median Response Time", 
                        f"{others_responses['response_time_hours'].median():.1f} hours"
                    )
        else:
            st.info("No response time data available. This could be because there are no conversation threads in the selected data range.")
            
    # Business Insights tab
    with tabs[6]:
        st.subheader("Business Analytics")
        
        if not df.empty:
            business_analyzer = BusinessAnalyzer(df)
            metrics = business_analyzer.get_business_metrics()
            insights = business_analyzer.generate_business_insights()
            
            # Display key metrics
            st.write("### Key Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if "communication_volume" in metrics:
                    vol = metrics["communication_volume"]
                    st.metric("Daily Volume", f"{vol.get('avg_daily_volume', 0):.1f}")
                    st.metric("S/R Ratio", f"{vol.get('sent_received_ratio', 0):.1f}%")
            
            with col2:
                if "response_efficiency" in metrics:
                    eff = metrics["response_efficiency"]
                    st.metric("Avg Response Time", f"{eff.get('avg_response_time', 0):.1f}h")
                    st.metric("Response Rate", f"{eff.get('response_rate', 0):.1f}%")
            
            with col3:
                if "contact_engagement" in metrics:
                    eng = metrics["contact_engagement"]
                    st.metric("Total Contacts", eng.get('total_contacts', 0))
                    st.metric("Avg Interactions", f"{eng.get('avg_interactions_per_contact', 0):.1f}")
            
            # Display insights
            st.write("### Key Insights")
            for insight in insights:
                st.write(f"• {insight}")
            
            # Display domain analysis
            if "domain_analysis" in metrics:
                st.write("### Domain Distribution")
                domain_data = pd.DataFrame(
                    list(metrics["domain_analysis"]["top_domains"].items()),
                    columns=["Domain", "Count"]
                )
                st.bar_chart(domain_data.set_index("Domain"))
        else:
            st.info("Load email data to view business insights.")

# Create Streamlit config file if it doesn't exist
if __name__ == "__main__":
    # Check for environment folder
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
    
    # Create Streamlit config
    if not os.path.exists(".streamlit/config.toml"):
        with open(".streamlit/config.toml", "w") as f:
            f.write("""
[server]
headless = true
address = "0.0.0.0"
port = 5000
            """)