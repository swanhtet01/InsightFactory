import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
PROCESSED_DATA_PATH = "data/processed_data.json"
REPORTS_PATH = "reports/exported_pdfs/"

# Translations for multilingual support
TRANSLATIONS = {
    'en': {
        'loading': 'Loading production data...',
        'no_data': 'No valid data found.',
        'kpi_titles': {
            'oee': 'Overall Equipment Effectiveness (OEE)',
            'fpy': 'First Pass Yield (FPY)',
            'quality_rate': 'Quality Rate',
            'scrap_rate': 'Scrap Rate',
            'production': 'Total Production',
            'target': 'Production Target',
            'target_achievement': 'Target Achievement'
        },
        'units': {
            'percentage': '%',
            'pieces': 'pcs',
            'hours': 'hrs'
        }
    }
}
