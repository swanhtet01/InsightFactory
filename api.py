"""
FastAPI backend for tyre production dashboard
"""
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pandas as pd
from helpers.data_processor import process_weekly_data, process_daily_data, process_monthly_data

app = FastAPI(
    title="Tyre Production Dashboard API",
    description="API backend for tyre production analytics and dashboard integration.",
    version="1.1.0",
    openapi_tags=[
        {"name": "dashboard", "description": "Dashboard and KPI data endpoints."},
        {"name": "health", "description": "Health and status endpoints."}
    ]
)

# Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == "YOUR_SECRET_API_KEY":  # Change this to a secure key
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API key")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yangontyre.com.mm"],  # Add your WordPress domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "message": "Welcome to the Tyre Production Dashboard API. See /docs for usage.",
        "endpoints": ["/api/health", "/api/dashboard-data"]
    }

@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "message": "Tyre dashboard API is running."}

@app.get("/api/dashboard-data", tags=["dashboard"])
async def get_dashboard_data(api_key: str = Depends(get_api_key)):
    import os
    # File paths
    weekly_file = 'data/Weekly Tyre 20225.xlsx'
    daily_file = 'data/Daily Pro; A,B,R Report .xlsx'
    monthly_file = 'data/1.  Tyre PD ; A.B.R ( 2025) year ).xlsx'
    missing = []
    for f in [weekly_file, daily_file, monthly_file]:
        if not os.path.exists(f):
            missing.append(f)
    if missing:
        raise HTTPException(status_code=404, detail={
            "error": "Missing data files",
            "missing_files": missing
        })
    try:
        # Process data
        weekly_data = process_weekly_data(weekly_file)
        daily_data = process_daily_data(daily_file)
        monthly_data = process_monthly_data(monthly_file)
        # Convert DataFrames to JSON serializable dicts
        def safe_to_dict(df):
            if isinstance(df, pd.DataFrame):
                return df.fillna('').to_dict(orient='records')
            return df
        return {
            "weekly": safe_to_dict(weekly_data),
            "daily": safe_to_dict(daily_data),
            "monthly": safe_to_dict(monthly_data),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Data processing error",
            "message": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
