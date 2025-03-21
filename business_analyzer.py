
"""
Business Analysis Module for Email Analytics
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta

class BusinessAnalyzer:
    def __init__(self):
        self.metrics = {}
        
    def analyze_engagement(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze email engagement metrics"""
        metrics = {
            'total_interactions': len(df),
            'active_contacts': df['from'].nunique() + df['to'].nunique(),
            'avg_response_time': df.groupby('thread_id')['date'].diff().mean().total_seconds() / 3600 if not df.empty else 0,
            'engagement_rate': (df['is_sent'].sum() / len(df)) * 100 if not df.empty else 0
        }
        return metrics
        
    def calculate_business_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate key business metrics"""
        metrics = {
            'communication_volume': {
                'daily': df.groupby(df['date'].dt.date).size().mean(),
                'weekly': df.groupby(pd.Grouper(key='date', freq='W')).size().mean(),
                'monthly': df.groupby(pd.Grouper(key='date', freq='M')).size().mean()
            },
            'response_patterns': {
                'avg_response_time': df.groupby('thread_id')['date'].diff().mean().total_seconds() / 3600 if not df.empty else 0,
                'response_rate': (df['is_sent'].sum() / len(df)) * 100 if not df.empty else 0
            },
            'domain_analysis': self._analyze_domains(df),
            'peak_activity': self._get_peak_activity(df)
        }
        return metrics
    
    def _analyze_domains(self, df: pd.DataFrame) -> Dict[str, int]:
        """Analyze email domains"""
        domains = df['from'].apply(lambda x: x.split('@')[1] if '@' in str(x) else 'unknown')
        return domains.value_counts().head(10).to_dict()
        
    def _get_peak_activity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get peak activity times"""
        if df.empty:
            return {'hour': 0, 'day': 'Unknown'}
            
        peak_hour = df['date'].dt.hour.mode().iloc[0]
        peak_day = df['date'].dt.day_name().mode().iloc[0]
        return {'hour': peak_hour, 'day': peak_day}
