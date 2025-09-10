# InsightFactory

A modern, robust KPI dashboard for tyre production analytics. All data is loaded from Google Drive and processed using specialized, modular agents for reliability and clarity.

## Key Features
- Google Drive integration (no upload widgets)
- Advanced analytics and anomaly detection
- Minimal, modern UI (only key KPIs and trends)
- Modular codebase: data loading, KPI engine, quality checker, and Drive sync are separated for maintainability
- Background watcher keeps local data synced with Drive (spreadsheets, images, and documents)
- Handles multiple data granularities; raw spreadsheets, claim forms, and image assets are stored for downstream analysis
- Automatic KPI computation after each sync with results stored in `reports/latest_kpis.csv`
- Claim spreadsheets summarized to `reports/latest_claim_metrics.csv`
- Document text extracted to `reports/latest_docs.txt` for search and review

## Folder Structure
- `app.py` — Main entry point
- `pages/` — Streamlit multipage app
- `helpers/` — Specialized modules (data_loader, kpi_engine, quality_checker, drive_sync, document_processor, claims_pipeline)
- `data/` — Only current, used data files (`images/`, `documents/` subfolders)
- `static/` — Static assets (e.g., logo)
- `reports/` — Exported reports
- `config/` — Configuration files

## Usage
1. Place your Google Drive credentials in `credentials.json`.
2. Start the Drive watcher: `python helpers/drive_watcher.py` (runs continuously and computes KPIs, claim metrics, and document extracts)
3. Run the app: `streamlit run app.py`
4. All analytics are auto-updated from your Drive folder with results stored in `reports/`.

## Maintenance
- Only keep files and modules listed above. Remove legacy/unused files for clarity.
- For help, contact your analytics team.
- Continuous integration runs `python -m py_compile` on key helpers for reliability (see `.github/workflows/ci.yml`).
