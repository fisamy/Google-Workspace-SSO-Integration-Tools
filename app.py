import streamlit as st
import pandas as pd
import datetime
import os
from account_manager import GmailAccountManager

from gmail_api import authenticate_gmail, get_gmail_service, get_messages
from data_processor import process_emails, categorize_emails, get_email_metrics
from visualizations import (
    plot_email_volume_over_time,
    plot_email_categories,
    plot_sender_distribution,
    plot_hourly_distribution,
    plot_word_cloud,
    plot_response_times
)

# Page configuration and styling
st.set_page_config(
    page_title="Gmail Analytics Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .st-emotion-cache-16idsys {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4A90E2;
        color: white;
    }
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .stMetric {
        background-color: #F0F2F6;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "creds" not in st.session_state:
    st.session_state.creds = None
if "emails_df" not in st.session_state:
    st.session_state.emails_df = None
if "service" not in st.session_state:
    st.session_state.service = None
if "fetch_count" not in st.session_state:
    st.session_state.fetch_count = 500

# Initialize cookie manager
from cookie_manager import CookieManager
cookie_manager = CookieManager()

# Restore authentication from cookie if available
if not st.session_state.authenticated:
    auth_cookie = cookie_manager.get_cookie('gmail_auth')
    if auth_cookie:
        try:
            auth_data = json.loads(auth_cookie)
            os.environ["GOOGLE_CLIENT_ID"] = auth_data['client_id']
            os.environ["GOOGLE_CLIENT_SECRET"] = auth_data['client_secret']
            st.session_state.authenticated = True
        except:
            cookie_manager.delete_cookie('gmail_auth')

def main():
    st.title("Gmail Analytics Dashboard")
    
    # Initialize account manager
    if 'account_manager' not in st.session_state:
        st.session_state.account_manager = GmailAccountManager()
    
    # Account management section
    with st.sidebar:
        st.header("Account Management")
        new_email = st.text_input("Add Gmail Account")
        if st.button("Add Account"):
            if new_email:
                if st.session_state.account_manager.add_account(new_email):
                    st.success(f"Successfully added {new_email}")
                    st.rerun()
        
        st.header("Account Status")
        for email in st.session_state.account_manager.list_accounts():
            status = st.session_state.account_manager.get_account_status(email)
            with st.expander(f"📧 {email}"):
                st.write(f"Status: {status['status']}")
                if status['status'] == 'Active':
                    st.write(f"Total Messages: {status['messages_total']}")
                    st.write(f"Total Threads: {status['threads_total']}")
                if st.button(f"Verify {email}", key=f"verify_{email}"):
                    if st.session_state.account_manager.verify_smtp(email):
                        st.success("Account verified successfully")
                    else:
                        st.error("Account verification failed")
    
    # Sidebar for authentication and filtering
    with st.sidebar:
        st.header("Authentication")
        
        if st.session_state.authenticated:
            st.success("✅ Authenticated with Gmail")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.creds = None
                st.session_state.emails_df = None
                st.session_state.service = None
                st.rerun()
        else:
            st.info("Please authenticate with Gmail to analyze your email data")
            client_id = st.text_input("Client ID", type="password", help="Enter your Google OAuth Client ID")
            client_secret = st.text_input("Client Secret", type="password", help="Enter your Google OAuth Client Secret")
            
            if st.button("Authenticate with Gmail"):
                if not client_id or not client_secret:
                    st.error("Please enter both Client ID and Client Secret")
                else:
                    with st.spinner("Authenticating..."):
                        try:
                            os.environ["GOOGLE_CLIENT_ID"] = client_id
                            os.environ["GOOGLE_CLIENT_SECRET"] = client_secret
                            st.session_state.creds = authenticate_gmail()
                            st.session_state.service = get_gmail_service(st.session_state.creds)
                            st.session_state.authenticated = True
                            # Save authentication data in cookie
                            auth_data = {
                                'client_id': client_id,
                                'client_secret': client_secret
                            }
                            cookie_manager.set_cookie('gmail_auth', json.dumps(auth_data))
                            st.success("Authentication successful!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Authentication failed: {str(e)}")
        
        if st.session_state.authenticated:
            st.header("Data Fetching")
            st.session_state.fetch_count = st.number_input(
                "Number of emails to fetch", 
                min_value=100, 
                max_value=1000, 
                value=st.session_state.fetch_count,
                step=100
            )
            
            if st.button("Fetch Emails"):
                with st.spinner("Fetching email data..."):
                    try:
                        messages = get_messages(
                            st.session_state.service, 
                            max_results=st.session_state.fetch_count
                        )
                        st.session_state.emails_df = process_emails(
                            st.session_state.service, 
                            messages
                        )
                        st.success(f"Successfully fetched {len(st.session_state.emails_df)} emails!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error fetching emails: {str(e)}")
            
            if st.session_state.emails_df is not None:
                st.header("Data Filters")
                
                # Date range filter
                min_date = st.session_state.emails_df['date'].min().date()
                max_date = st.session_state.emails_df['date'].max().date()
                
                date_range = st.date_input(
                    "Filter by date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    # Convert to datetime for comparison
                    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                    
                    filtered_df = st.session_state.emails_df[
                        (st.session_state.emails_df['date'] >= start_datetime) &
                        (st.session_state.emails_df['date'] <= end_datetime)
                    ]
                else:
                    filtered_df = st.session_state.emails_df
                
                # Sender filter - show top 20 most frequent senders
                if not filtered_df.empty:
                    top_senders = filtered_df['from'].value_counts().head(20).index.tolist()
                    selected_senders = st.multiselect(
                        "Filter by sender",
                        options=top_senders,
                        default=[]
                    )
                    
                    if selected_senders:
                        filtered_df = filtered_df[filtered_df['from'].isin(selected_senders)]
                
                # Category filter
                if not filtered_df.empty:
                    categorized_df = categorize_emails(filtered_df)
                    categories = categorized_df['category'].unique().tolist()
                    selected_categories = st.multiselect(
                        "Filter by category",
                        options=categories,
                        default=categories
                    )
                    
                    if selected_categories:
                        categorized_df = categorized_df[categorized_df['category'].isin(selected_categories)]
                    
                    filtered_df = categorized_df
    
    # Main content area - only show if authenticated
    if st.session_state.authenticated:
        if st.session_state.emails_df is None:
            st.info("Please fetch your email data using the sidebar to view analytics.")
        else:
            if filtered_df.empty:
                st.warning("No emails match the selected filters. Please adjust your filter settings.")
            else:
                # Email metrics
                st.header("Email Metrics")
                metrics = get_email_metrics(filtered_df)
                
                st.markdown("### 📊 Key Metrics")
                metrics_container = st.container()
                with metrics_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📬 Total Emails", metrics["total_emails"], 
                                delta=f"{metrics['total_emails']-metrics['total_emails_prev']}")
                        st.metric("📈 Daily Average", f"{metrics['avg_daily_volume']:.1f}")
                    with col2:
                        st.metric("📤 Sent Emails", metrics["sent_emails"])
                        st.metric("📨 Avg Message Length", f"{filtered_df['body'].str.len().mean():.0f} chars")
                    with col3:
                        st.metric("📥 Received Emails", metrics["received_emails"])
                        response_rate = (metrics["sent_emails"] / metrics["received_emails"] * 100) if metrics["received_emails"] > 0 else 0
                        st.metric("📫 Response Rate", f"{response_rate:.1f}%")
                st.markdown("---")
                
                # Visualizations
                st.header("Email Trends")
                
                # Email volume over time
                st.subheader("Email Volume Over Time")
                volume_chart = plot_email_volume_over_time(filtered_df)
                st.plotly_chart(volume_chart, use_container_width=True)
                
                # Senders and categories
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Top Email Senders")
                    sender_chart = plot_sender_distribution(filtered_df)
                    st.plotly_chart(sender_chart, use_container_width=True)
                
                with col2:
                    st.subheader("Email Categories")
                    category_chart = plot_email_categories(filtered_df)
                    st.plotly_chart(category_chart, use_container_width=True)
                
                # Hour of day distribution
                st.subheader("Email Activity by Hour")
                hourly_chart = plot_hourly_distribution(filtered_df)
                st.plotly_chart(hourly_chart, use_container_width=True)
                
                # Word cloud of email subjects
                st.subheader("Common Words in Email Subjects")
                word_cloud = plot_word_cloud(filtered_df)
                st.pyplot(word_cloud)
                
                # Response times analysis
                st.subheader("Response Time Analysis")
                response_chart = plot_response_times(filtered_df)
                st.plotly_chart(response_chart, use_container_width=True)
                
                # Raw data table (expandable)
                with st.expander("View Raw Email Data"):
                    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
