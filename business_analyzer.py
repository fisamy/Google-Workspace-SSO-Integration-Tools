
"""
Business Analysis Module for Email Analytics
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

class BusinessAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def get_business_metrics(self) -> Dict[str, Any]:
        """Calculate business-related metrics from email data."""
        metrics = {
            "communication_volume": self._analyze_communication_volume(),
            "response_efficiency": self._analyze_response_efficiency(),
            "contact_engagement": self._analyze_contact_engagement(),
            "time_distribution": self._analyze_time_distribution(),
            "domain_analysis": self._analyze_domain_distribution()
        }
        return metrics
    
    def _analyze_communication_volume(self) -> Dict[str, Any]:
        """Analyze email communication volume trends."""
        if self.df.empty:
            return {}
            
        # Group by date and calculate daily metrics
        daily_stats = self.df.groupby(self.df['date'].dt.date).agg({
            'id': 'count',
            'is_sent': ['sum', 'size'],
            'word_count': 'mean'
        }).reset_index()
        
        return {
            "avg_daily_volume": daily_stats['id']['count'].mean(),
            "peak_day_volume": daily_stats['id']['count'].max(),
            "avg_word_count": self.df['word_count'].mean(),
            "sent_received_ratio": (self.df['is_sent'].sum() / len(self.df)) * 100
        }
    
    def _analyze_response_efficiency(self) -> Dict[str, Any]:
        """Analyze email response patterns and efficiency."""
        if self.df.empty:
            return {}
            
        # Group emails by thread
        threads = self.df.groupby('thread_id')
        
        response_times = []
        for _, thread in threads:
            if len(thread) > 1:
                thread_sorted = thread.sort_values('date')
                response_times.extend([
                    (later - earlier).total_seconds() / 3600  # Convert to hours
                    for earlier, later in zip(thread_sorted['date'], thread_sorted['date'][1:])
                ])
        
        if response_times:
            return {
                "avg_response_time": np.mean(response_times),
                "median_response_time": np.median(response_times),
                "response_rate": (len(response_times) / len(threads)) * 100
            }
        return {}
    
    def _analyze_contact_engagement(self) -> Dict[str, Any]:
        """Analyze engagement with contacts."""
        if self.df.empty:
            return {}
            
        # Analyze unique contacts and interaction frequency
        contacts = pd.concat([
            self.df['from'].value_counts(),
            self.df['to'].value_counts()
        ]).reset_index()
        contacts.columns = ['email', 'count']
        contacts = contacts.groupby('email')['count'].sum()
        
        return {
            "total_contacts": len(contacts),
            "top_contacts": contacts.nlargest(10).to_dict(),
            "avg_interactions_per_contact": contacts.mean()
        }
    
    def _analyze_time_distribution(self) -> Dict[str, Any]:
        """Analyze email timing patterns."""
        if self.df.empty:
            return {}
            
        hour_dist = self.df['date'].dt.hour.value_counts().sort_index()
        day_dist = self.df['date'].dt.day_name().value_counts()
        
        return {
            "peak_hours": hour_dist.nlargest(3).index.tolist(),
            "peak_days": day_dist.nlargest(3).index.tolist(),
            "hourly_distribution": hour_dist.to_dict(),
            "daily_distribution": day_dist.to_dict()
        }
    
    def _analyze_domain_distribution(self) -> Dict[str, Any]:
        """Analyze email domain distribution."""
        if self.df.empty:
            return {}
            
        def extract_domain(email: str) -> str:
            try:
                return email.split('@')[1]
            except:
                return 'unknown'
        
        domains = pd.concat([
            self.df['from'].apply(extract_domain).value_counts(),
            self.df['to'].apply(extract_domain).value_counts()
        ]).reset_index()
        domains.columns = ['domain', 'count']
        domains = domains.groupby('domain')['count'].sum()
        
        return {
            "top_domains": domains.nlargest(10).to_dict(),
            "unique_domains": len(domains),
            "domain_distribution": domains.to_dict()
        }
    
    def generate_business_insights(self) -> List[str]:
        """Generate key business insights from the metrics."""
        metrics = self.get_business_metrics()
        insights = []
        
        # Communication volume insights
        if "communication_volume" in metrics and metrics["communication_volume"]:
            vol = metrics["communication_volume"]
            insights.append(f"Average daily email volume: {vol['avg_daily_volume']:.1f}")
            insights.append(f"Sent/Received ratio: {vol['sent_received_ratio']:.1f}%")
        
        # Response efficiency insights
        if "response_efficiency" in metrics and metrics["response_efficiency"]:
            eff = metrics["response_efficiency"]
            insights.append(f"Average response time: {eff['avg_response_time']:.1f} hours")
            insights.append(f"Response rate: {eff['response_rate']:.1f}%")
        
        # Time distribution insights
        if "time_distribution" in metrics and metrics["time_distribution"]:
            time_dist = metrics["time_distribution"]
            insights.append(f"Peak email hours: {', '.join(map(str, time_dist['peak_hours']))}")
            insights.append(f"Most active days: {', '.join(time_dist['peak_days'][:2])}")
        
        return insights

