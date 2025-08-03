def check_quality(df):
    """Return a list of data quality issues for the given DataFrame."""
    issues = []
    if df.duplicated(subset=['date', 'tyre_size']).any():
        issues.append("Duplicate rows detected (same date and tyre size). Please check your data files.")
    if 'quantity' in df.columns and (df['quantity'] < 0).any():
        issues.append("Negative production quantities found.")
    if 'oee' in df.columns and ((df['oee'] > 100).any() or (df['oee'] < 0).any()):
        issues.append("OEE values out of range (should be 0-100).")
    if 'fpy' in df.columns and ((df['fpy'] > 100).any() or (df['fpy'] < 0).any()):
        issues.append("FPY values out of range (should be 0-100).")
    return issues
