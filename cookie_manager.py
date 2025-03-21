
from typing import Dict, Optional, List, Any, Union
import streamlit as st
from datetime import datetime, timedelta
import json
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cookie categories based on common industry standards
COOKIE_CATEGORIES = {
    "necessary": {
        "name": "Necessary",
        "description": "Essential cookies required for basic website functionality. Cannot be disabled.",
        "required": True
    },
    "functional": {
        "name": "Functional",
        "description": "Cookies that enhance functionality and personalization.",
        "required": False
    },
    "analytics": {
        "name": "Analytics",
        "description": "Cookies used to analyze site usage and improve performance.",
        "required": False
    },
    "marketing": {
        "name": "Marketing",
        "description": "Cookies used for marketing and advertising purposes.",
        "required": False
    },
    "third_party": {
        "name": "Third Party",
        "description": "Cookies set by third-party services and embedded content.",
        "required": False
    }
}

class CookieManager:
    def __init__(self):
        # Initialize session state for cookies
        if 'cookies' not in st.session_state:
            st.session_state.cookies = {}
        
        # Initialize session state for cookie preferences
        if 'cookie_preferences' not in st.session_state:
            st.session_state.cookie_preferences = {
                "necessary": True,  # Always required
                "functional": True,  # Default to enabled
                "analytics": False,
                "marketing": False,
                "third_party": False
            }
            
        # Initialize session state for consent status
        if 'cookie_consent' not in st.session_state:
            st.session_state.cookie_consent = {
                "status": None,  # None, "granted", "denied"
                "timestamp": None,
                "version": "1.0",
                "id": str(uuid.uuid4())
            }
            
        self.default_expiry_days = 30
        
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
        if options is None:
            options = {}
            
        # Check cookie consent and category
        if category != "necessary" and not self._check_category_consent(category):
            logger.info(f"Cookie '{name}' not set: user did not consent to {category} cookies")
            return {
                "success": False,
                "reason": f"User did not consent to {category} cookies"
            }
        
        # Set default options and add category information
        expiry = datetime.now() + timedelta(days=options.get('expires_days', self.default_expiry_days))
        st.session_state.cookies[name] = {
            'value': value,
            'expires': expiry.isoformat(),
            'path': options.get('path', '/'),
            'secure': options.get('secure', True),
            'httponly': options.get('httponly', True),
            'category': category,
            'created': datetime.now().isoformat(),
            'description': options.get('description', None)
        }
        
        logger.debug(f"Cookie '{name}' set in category '{category}'")
        return {
            "success": True,
            "cookie": name
        }

    def get_cookie_details(self, name: str) -> Optional[Dict]:
        """Get full cookie details if it exists, hasn't expired, and consent is given."""
        if name in st.session_state.cookies:
            cookie = st.session_state.cookies[name]
            
            # Check expiration
            expiry = datetime.fromisoformat(cookie['expires'])
            if datetime.now() >= expiry:
                del st.session_state.cookies[name]
                return None
                
            # Check consent for non-necessary cookies
            category = cookie.get('category', 'necessary')
            if category != 'necessary' and not self._check_category_consent(category):
                logger.debug(f"Access to cookie '{name}' blocked due to consent settings")
                return None
                
            return cookie
        return None

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
        if name in st.session_state.cookies:
            cookie = st.session_state.cookies[name]
            
            # Check consent for non-necessary cookies
            category = cookie.get('category', 'necessary')
            if category != 'necessary' and not self._check_category_consent(category):
                logger.debug(f"Extension of cookie '{name}' blocked due to consent settings")
                return False
                
            days = days or self.default_expiry_days
            expiry = datetime.now() + timedelta(days=days)
            cookie['expires'] = expiry.isoformat()
            logger.debug(f"Cookie '{name}' expiry extended to {expiry.isoformat()}")
            return True
        return False

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
            'expires_days': expires_days,
            'description': description
        }
        return self.set_cookie_with_options(name, value, category, options)

    def get_cookie(self, name: str) -> Optional[str]:
        """Get cookie value if it exists, hasn't expired, and consent allows access."""
        details = self.get_cookie_details(name)
        return details['value'] if details else None

    def delete_cookie(self, name: str) -> None:
        """Delete a cookie if it exists."""
        if name in st.session_state.cookies:
            logger.debug(f"Cookie '{name}' deleted")
            del st.session_state.cookies[name]

    def get_all_cookies(self, include_details: bool = False) -> Dict:
        """
        Get all valid cookies for which consent has been given.
        
        Args:
            include_details: Whether to include full cookie details or just values
            
        Returns:
            Dict of cookies
        """
        valid_cookies = {}
        now = datetime.now()
        
        for name, cookie in st.session_state.cookies.items():
            # Check expiration
            expiry = datetime.fromisoformat(cookie['expires'])
            if now >= expiry:
                del st.session_state.cookies[name]
                continue
                
            # Check consent for non-necessary cookies
            category = cookie.get('category', 'necessary')
            if category != 'necessary' and not self._check_category_consent(category):
                continue
                
            valid_cookies[name] = cookie if include_details else cookie['value']
        
        return valid_cookies

    def get_cookies_by_category(self, category: str, include_details: bool = False) -> Dict:
        """
        Get all valid cookies belonging to a specific category.
        
        Args:
            category: Cookie category
            include_details: Whether to include full cookie details or just values
            
        Returns:
            Dict of cookies in the requested category
        """
        if not self._check_category_consent(category) and category != "necessary":
            return {}
            
        category_cookies = {}
        now = datetime.now()
        
        for name, cookie in st.session_state.cookies.items():
            # Check if cookie belongs to the requested category
            if cookie.get('category', 'necessary') != category:
                continue
                
            # Check expiration
            expiry = datetime.fromisoformat(cookie['expires'])
            if now >= expiry:
                del st.session_state.cookies[name]
                continue
                
            category_cookies[name] = cookie if include_details else cookie['value']
        
        return category_cookies

    def clear_all_cookies(self, exclude_necessary: bool = True) -> None:
        """
        Clear all cookies, optionally preserving necessary cookies.
        
        Args:
            exclude_necessary: Whether to preserve necessary cookies
        """
        if exclude_necessary:
            # Keep only necessary cookies
            necessary_cookies = {}
            for name, cookie in st.session_state.cookies.items():
                if cookie.get('category', "") == "necessary":
                    necessary_cookies[name] = cookie
            st.session_state.cookies = necessary_cookies
            logger.info("Cleared all non-necessary cookies")
        else:
            # Clear all cookies
            st.session_state.cookies = {}
            logger.info("Cleared all cookies")

    def clear_category(self, category: str) -> None:
        """
        Clear all cookies in a specific category.
        
        Args:
            category: Category of cookies to clear
        """
        if category == "necessary":
            logger.warning("Attempted to clear necessary cookies, operation denied")
            return
            
        # Keep cookies not in the specified category
        preserved_cookies = {}
        for name, cookie in st.session_state.cookies.items():
            if cookie.get('category', "") != category:
                preserved_cookies[name] = cookie
        
        st.session_state.cookies = preserved_cookies
        logger.info(f"Cleared all cookies in category '{category}'")

    def set_consent(self, status: str, preferences: Dict[str, bool] = None) -> Dict:
        """
        Set cookie consent status and preferences.
        
        Args:
            status: Consent status ("granted" or "denied")
            preferences: Dict of category preferences
            
        Returns:
            Dict with operation result
        """
        if status not in ["granted", "denied"]:
            return {
                "success": False,
                "reason": "Invalid consent status. Must be 'granted' or 'denied'."
            }
            
        # Update consent status
        st.session_state.cookie_consent["status"] = status
        st.session_state.cookie_consent["timestamp"] = datetime.now().isoformat()
        
        # Update preferences if provided
        if preferences:
            for category, enabled in preferences.items():
                if category in st.session_state.cookie_preferences:
                    # Don't allow disabling necessary cookies
                    if category == "necessary":
                        continue
                    st.session_state.cookie_preferences[category] = enabled
        
        # If consent is denied, clear non-necessary cookies
        if status == "denied":
            self.clear_all_cookies(exclude_necessary=True)
        
        logger.info(f"Cookie consent set to '{status}' with preferences: {st.session_state.cookie_preferences}")
        return {
            "success": True,
            "consent": st.session_state.cookie_consent,
            "preferences": st.session_state.cookie_preferences
        }

    def get_consent_status(self) -> Dict:
        """
        Get current consent status and preferences.
        
        Returns:
            Dict with consent status information
        """
        return {
            "consent": st.session_state.cookie_consent,
            "preferences": st.session_state.cookie_preferences
        }

    def has_consent(self) -> bool:
        """
        Check if user has given cookie consent.
        
        Returns:
            True if consent has been granted, False otherwise
        """
        return st.session_state.cookie_consent["status"] == "granted"

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
            "consent_id": st.session_state.cookie_consent.get("id"),
            "status": st.session_state.cookie_consent.get("status"),
            "timestamp": st.session_state.cookie_consent.get("timestamp"),
            "version": st.session_state.cookie_consent.get("version"),
            "preferences": st.session_state.cookie_preferences,
            "cookies": {
                "necessary": len(self.get_cookies_by_category("necessary")),
                "functional": len(self.get_cookies_by_category("functional")),
                "analytics": len(self.get_cookies_by_category("analytics")),
                "marketing": len(self.get_cookies_by_category("marketing")),
                "third_party": len(self.get_cookies_by_category("third_party"))
            },
            "user_agent": "Streamlit"  # Would be actual user agent in a real web app
        }
        
    def _check_category_consent(self, category: str) -> bool:
        """
        Check if consent has been given for a specific cookie category.
        
        Args:
            category: Cookie category to check
            
        Returns:
            True if consent given or category is necessary, False otherwise
        """
        # Necessary cookies are always allowed
        if category == "necessary":
            return True
            
        # Check if user has given general consent
        if st.session_state.cookie_consent["status"] != "granted":
            return False
            
        # Check specific category preference
        return st.session_state.cookie_preferences.get(category, False)
