"""
Configuration settings for the application
"""

# Email Configuration
SMTP_CONFIG = {
    "server": "smtp.gmail.com",  # Update with your SMTP server
    "port": 587,
    "username": "",  # Add your email
    "password": "",  # Add your app password
}

# Report Settings
REPORT_CONFIG = {
    "daily_report_time": "18:00",  # 6 PM
    "weekly_report_day": "FRI",
    "monthly_report_day": "LAST",
    "recipients": [
        # Add email recipients
    ]
}

# Web Dashboard Settings
WEB_CONFIG = {
    "base_url": "https://yangontyre.com.mm",
    "dashboard_path": "/private/dashboard",
    "api_key": "",  # Add API key for authentication
}
