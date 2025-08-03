"""
KPI computation engine for tyre production data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class KPIAgent:
    def __init__(self):
        """Initialize KPI Agent"""
        self.metrics_history = []
        
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add engineered features for advanced analytics."""
        try:
            df = df.copy()
            if 'date' in df.columns:
                df['hour_of_day'] = df['date'].dt.hour
                df['day_of_week'] = df['date'].dt.dayofweek
                df['is_weekend'] = df['date'].dt.weekday.isin([5, 6]).astype(int)
            
            # Production efficiency features
            if 'quantity' in df.columns and 'target' in df.columns:
                df['output_efficiency'] = df['quantity'] / df['target']
                df['output_variance'] = df['quantity'] - df['target']
            
            # Quality features
            if 'a_grade' in df.columns and 'b_grade' in df.columns:
                df['total_production'] = df['a_grade'] + df['b_grade']
                df['quality_score'] = df['a_grade'] / df['total_production']
            
            # Moving averages and trends
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                df[f'{col}_ma7'] = df[col].rolling(window=7).mean()
                df[f'{col}_ma30'] = df[col].rolling(window=30).mean()
                df[f'{col}_trend'] = df[col].diff()
            
            return df
        except Exception as e:
            print(f"Error engineering features: {e}")
            return df
            
    def compute_kpis(self, df: pd.DataFrame) -> dict:
        """
        Compute key manufacturing KPIs from cleaned dataframe.
        Args:
            df (pd.DataFrame): Cleaned production data.
        Returns:
            dict: KPI metrics with current and historical trends.
        """
        if df.empty:
            return {
                'oee': 0,
                'fpy': 0,
                'quality_rate': 0,
                'scrap_rate': 0,
                'production': 0,
                'target': 0,
                'target_achievement': 0
            }
            
        # Add engineered features
        df = self.engineer_features(df)
        
        # Calculate basic KPIs
        kpis = {}
        kpis['oee'] = df['oee'].mean() if 'oee' in df.columns else 0
        kpis['fpy'] = df['fpy'].mean() if 'fpy' in df.columns else 0
        kpis['production'] = df['quantity'].sum() if 'quantity' in df.columns else 0
        kpis['target'] = df['target'].sum() if 'target' in df.columns else 0
        kpis['target_achievement'] = (kpis['production'] / kpis['target'] * 100) if kpis['target'] > 0 else 0
        
        if 'a_grade' in df.columns and 'b_grade' in df.columns:
            total_graded = df['a_grade'].sum() + df['b_grade'].sum()
            kpis['quality_rate'] = (df['a_grade'].sum() / total_graded * 100) if total_graded > 0 else 0
        else:
            kpis['quality_rate'] = 0
            
        kpis['scrap_rate'] = (df['scrap'].sum() / kpis['production'] * 100) if 'scrap' in df.columns and kpis['production'] > 0 else 0
        
        # Store metrics history
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': kpis
        })
        
        return kpis
