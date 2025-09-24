import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
INSIGHT_API_KEY = os.getenv("INSIGHT_API_KEY", "")
INSIGHT_API_KEY_HEADER = os.getenv("INSIGHT_API_KEY_HEADER", "X-API-Key")

_origins = [origin.strip() for origin in os.getenv("API_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
API_ALLOWED_ORIGINS = _origins or ["*"]

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports")).expanduser().resolve()

# Support multiple Drive folders via comma-separated environment variable.
GOOGLE_DRIVE_FOLDER_IDS = [
    fid.strip()
    for fid in os.getenv("GOOGLE_DRIVE_FOLDER_IDS", "").split(",")
    if fid.strip()
]
if not GOOGLE_DRIVE_FOLDER_IDS:
    fallback = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if fallback:
        GOOGLE_DRIVE_FOLDER_IDS = [fallback]


def _parse_folder_aliases(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for chunk in raw.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        mapping[key] = value
    return mapping


GOOGLE_DRIVE_FOLDER_ALIASES = _parse_folder_aliases(
    os.getenv("GOOGLE_DRIVE_FOLDER_ALIASES", "")
)


def resolve_drive_folder_label(folder_id: str) -> str:
    """Return a human-readable label for a Drive folder."""

    return GOOGLE_DRIVE_FOLDER_ALIASES.get(folder_id, folder_id)
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
