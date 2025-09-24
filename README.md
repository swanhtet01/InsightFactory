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
- Document word counts tracked in `reports/latest_doc_metrics.csv` for quick sizing insights
- All pipeline outputs aggregated into `reports/latest_summary.json` for downstream systems
- Summary also rendered to `reports/latest_summary.html` for quick human review
- HTML summary automatically includes the latest run history snapshot so audits have context without opening Streamlit
- Each run is appended to `reports/run_history.csv` so dashboards can trend KPIs, claims, and document throughput over time
- Automatic data intake profiling captures file counts, unreadable files, extension mix, volume, and detected granularities for every run
- Drive sync snapshots capture per-folder file counts, contributors, and recent changes in `reports/latest_sources.json` so multi-plant coverage is transparent
- Run metadata (duration, files processed, generated reports) is captured alongside analytics for auditable operations
- Continuous improvement engine analyzes run history to surface KPI/claim/document trends, alerts, and volatility warnings for proactive action
- Forecast engine projects KPI trajectories and target attainment windows for forward-looking planning
- AI research layer produces continuous improvement plans and integration steps for CopilotKit and Tongyi DeepResearch, including live API hand-offs when credentials are provided
- Autonomous operations planner recommends immediate actions, automation opportunities, and agent readiness so the system can self-steer
- PDF parsing is optional; install `pdfminer.six` if your Drive contains PDFs
- Unified pipeline runner coordinates KPI, claim, and document processing for easy reuse
- Automatically derives Overall Equipment Effectiveness (OEE) and first-pass yield (FPY) when raw production columns are present

## Folder Structure
- `app.py` — Main entry point
- `pages/` — Streamlit multipage app
- `helpers/` — Specialized modules (data_loader, kpi_engine, quality_checker, drive_sync, document_processor, claims_pipeline)
- `data/` — Only current, used data files (`images/`, `documents/` subfolders)
- `static/` — Static assets (e.g., logo)
- `reports/` — Exported reports
- `config/` — Configuration files

## Usage
1. Copy `.env.example` to `.env` and fill in any API keys (OpenAI, Gemini, GitHub) and `GOOGLE_DRIVE_FOLDER_IDS` (comma-separated list of folder IDs). Optionally map friendly plant names via `GOOGLE_DRIVE_FOLDER_ALIASES` using `folder-id=Label` pairs.
2. Download Google API credentials and save as `credentials.json` (not tracked; see `credentials_sample.json` for format).
3. Run the full pipeline once: `python -m helpers.pipeline_runner <path> [<path> ...]` where each path can be a file or a directory; directories are scanned recursively. The Drive watcher can also trigger it automatically.
4. Start the Drive watcher: `python helpers/drive_watcher.py` (runs continuously and computes KPIs, claim metrics, and document extracts for all configured folders)
5. Run the app: `streamlit run app.py`
6. Visit the **📊 Operations Command Center** page to review run cadence, trend charts, and AI-driven action plans across plants. A new Files Profiled metric highlights ingestion health.
7. Open the **📁 Pipeline Summary** page to inspect the latest KPI, claim, document, and data intake metrics alongside integration telemetry.
8. Visit the **Autonomy Plan** tab inside the Pipeline Summary to review immediate actions, automation opportunities, and the status of the autonomous agents orchestrating the pipelines.
9. Use the **Data Intake** tab inside the Pipeline Summary to explore file profiling, detected granularities, per-source coverage, run duration, and generated report artifacts.
10. All analytics are auto-updated from your Drive folders with results stored in `reports/` (JSON, HTML, CSV history, document extracts).

## Dashboards
- **📊 Operations Command Center** highlights multi-run trends, production throughput, claims exposure, and recommended next steps driven by the AI research planner.
- **📁 Pipeline Summary** provides a drill-down into the most recent run, including metric tables, charts, run history, continuous-improvement insights, the autonomous operations plan, and raw HTML exports for compliance snapshots.
- **🤖 AI Operations Copilot** (existing page) surfaces CopilotKit and DeepResearch readiness plus the recommended enablement roadmap.

## Testing
- Install the dependencies from `requirements.txt` (a virtual environment is recommended).
- Run `pytest` from the repository root to execute the end-to-end regression suite. The included
  `pytest.ini` ensures the `helpers` package resolves correctly even when the `pytest` console
  script is used, and optional OCR assertions are skipped automatically when Tesseract is not
  available.

## AI Copilot & Research Integrations
- Set `COPILOTKIT_API_BASE` and `COPILOTKIT_API_KEY` to stream data to [CopilotKit](https://github.com/CopilotKit/CopilotKit) copilots. Override the relative REST path with `COPILOTKIT_INSIGHTS_PATH` if your deployment does not expose `/api/v1/insights`.
- Set `DEEPRESEARCH_API_BASE` and `DEEPRESEARCH_API_KEY` to orchestrate Tongyi [DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) studies. Customize the endpoint via `DEEPRESEARCH_RESEARCH_PATH` if required.
- The pipeline summary now embeds AI observations, recommended actions, integration API responses, and next integration steps in `reports/latest_summary.json`, the HTML report, and the Streamlit **Pipeline Summary**/**AI Operations Copilot** pages.
- Use these connectors to auto-generate shift handover summaries, claim triage, and deep investigative narratives without hard-coding API calls into the analytics core. Integration errors or disabled states are surfaced in the UI so you can troubleshoot credentials quickly.

## Maintenance
- Only keep files and modules listed above. Remove legacy/unused files for clarity.
- For help, contact your analytics team.
- Continuous integration runs `python -m py_compile` and the unit test suite for reliability (see `.github/workflows/ci.yml`).
