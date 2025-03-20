import streamlit as st
import pandas as pd
import datetime
import os

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

# Page configuration
st.set_page_config(
    page_title="Gmail Analytics Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def main():
    st.title("Gmail Analytics Dashboard")
    
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
            if st.button("Authenticate with Gmail"):
                with st.spinner("Authenticating..."):
                    try:
                        st.session_state.creds = authenticate_gmail()
                        st.session_state.service = get_gmail_service(st.session_state.creds)
                        st.session_state.authenticated = True
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
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Emails", metrics["total_emails"])
                with col2:
                    st.metric("Sent Emails", metrics["sent_emails"])
                with col3:
                    st.metric("Received Emails", metrics["received_emails"])
                with col4:
                    st.metric("Average Daily Volume", f"{metrics['avg_daily_volume']:.1f}")
                
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
