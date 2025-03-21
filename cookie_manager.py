
from typing import Dict, Optional
import streamlit as st
from datetime import datetime, timedelta
import json

class CookieManager:
    def __init__(self):
        if 'cookies' not in st.session_state:
            st.session_state.cookies = {}

    def set_cookie(self, name: str, value: str, expires_days: int = 30) -> None:
        """Set a cookie with expiration."""
        expiry = datetime.now() + timedelta(days=expires_days)
        st.session_state.cookies[name] = {
            'value': value,
            'expires': expiry.isoformat()
        }

    def get_cookie(self, name: str) -> Optional[str]:
        """Get cookie value if it exists and hasn't expired."""
        if name in st.session_state.cookies:
            cookie = st.session_state.cookies[name]
            expiry = datetime.fromisoformat(cookie['expires'])
            if datetime.now() < expiry:
                return cookie['value']
            else:
                del st.session_state.cookies[name]
        return None

    def delete_cookie(self, name: str) -> None:
        """Delete a cookie if it exists."""
        if name in st.session_state.cookies:
            del st.session_state.cookies[name]

    def get_all_cookies(self) -> Dict:
        """Get all valid cookies."""
        valid_cookies = {}
        now = datetime.now()
        for name, cookie in st.session_state.cookies.items():
            expiry = datetime.fromisoformat(cookie['expires'])
            if now < expiry:
                valid_cookies[name] = cookie['value']
        return valid_cookies

    def clear_all_cookies(self) -> None:
        """Clear all cookies."""
        st.session_state.cookies = {}
