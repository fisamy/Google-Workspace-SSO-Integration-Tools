"""
Cookie Consent UI Component for Streamlit Applications

This module provides a user interface for cookie consent management
that can be integrated into Streamlit applications.
"""
import streamlit as st
import json
from typing import Dict, Optional, Any
from cookie_manager import CookieManager

class CookieConsentUI:
    def __init__(self, cookie_manager: CookieManager):
        """
        Initialize the Cookie Consent UI.
        
        Args:
            cookie_manager: An instance of the CookieManager class
        """
        self.cookie_manager = cookie_manager
        
        # Initialize session state for UI
        if "show_cookie_settings" not in st.session_state:
            st.session_state.show_cookie_settings = False
            
    def display_cookie_banner(self, key_prefix: str = "banner") -> Optional[Dict[str, Any]]:
        """
        Display a cookie consent banner if consent has not been given.
        
        Args:
            key_prefix: Prefix for Streamlit widget keys to avoid duplicates
            
        Returns:
            Consent status or None if no action was taken
        """
        consent_status = self.cookie_manager.get_consent_status()
        
        # If consent already given, don't show banner
        if consent_status["consent"]["status"] == "granted":
            return None
            
        # Container for banner at the bottom of the page
        with st.container():
            # Use columns for layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("### We use cookies")
                st.write("""
                This website uses cookies to improve your experience, analyze our traffic, 
                and provide social media features. By using our website, you accept our use of cookies.
                Click 'Accept All' to consent to all cookies, or click 'Cookie Settings' to manage your preferences.
                """)
                
            with col2:
                # Accept all button
                if st.button("Accept All", key=f"{key_prefix}_accept_all"):
                    # Enable all cookie categories
                    preferences = {category: True for category in self.cookie_manager.get_categories().keys()}
                    result = self.cookie_manager.set_consent("granted", preferences)
                    return result
                
                # Settings button
                if st.button("Cookie Settings", key=f"{key_prefix}_settings"):
                    st.session_state.show_cookie_settings = True
                    # Return None as no consent was given yet
                    return None
                    
                # Reject all button
                if st.button("Reject All", key=f"{key_prefix}_reject_all"):
                    # Only allow necessary cookies
                    preferences = {category: False for category in self.cookie_manager.get_categories().keys()}
                    preferences["necessary"] = True  # necessary cookies are always enabled
                    result = self.cookie_manager.set_consent("denied", preferences)
                    return result
                    
        return None
        
    def display_preferences_form(self, key_prefix: str = "prefs") -> Optional[Dict[str, Any]]:
        """
        Display a detailed cookie preferences form.
        
        Args:
            key_prefix: Prefix for Streamlit widget keys to avoid duplicates
            
        Returns:
            Consent status or None if no action was taken
        """
        st.subheader("Cookie Preferences")
        
        # Get current consent status
        consent_status = self.cookie_manager.get_consent_status()
        categories = self.cookie_manager.get_categories()
        
        # Create form for cookie settings
        preferences = {}
        
        # Initialize with current preferences
        for category, details in categories.items():
            is_necessary = category == "necessary"
            current_value = consent_status["preferences"].get(category, False)
            
            # Display category information
            st.write(f"**{details['name']}**")
            st.write(details["description"])
            
            # Checkbox for category (disabled for necessary cookies)
            if is_necessary:
                st.checkbox(
                    "Enabled", 
                    value=True, 
                    disabled=True,
                    key=f"{key_prefix}_{category}"
                )
                preferences[category] = True
            else:
                preferences[category] = st.checkbox(
                    "Enable", 
                    value=current_value,
                    key=f"{key_prefix}_{category}"
                )
            
            st.write("---")
        
        # Save preferences button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Preferences", key=f"{key_prefix}_save"):
                result = self.cookie_manager.set_consent("granted", preferences)
                st.session_state.show_cookie_settings = False
                return result
                
        with col2:
            if st.button("Cancel", key=f"{key_prefix}_cancel"):
                st.session_state.show_cookie_settings = False
                return None
                
        return None
        
    def display_management_page(self) -> None:
        """Display a full cookie management page."""
        # Current consent status
        consent_status = self.cookie_manager.get_consent_status()
        
        st.subheader("Cookie Consent Status")
        status = consent_status["consent"]["status"]
        
        if status == "granted":
            st.success("Consent: Granted")
        elif status == "denied":
            st.error("Consent: Denied")
        else:
            st.warning("Consent: Not yet provided")
            
        st.write(f"Last updated: {consent_status['consent']['date']}")
        
        # Display current preferences
        st.subheader("Current Preferences")
        
        categories = self.cookie_manager.get_categories()
        for category, details in categories.items():
            enabled = consent_status["preferences"].get(category, False)
            status_text = "Enabled" if enabled else "Disabled"
            
            if enabled:
                st.success(f"{details['name']}: {status_text}")
            else:
                st.error(f"{details['name']}: {status_text}")
                
        # List of active cookies
        st.subheader("Active Cookies")
        cookies = self.cookie_manager.get_all_cookies(include_details=True)
        
        if not cookies:
            st.info("No active cookies")
        else:
            for name, details in cookies.items():
                st.write(f"**{name}**")
                st.write(f"- Category: {details.get('category', 'unknown')}")
                st.write(f"- Created: {details.get('created', 'unknown')}")
                st.write(f"- Expires: {details.get('expires', 'unknown')}")
                if "description" in details:
                    st.write(f"- Purpose: {details['description']}")
                st.write("---")
                
        # Update preferences button
        if st.button("Update Cookie Preferences"):
            st.session_state.show_cookie_settings = True
            
        # Display preference form if requested
        if st.session_state.show_cookie_settings:
            st.markdown("---")
            self.display_preferences_form(key_prefix="management")
            
    def display_cookie_settings_button(self, label: str = "Cookie Settings", location: str = "sidebar") -> bool:
        """
        Display a button to open cookie settings.
        
        Args:
            label: Button label
            location: Where to place the button ("sidebar" or "main")
            
        Returns:
            True if button was clicked
        """
        if location == "sidebar":
            clicked = st.sidebar.button(label)
        else:
            clicked = st.button(label)
            
        if clicked:
            st.session_state.show_cookie_settings = True
            
        return clicked
            
    def handle_cookie_settings(self) -> None:
        """Handle displaying and hiding cookie settings."""
        if st.session_state.show_cookie_settings:
            with st.expander("Cookie Settings", expanded=True):
                if self.display_preferences_form(key_prefix="popup"):
                    st.success("Cookie preferences updated!")
                    st.rerun()
                    
    def add_cookie_footer(self) -> None:
        """Add a small cookie settings button to the page footer."""
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.8em;">
                <a href="#" onclick="javascript:document.dispatchEvent(new CustomEvent('cookie_settings')); return false;">
                    Cookie Settings
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Handle the event
        if st.button("Cookie Settings", key="footer_cookie_settings"):
            st.session_state.show_cookie_settings = True