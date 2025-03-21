"""
Cookie Consent UI Component for Streamlit Applications

This module provides a user interface for cookie consent management
that can be integrated into Streamlit applications.
"""
import streamlit as st
from cookie_manager import CookieManager, COOKIE_CATEGORIES
import json
from typing import Dict, Optional, Any

class CookieConsentUI:
    def __init__(self, cookie_manager: CookieManager):
        """
        Initialize the Cookie Consent UI.
        
        Args:
            cookie_manager: An instance of the CookieManager class
        """
        self.cookie_manager = cookie_manager
        self.categories = COOKIE_CATEGORIES

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
        
        # Display banner
        with st.container():
            st.markdown("""
            <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; border: 1px solid #dee2e6;">
                <h3 style="margin-top: 0;">Cookie Consent</h3>
                <p>This website uses cookies to enhance your experience. By continuing to browse, you agree to our use of cookies.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("Accept All", key=f"{key_prefix}_accept_all"):
                    # Accept all cookies
                    preferences = {category: True for category in self.categories.keys()}
                    result = self.cookie_manager.set_consent("granted", preferences)
                    st.success("Thank you! Your preferences have been saved.")
                    return result
            
            with col2:
                if st.button("Reject All", key=f"{key_prefix}_reject_all"):
                    # Reject all except necessary
                    preferences = {category: False for category in self.categories.keys()}
                    preferences["necessary"] = True  # Necessary cookies always enabled
                    result = self.cookie_manager.set_consent("denied", preferences)
                    st.success("Your preferences have been saved. Only necessary cookies will be used.")
                    return result
            
            with col3:
                if st.button("Preferences", key=f"{key_prefix}_preferences"):
                    # Show expanded preferences in session state
                    if "show_cookie_preferences" not in st.session_state:
                        st.session_state.show_cookie_preferences = True
                    else:
                        st.session_state.show_cookie_preferences = True
        
        # Show detailed preferences if requested
        if st.session_state.get("show_cookie_preferences", False):
            return self.display_preferences_form(key_prefix)
        
        return None

    def display_preferences_form(self, key_prefix: str = "prefs") -> Optional[Dict[str, Any]]:
        """
        Display a detailed cookie preferences form.
        
        Args:
            key_prefix: Prefix for Streamlit widget keys to avoid duplicates
            
        Returns:
            Consent status or None if no action was taken
        """
        with st.form(key=f"{key_prefix}_form"):
            st.markdown("### Cookie Preferences")
            st.markdown("Please select which types of cookies you would like to accept.")
            
            # Get current preferences
            current_prefs = self.cookie_manager.get_consent_status()["preferences"]
            
            # Prepare new preferences dict
            new_preferences = {}
            
            # Add toggle for each category
            for category_id, category_info in self.categories.items():
                # Necessary cookies can't be disabled
                if category_id == "necessary":
                    st.markdown(f"**{category_info['name']}**: {category_info['description']}")
                    st.info("These cookies are required for the website to function and cannot be disabled.")
                    new_preferences[category_id] = True
                else:
                    # Create a checkbox for this category
                    value = st.checkbox(
                        f"{category_info['name']}",
                        value=current_prefs.get(category_id, False),
                        help=category_info['description'],
                        key=f"{key_prefix}_{category_id}"
                    )
                    new_preferences[category_id] = value
            
            # Submit button
            submitted = st.form_submit_button("Save Preferences")
            
            if submitted:
                # Save preferences
                result = self.cookie_manager.set_consent("granted", new_preferences)
                st.success("Your cookie preferences have been saved.")
                
                # Clear the show preferences flag
                st.session_state.show_cookie_preferences = False
                
                return result
        
        return None

    def display_management_page(self) -> None:
        """Display a full cookie management page."""
        st.title("Cookie Settings")
        
        # Current status summary
        consent_status = self.cookie_manager.get_consent_status()
        
        if consent_status["consent"]["status"] == "granted":
            st.success("You have given consent to cookies on this site.")
        elif consent_status["consent"]["status"] == "denied":
            st.warning("You have declined non-essential cookies on this site.")
        else:
            st.info("You have not yet set your cookie preferences.")
        
        # Preference tabs
        tabs = st.tabs(["Preferences", "Current Cookies", "Privacy Information"])
        
        with tabs[0]:
            self.display_preferences_form("mgmt")
        
        with tabs[1]:
            st.subheader("Currently Stored Cookies")
            
            # Get cookies with details
            cookies_by_category = {}
            for category in self.categories:
                category_cookies = self.cookie_manager.get_cookies_by_category(category, include_details=True)
                if category_cookies:
                    cookies_by_category[category] = category_cookies
            
            if not any(cookies_by_category.values()):
                st.info("No cookies currently stored.")
            else:
                for category_id, cookies in cookies_by_category.items():
                    category_info = self.categories[category_id]
                    with st.expander(f"{category_info['name']} ({len(cookies)})"):
                        if not cookies:
                            st.write("No cookies in this category.")
                        else:
                            for name, details in cookies.items():
                                st.write(f"**{name}**")
                                st.json(details)
            
            # Clear buttons
            st.subheader("Clear Cookies")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Clear All Non-Essential Cookies"):
                    self.cookie_manager.clear_all_cookies(exclude_necessary=True)
                    st.success("All non-essential cookies have been cleared.")
                    st.experimental_rerun()
            
            with col2:
                if st.button("Clear All Cookies"):
                    self.cookie_manager.clear_all_cookies(exclude_necessary=False)
                    st.success("All cookies have been cleared.")
                    st.experimental_rerun()
        
        with tabs[2]:
            st.subheader("Privacy Information")
            st.markdown("""
            ### Cookie Policy
            
            This website uses cookies to improve your experience while you navigate through the website. 
            Cookies categorized as necessary are stored on your browser as they are essential for the basic 
            functionalities of the website to work properly.
            
            We also use third-party cookies that help us analyze and understand how you use this website, 
            to store user preferences, and to provide content and advertisements. These cookies will be 
            stored in your browser only with your consent.
            
            ### Cookie Categories
            
            - **Necessary**: Essential for the website to function properly. These cannot be disabled.
            - **Functional**: Enable enhanced functionality and personalization.
            - **Analytics**: Help us understand how visitors interact with the website.
            - **Marketing**: Used to track visitors across websites for advertising purposes.
            - **Third Party**: Set by third-party services or content embedded on our pages.
            
            ### Your Rights
            
            You have the right to accept or decline cookies (except necessary cookies). You can 
            exercise your preferences by clicking on the preference settings on this page.
            
            ### Data Retention
            
            Cookies expire after their designated lifespan, which may vary from session-only 
            to persistent cookies that remain valid for a set period.
            
            ### Changes to This Policy
            
            We may update our cookie policy from time to time. Any changes will be posted on this page.
            """)
            
            # Export consent record
            st.subheader("Your Consent Record")
            record = self.cookie_manager.export_consent_record()
            st.json(record)
            
            consent_json = json.dumps(record, indent=2)
            st.download_button(
                "Download Consent Record",
                consent_json,
                "consent_record.json",
                "application/json"
            )

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
            # Set flag to show settings
            st.session_state.show_cookie_settings = True
            return True
            
        return False

    def handle_cookie_settings(self) -> None:
        """Handle displaying and hiding cookie settings."""
        # If settings flag is set, show the management page
        if st.session_state.get("show_cookie_settings", False):
            with st.container():
                self.display_management_page()
                
                if st.button("Close Settings"):
                    st.session_state.show_cookie_settings = False
                    st.experimental_rerun()

    def add_cookie_footer(self) -> None:
        """Add a small cookie settings button to the page footer."""
        st.markdown("""
        <div style="position: fixed; bottom: 10px; right: 10px; background-color: #f8f9fa; 
        padding: 5px 10px; border-radius: 5px; border: 1px solid #dee2e6; z-index: 1000;">
            <a href="#" id="cookie-settings-btn" style="text-decoration: none; color: #495057;">
                🍪 Cookie Settings
            </a>
        </div>
        <script>
            document.getElementById('cookie-settings-btn').addEventListener('click', function(e) {
                e.preventDefault();
                // This would need integration with Streamlit's event system
                // For now, we're using the sidebar button instead
            });
        </script>
        """, unsafe_allow_html=True)