"""
KPI computation engine for tyre production data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def engineer_features(df):
    """Add engineered features for advanced analytics."""
    try:
        # Time-based features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['timestamp'].dt.weekday.isin([5, 6]).astype(int)
        
        # Production efficiency features
        if all(col in df.columns for col in ['actual_output', 'target_output']):
            df['output_efficiency'] = df['actual_output'] / df['target_output']
            df['output_variance'] = df['actual_output'] - df['target_output']
        
        # Quality features
        if 'defects' in df.columns and 'total_production' in df.columns:
            df['defect_rate'] = df['defects'] / df['total_production']
            df['quality_score'] = 1 - df['defect_rate']
        
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

def compute_kpis(df):
    """
    Compute key manufacturing KPIs from cleaned dataframe.
    Args:
        df (pd.DataFrame): Cleaned production data.
    Returns:
        dict: KPI metrics with current and historical trends.
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # Add engineered features
    df = engineer_features(df)
    
    # Initialize KPIs dictionary with nested structure
    kpis = {
        'production': {
            'total_output': 0,
            'hourly_rate': 0,
            'capacity_utilization': 0,
            'output_by_size': {},
            'output_by_type': {}
        },
        'quality': {
            'first_time_pass_rate': 0,
            'defect_rate': 0,
            'scrap_rate': 0,
            'rework_rate': 0,
            'uniformity_metrics': {},
            'compound_quality_index': 0
        },
        'efficiency': {
            'oee': 0,  # Overall Equipment Effectiveness
            'availability': 0,
            'performance_rate': 0,
            'quality_rate': 0,
            'cycle_time': 0,
            'setup_time': 0,
            'downtime': 0
        },
        'performance': {
            'energy_efficiency': 0,
            'material_utilization': 0,
            'labor_productivity': 0,
            'machine_utilization': 0
        },
        'historical': {
            'daily': {},
            'weekly': {},
            'monthly': {},
            'yearly': {}
        },
        'trends': {
            'production_trend': [],
            'quality_trend': [],
            'efficiency_trend': []
        },
        'aggregates': {
            'moving_averages': {},
            'running_totals': {},
            'variance_metrics': {}
        },
        '_metadata': {
            'computed_at': datetime.now().isoformat(),
            'data_sources': [],
            'validation_status': 'pending'
        }
    }
    
    # Find date column
    date_cols = df.select_dtypes(include=['datetime64']).columns
    if len(date_cols) > 0:
        date_col = date_cols[0]
        latest_date = df[date_col].max()
        kpis['latest_date'] = latest_date.strftime('%Y-%m-%d')
        
        # Calculate periods for comparison
        current_month = df[df[date_col].dt.month == latest_date.month]
        prev_month = df[df[date_col].dt.month == (latest_date - timedelta(days=30)).month]
        
        # Get weekly data
        current_week = df[df[date_col].dt.isocalendar().week == latest_date.isocalendar().week]
        prev_week = df[df[date_col].dt.isocalendar().week == (latest_date - timedelta(days=7)).isocalendar().week]
        
        # Latest day's data and yesterday
        latest_day = df[df[date_col].dt.date == latest_date.date()]
        yesterday = df[df[date_col].dt.date == (latest_date.date() - timedelta(days=1))]
    
    # Helper function to safely convert to numeric
    def to_numeric(series):
        if series is None:
            return None
        return pd.to_numeric(series, errors='coerce')
    
    # Try to be robust to missing columns
    def get(col):
        if col not in df.columns:
            return None
        return to_numeric(df[col])

    def calculate_period_kpis(period_df):
        """Calculate KPIs for a specific time period"""
        period_kpis = {}
        
        # Production Quantity
        for col in ['Production Quantity', 'Production_Quantity', 'Quantity', 'Output']:
            qty = get_from_df(period_df, col)
            if qty is not None and not qty.empty and np.nansum(qty) > 0:
                period_kpis['production'] = int(np.nansum(qty))
                break
        
        # Rejected/Defect Quantity
        for col in ['Rejected Quantity', 'Rejected_Quantity', 'Defects', 'Rejects']:
            rej = get_from_df(period_df, col)
            if rej is not None and not rej.empty and np.nansum(rej) > 0:
                period_kpis['rejected'] = int(np.nansum(rej))
                if 'production' in period_kpis:
                    period_kpis['reject_rate'] = (period_kpis['rejected'] / period_kpis['production'] * 100)
                break
        
        # Rework Quantity
        for col in ['Rework Quantity', 'Rework_Quantity', 'Rework']:
            rwk = get_from_df(period_df, col)
            if rwk is not None and not rwk.empty and np.nansum(rwk) > 0:
                period_kpis['rework'] = int(np.nansum(rwk))
                if 'production' in period_kpis:
                    period_kpis['rework_rate'] = (period_kpis['rework'] / period_kpis['production'] * 100)
                break
                
        # Calculate efficiency
        if 'production' in period_kpis:
            rejected = period_kpis.get('rejected', 0)
            rework = period_kpis.get('rework', 0)
            period_kpis['efficiency'] = (
                (period_kpis['production'] - rejected - rework) / 
                period_kpis['production'] * 100
            )
            period_kpis['first_pass_yield'] = (
                (period_kpis['production'] - rejected) / 
                period_kpis['production'] * 100
            )
            
        # Target achievement
        for col in ['Target', 'Plan', 'Goal']:
            target = get_from_df(period_df, col)
            if target is not None and not target.empty and np.nansum(target) > 0:
                period_kpis['target'] = int(np.nansum(target))
                if 'production' in period_kpis:
                    period_kpis['target_achievement'] = (
                        period_kpis['production'] / period_kpis['target'] * 100
                    )
                break
                
        return period_kpis
    
    def get_from_df(df, col):
        """Safely get column from DataFrame"""
        if col not in df.columns:
            return None
        return pd.to_numeric(df[col], errors='coerce')
    
    # Calculate KPIs for different time periods
    if len(date_cols) > 0:
        # Today/Latest and Yesterday
        today_kpis = calculate_period_kpis(latest_day)
        yesterday_kpis = calculate_period_kpis(yesterday)
        if today_kpis:
            kpis['today'] = today_kpis
        if yesterday_kpis:
            kpis['yesterday'] = yesterday_kpis
        
        # This Week
        week_kpis = calculate_period_kpis(current_week)
        if week_kpis:
            kpis['this_week'] = week_kpis
        
        # Previous Week (for comparison)
        prev_week_kpis = calculate_period_kpis(prev_week)
        if prev_week_kpis and week_kpis:
            for key in week_kpis:
                if key in prev_week_kpis:
                    change = ((week_kpis[key] - prev_week_kpis[key]) / prev_week_kpis[key] * 100)
                    kpis[f'week_{key}_change'] = change
        
        # This Month
        month_kpis = calculate_period_kpis(current_month)
        if month_kpis:
            kpis['this_month'] = month_kpis
            
        # Previous Month (for comparison)
        prev_month_kpis = calculate_period_kpis(prev_month)
        if prev_month_kpis and month_kpis:
            for key in month_kpis:
                if key in prev_month_kpis:
                    change = ((month_kpis[key] - prev_month_kpis[key]) / prev_month_kpis[key] * 100)
                    kpis[f'month_{key}_change'] = change
            
    # Rework Quantity
    for col in ['Rework Quantity', 'Rework_Quantity']:
        rwk_qty = get(col)
        if rwk_qty is not None and not rwk_qty.empty and np.nansum(rwk_qty) > 0:
            kpis['rework_quantity'] = int(np.nansum(rwk_qty))
            break
            
    # Scrap Quantity
    for col in ['Scrap Quantity', 'Scrap_Quantity']:
        scrap_qty = get(col)
        if scrap_qty is not None and not scrap_qty.empty and np.nansum(scrap_qty) > 0:
            kpis['scrap_quantity'] = int(np.nansum(scrap_qty))
            break
            
    # Downtime Duration
    for col in ['Downtime Duration', 'Downtime_Duration']:
        dt = get(col)
        if dt is not None and not dt.empty and np.nansum(dt) > 0:
            kpis['downtime_duration'] = float(np.nansum(dt))
            break
    # QC Passed/Failed
    if get('QC Passed') is not None:
        kpis['qc_passed'] = int(np.nansum(get('QC Passed')))
    if get('QC Failed') is not None:
        kpis['qc_failed'] = int(np.nansum(get('QC Failed')))
    # Yield
    if 'good_quantity' in kpis and 'total_production' in kpis and kpis['total_production'] > 0:
        kpis['yield'] = round(kpis['good_quantity'] / kpis['total_production'] * 100, 2)
    # Rejection Rate
    if 'rejected_quantity' in kpis and 'total_production' in kpis and kpis['total_production'] > 0:
        kpis['rejection_rate'] = round(kpis['rejected_quantity'] / kpis['total_production'] * 100, 2)
    # Rework Rate
    if 'rework_quantity' in kpis and 'total_production' in kpis and kpis['total_production'] > 0:
        kpis['rework_rate'] = round(kpis['rework_quantity'] / kpis['total_production'] * 100, 2)
    # Scrap Rate
    if 'scrap_quantity' in kpis and 'total_production' in kpis and kpis['total_production'] > 0:
        kpis['scrap_rate'] = round(kpis['scrap_quantity'] / kpis['total_production'] * 100, 2)
    # Average Spec/Actual Weight
    if get('Spec Weight') is not None:
        kpis['avg_spec_weight'] = float(np.nanmean(get('Spec Weight')))
    if get('Actual Weight') is not None:
        kpis['avg_actual_weight'] = float(np.nanmean(get('Actual Weight')))
    # Add more KPIs as needed
    return kpis
