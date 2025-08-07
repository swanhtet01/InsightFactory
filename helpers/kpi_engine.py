"""
KPI computation engine for tyre production data.
"""
import pandas as pd
import numpy as np
from datetime import datetime

class KPIAgent:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize KPI Agent with the dataframe to be analyzed.
        Args:
            df (pd.DataFrame): The production data.
        """
        self.df = df.copy()
        self.metrics_history = []
        self.kpis = {}

    def engineer_features(self):
        """Add engineered features for advanced analytics."""
        if self.df.empty:
            return

        try:
            if 'date' in self.df.columns:
                self.df['hour_of_day'] = pd.to_datetime(self.df['date']).dt.hour
                self.df['day_of_week'] = pd.to_datetime(self.df['date']).dt.dayofweek
                self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)
            
            if 'quantity' in self.df.columns and 'target' in self.df.columns:
                # Use .loc to avoid SettingWithCopyWarning
                self.df.loc[:, 'output_efficiency'] = self.df['quantity'] / self.df['target']
                self.df.loc[:, 'output_variance'] = self.df['quantity'] - self.df['target']
            
            if 'a_grade' in self.df.columns and 'b_grade' in self.df.columns:
                self.df.loc[:, 'total_production'] = self.df['a_grade'] + self.df['b_grade']
                self.df.loc[:, 'quality_score'] = self.df['a_grade'] / self.df['total_production']
            
            numeric_cols = self.df.select_dtypes(include=np.number).columns
            for col in numeric_cols:
                self.df.loc[:, f'{col}_ma7'] = self.df[col].rolling(window=7).mean()
                self.df.loc[:, f'{col}_ma30'] = self.df[col].rolling(window=30).mean()

        except Exception as e:
            print(f"Error engineering features: {e}")

    def compute_kpis(self):
        """
        Compute key manufacturing KPIs from the dataframe.
        """
        if self.df.empty:
            self.kpis = {
                'oee': 0, 'fpy': 0, 'quality_rate': 0, 'scrap_rate': 0,
                'production': 0, 'target': 0, 'target_achievement': 0
            }
            return

        self.engineer_features()
        
        kpis = {}
        kpis['oee'] = self.df['oee'].mean() if 'oee' in self.df.columns else 0
        kpis['fpy'] = self.df['fpy'].mean() if 'fpy' in self.df.columns else 0
        kpis['production'] = self.df['quantity'].sum() if 'quantity' in self.df.columns else 0
        kpis['target'] = self.df['target'].sum() if 'target' in self.df.columns else 0
        kpis['target_achievement'] = (kpis['production'] / kpis['target'] * 100) if kpis['target'] > 0 else 0
        
        if 'a_grade' in self.df.columns and 'b_grade' in self.df.columns:
            total_graded = self.df['a_grade'].sum() + self.df['b_grade'].sum()
            kpis['quality_rate'] = (self.df['a_grade'].sum() / total_graded * 100) if total_graded > 0 else 0
        else:
            kpis['quality_rate'] = 0
            
        kpis['scrap_rate'] = (self.df['scrap'].sum() / kpis['production'] * 100) if 'scrap' in self.df.columns and kpis['production'] > 0 else 0
        
        self.kpis = kpis
        self.metrics_history.append({'timestamp': datetime.now(), 'metrics': self.kpis})

    def summary(self) -> str:
        """
        Generates a text summary of the computed KPIs.
        """
        if not self.kpis:
            self.compute_kpis()

        summary_str = (
            f"Key Performance Indicators:\n"
            f"---------------------------\n"
            f"Overall Equipment Effectiveness (OEE): {self.kpis.get('oee', 0):.2f}%\n"
            f"First Pass Yield (FPY): {self.kpis.get('fpy', 0):.2f}%\n"
            f"Total Production: {self.kpis.get('production', 0):,.0f} units\n"
            f"Target Achievement: {self.kpis.get('target_achievement', 0):.2f}%\n"
            f"A-Grade Quality Rate: {self.kpis.get('quality_rate', 0):.2f}%\n"
            f"Scrap Rate: {self.kpis.get('scrap_rate', 0):.2f}%\n"
            f"---------------------------"
        )
        return summary_str
