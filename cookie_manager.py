"""
Cookie Management System for Streamlit Applications

This module provides cookie management capabilities for Streamlit applications,
including cookie categorization, consent management, and storage.
"""
import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Define cookie categories with descriptions
COOKIE_CATEGORIES = {
    "necessary": {
        "name": "Necessary Cookies",
        "description": "These cookies are required for the website to function properly and cannot be disabled."
    },
    "functional": {
        "name": "Functional Cookies",
        "description": "These cookies enable personalized features and functionality."
    },
    "analytics": {
        "name": "Analytics Cookies",
        "description": "These cookies help us understand how visitors interact with the website."
    },
    "marketing": {
        "name": "Marketing Cookies",
        "description": "These cookies are used for marketing purposes, such as showing relevant advertisements."
    },
    "third_party": {
        "name": "Third-Party Cookies",
        "description": "These cookies are set by third-party services or content embedded on our pages."
    }
}

class CookieManager:
    def __init__(self):
        """Initialize the cookie manager and set up session state."""
        # Initialize session state for cookies
        if "cookies" not in st.session_state:
            st.session_state.cookies = {}
            
        # Initialize session state for consent
        if "cookie_consent" not in st.session_state:
            st.session_state.cookie_consent = {
                "status": "unknown",  # 'unknown', 'granted', 'denied'
                "date": datetime.utcnow().isoformat(),
                "preferences": {category: False for category in COOKIE_CATEGORIES.keys()}
            }
            # Necessary cookies are always enabled
            st.session_state.cookie_consent["preferences"]["necessary"] = True

    def set_cookie_with_options(self, name: str, value: str, category: str = "necessary", options: Dict = None) -> Dict:
        """
        Set a cookie with custom options and categorization.
        
        Args:
            name: Cookie name
            value: Cookie value
            category: Category of the cookie (necessary, functional, analytics, marketing, third_party)
            options: Additional cookie options
            
        Returns:
            Dict with operation result
        """
        # Validate category
        if category not in COOKIE_CATEGORIES:
            return {"error": f"Invalid cookie category: {category}"}
        
        # Check if consent allows setting this cookie
        if not self._check_category_consent(category):
            return {"error": f"Consent not given for {category} cookies"}
        
        # Default options
        cookie_options = {
            "value": value,
            "category": category,
            "created": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        # Add description from category
        cookie_options["description"] = COOKIE_CATEGORIES[category]["description"]
        
        # Add custom options
        if options:
            cookie_options.update(options)
        
        # Store cookie
        st.session_state.cookies[name] = cookie_options
        
        return {"success": True, "message": f"Cookie '{name}' set successfully"}

    def get_cookie_details(self, name: str) -> Optional[Dict]:
        """Get full cookie details if it exists, hasn't expired, and consent is given."""
        # Check if cookie exists
        if name not in st.session_state.cookies:
            return None
        
        cookie = st.session_state.cookies[name]
        
        # Check if expired
        if "expires" in cookie:
            expiry = datetime.fromisoformat(cookie["expires"])
            if expiry < datetime.utcnow():
                return None
        
        # Check consent
        if not self._check_category_consent(cookie.get("category", "necessary")):
            return None
        
        return cookie

    def has_cookie(self, name: str) -> bool:
        """Check if a valid cookie exists and consent allows access."""
        return self.get_cookie_details(name) is not None

    def extend_expiry(self, name: str, days: int = None) -> bool:
        """
        Extend the expiry of a cookie.
        
        Args:
            name: Cookie name
            days: Number of days to extend expiry by (uses default if None)
            
        Returns:
            True if cookie was updated, False otherwise
        """
        # Check if cookie exists
        if name not in st.session_state.cookies:
            return False
        
        # Get current details
        cookie = st.session_state.cookies[name]
        
        # Set new expiry
        if days is None:
            days = 30  # Default extension
            
        new_expiry = datetime.utcnow() + timedelta(days=days)
        cookie["expires"] = new_expiry.isoformat()
        
        # Update cookie
        st.session_state.cookies[name] = cookie
        
        return True

    def set_cookie(self, name: str, value: str, category: str = "necessary", expires_days: int = 30, description: str = None) -> Dict:
        """
        Set a cookie with expiration and category.
        
        Args:
            name: Cookie name
            value: Cookie value
            category: Cookie category
            expires_days: Days until expiration
            description: Optional description of the cookie purpose
            
        Returns:
            Dict with operation result
        """
        options = {
            "expires": (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
        }
        
        if description:
            options["description"] = description
            
        return self.set_cookie_with_options(name, value, category, options)

    def get_cookie(self, name: str) -> Optional[str]:
        """Get cookie value if it exists, hasn't expired, and consent allows access."""
        details = self.get_cookie_details(name)
        if details and "value" in details:
            return details["value"]
        return None

    def delete_cookie(self, name: str) -> None:
        """Delete a cookie if it exists."""
        if name in st.session_state.cookies:
            del st.session_state.cookies[name]

    def get_all_cookies(self, include_details: bool = False) -> Dict:
        """
        Get all valid cookies for which consent has been given.
        
        Args:
            include_details: Whether to include full cookie details or just values
            
        Returns:
            Dict of cookies
        """
        result = {}
        
        for name, details in st.session_state.cookies.items():
            # Check if expired
            if "expires" in details:
                expiry = datetime.fromisoformat(details["expires"])
                if expiry < datetime.utcnow():
                    continue
            
            # Check consent
            if not self._check_category_consent(details.get("category", "necessary")):
                continue
            
            # Add to result
            if include_details:
                result[name] = details
            else:
                result[name] = details.get("value")
        
        return result

    def get_cookies_by_category(self, category: str, include_details: bool = False) -> Dict:
        """
        Get all valid cookies belonging to a specific category.
        
        Args:
            category: Cookie category
            include_details: Whether to include full cookie details or just values
            
        Returns:
            Dict of cookies in the requested category
        """
        result = {}
        
        for name, details in st.session_state.cookies.items():
            # Check category
            if details.get("category") != category:
                continue
            
            # Check if expired
            if "expires" in details:
                expiry = datetime.fromisoformat(details["expires"])
                if expiry < datetime.utcnow():
                    continue
            
            # Check consent
            if not self._check_category_consent(category):
                continue
            
            # Add to result
            if include_details:
                result[name] = details
            else:
                result[name] = details.get("value")
        
        return result

    def clear_all_cookies(self, exclude_necessary: bool = True) -> None:
        """
        Clear all cookies, optionally preserving necessary cookies.
        
        Args:
            exclude_necessary: Whether to preserve necessary cookies
        """
        if exclude_necessary:
            # Keep only necessary cookies
            for name, details in list(st.session_state.cookies.items()):
                if details.get("category") != "necessary":
                    del st.session_state.cookies[name]
        else:
            # Clear all cookies
            st.session_state.cookies = {}

    def clear_category(self, category: str) -> None:
        """
        Clear all cookies in a specific category.
        
        Args:
            category: Category of cookies to clear
        """
        for name, details in list(st.session_state.cookies.items()):
            if details.get("category") == category:
                del st.session_state.cookies[name]

    def set_consent(self, status: str, preferences: Dict[str, bool] = None) -> Dict:
        """
        Set cookie consent status and preferences.
        
        Args:
            status: Consent status ("granted" or "denied")
            preferences: Dict of category preferences
            
        Returns:
            Dict with operation result
        """
        # Validate status
        if status not in ["granted", "denied", "unknown"]:
            return {"error": "Invalid consent status. Use 'granted', 'denied', or 'unknown'."}
        
        # If preferences not provided, use current
        if preferences is None:
            preferences = st.session_state.cookie_consent.get("preferences", {})
        
        # Make sure necessary cookies are always enabled
        preferences["necessary"] = True
        
        # Update consent
        st.session_state.cookie_consent = {
            "status": status,
            "date": datetime.utcnow().isoformat(),
            "preferences": preferences
        }
        
        # If consent denied, clear non-necessary cookies
        if status == "denied":
            self.clear_all_cookies(exclude_necessary=True)
        
        # If specific preferences provided, clear cookies for denied categories
        elif status == "granted" and preferences:
            for category, allowed in preferences.items():
                if not allowed and category != "necessary":
                    self.clear_category(category)
        
        return {
            "success": True,
            "status": status,
            "preferences": preferences
        }

    def get_consent_status(self) -> Dict:
        """
        Get current consent status and preferences.
        
        Returns:
            Dict with consent status information
        """
        return {
            "consent": st.session_state.cookie_consent,
            "preferences": st.session_state.cookie_consent.get("preferences", {})
        }

    def has_consent(self) -> bool:
        """
        Check if user has given cookie consent.
        
        Returns:
            True if consent has been granted, False otherwise
        """
        return st.session_state.cookie_consent.get("status") == "granted"

    def get_categories(self) -> Dict:
        """
        Get information about available cookie categories.
        
        Returns:
            Dict with category information
        """
        return COOKIE_CATEGORIES

    def export_consent_record(self) -> Dict:
        """
        Generate a consent record for compliance purposes.
        
        Returns:
            Dict with consent record
        """
        return {
            "consent": st.session_state.cookie_consent,
            "timestamp": datetime.utcnow().isoformat(),
            "user_agent": "Streamlit App",  # Would need to be retrieved from request in a production app
            "cookies": self.get_all_cookies(include_details=True)
        }

    def _check_category_consent(self, category: str) -> bool:
        """
        Check if consent has been given for a specific cookie category.
        
        Args:
            category: Cookie category to check
            
        Returns:
            True if consent given or category is necessary, False otherwise
        """
        # Necessary cookies always have consent
        if category == "necessary":
            return True
        
        # Get consent status
        consent_status = st.session_state.cookie_consent.get("status")
        preferences = st.session_state.cookie_consent.get("preferences", {})
        
        # If consent granted, check specific preference
        if consent_status == "granted":
            return preferences.get(category, False)
        
        # If consent denied or unknown, only necessary cookies allowed
        return False