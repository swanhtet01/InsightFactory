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
- Executive dashboard payload exported to `reports/latest_dashboard.json` for lightweight web clients
- Dashboard payload includes freshness scoring so operations know when KPIs need a refresh
- HTML summary automatically includes the latest run history snapshot so audits have context without opening Streamlit
- Each run is appended to `reports/run_history.csv` so dashboards can trend KPIs, claims, and document throughput over time
- Automatic data intake profiling captures file counts, unreadable files, extension mix, volume, and detected granularities for every run
- Drive sync snapshots capture per-folder file counts, contributors, and recent changes in `reports/latest_sources.json` so multi-plant coverage is transparent
- Run metadata (duration, files processed, generated reports) is captured alongside analytics for auditable operations
- Continuous improvement engine analyzes run history to surface KPI/claim/document trends, alerts, and volatility warnings for proactive action
- Forecast engine projects KPI trajectories and target attainment windows for forward-looking planning
- Health scorecard synthesizes KPI, claim, document, and data intake context into an overall readiness score
- Preflight readiness command validates environment configuration, dependencies, and report artifacts (writes `preflight_status.json`)
- AI research layer produces continuous improvement plans and integration steps for CopilotKit and Tongyi DeepResearch, including live API hand-offs when credentials are provided
- Autonomous operations planner recommends immediate actions, automation opportunities, and agent readiness so the system can self-steer
- PDF parsing is optional; install `pdfminer.six` if your Drive contains PDFs
- Unified pipeline runner coordinates KPI, claim, and document processing for easy reuse
- Automatically derives Overall Equipment Effectiveness (OEE) and first-pass yield (FPY) when raw production columns are present

## Quickstart

1. Create and activate a virtual environment (recommended).
2. Install all project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   The suite now depends on FastAPI for the REST gateway alongside the
   Streamlit dashboards and analytics helpers, so installing the full
   requirements set keeps both interfaces working and ensures the test
   suite imports succeed.

3. Copy `.env.example` to `.env` and populate the Google Drive, OpenAI,
   CopilotKit, and Tongyi settings required for your deployment.
4. Validate the setup with `python cli.py preflight --json` to ensure
   credentials, dependencies, and report directories are ready.
5. Run the unified CLI to sync data, execute pipelines, or launch services (details below).

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
2. Provide Google Drive API credentials (a service-account JSON is recommended for headless runs). Save the file as `credentials.json` or point `GOOGLE_CREDENTIALS_FILE`/`GOOGLE_APPLICATION_CREDENTIALS` to the location. If you need to impersonate a Workspace user, set `GOOGLE_IMPERSONATE_SUBJECT` in `.env`.
3. Validate the environment with `python cli.py preflight --json` to confirm dependencies, credentials, and report directories are ready before running workloads. The Drive helper persists OAuth tokens to `GOOGLE_TOKEN_FILE` (default `token.json`) so repeat syncs run without reauthentication.
4. Run the full pipeline once via the CLI or module entrypoint: `python cli.py pipeline data` (defaults to the `data/` directory). You can still call the module directly with `python -m helpers.pipeline_runner <path> [<path> ...]` when you need fine-grained control.
5. Start the Drive watcher through the CLI (`python cli.py watch`) or directly with `python helpers/drive_watcher.py`. The watcher now performs an optional initial sync (`--sync-on-start / --no-sync-on-start`), automatically retries when Google Drive throttles requests, and keeps polling on transient failures. The `--run-once` flag triggers a single sync + pipeline pass for smoke tests.
6. Run the app: `python cli.py dashboard` (wraps `streamlit run app.py` with sensible defaults).
7. Start on the **🚀 InsightFactory Control Center** home page to confirm the latest run status, system health, recent history, and quick navigation to deeper dashboards.
   The freshness banner highlights when analytics are stale and need a rerun.
8. Visit the **🏠 Executive Overview** page for a curated leadership view of hero metrics, trend charts, health signals, and next best actions.
9. Visit the **📊 Operations Command Center** page to review run cadence, trend charts, and AI-driven action plans across plants. A new Files Profiled metric highlights ingestion health.
10. Open the **📁 Pipeline Summary** page to inspect the latest KPI, claim, document, and data intake metrics alongside integration telemetry.
11. Visit the **Autonomy Plan** tab inside the Pipeline Summary to review immediate actions, automation opportunities, and the status of the autonomous agents orchestrating the pipelines.
12. Use the **Data Intake** tab inside the Pipeline Summary to explore file profiling, detected granularities, per-source coverage, run duration, and generated report artifacts.
13. All analytics are auto-updated from your Drive folders with results stored in `reports/` (JSON, HTML, CSV history, document extracts).

## Command-line Orchestration

Use the new `cli.py` control center to manage pipelines, syncing, and services without remembering individual module paths:

```bash
# Sync Drive folders configured in GOOGLE_DRIVE_FOLDER_IDS
python cli.py sync

# Validate environment configuration and generated artifacts
python cli.py preflight --json

# Run the analytics pipeline against the ./data directory (default)
python cli.py pipeline

# Watch Drive for changes, running the pipeline whenever new files appear
python cli.py watch

# Launch the FastAPI gateway and Streamlit dashboard
python cli.py serve-api --port 8080
python cli.py dashboard

# Check which artifacts were produced during the last run
python cli.py status
```

Flags such as `--folder` allow you to override Drive folders at runtime, while `--run-once` on `watch` performs a single sync + pipeline loop for staging smoke tests. All commands respect the configured `REPORTS_DIR`, so artifacts stay aligned with the API and dashboards.

## REST API
- Launch the FastAPI service with `uvicorn api:app --reload` to expose read-only ERP-friendly endpoints.
- Secure requests by setting `INSIGHT_API_KEY` (required) and optionally `API_ALLOWED_ORIGINS`/`REPORTS_DIR` via environment variables or `.env`.
- `GET /api/summary` returns the latest unified pipeline JSON summary, while `GET /api/run-history?limit=10` streams historical runs for dashboards.
- `GET /api/insights` bundles AI research notes, performance forecasts, the system-health scorecard, and the autonomous operations plan; `GET /api/report/html` serves the rendered report snapshot for compliance archives.
- `GET /api/dashboard` returns the curated executive dashboard payload for lightweight portals or CopilotKit extensions.

## Dashboards
- **🚀 InsightFactory Control Center** (home) consolidates the latest run status, system health, run history, and quick navigation links into one launchpad.
- **🏠 Executive Overview** provides hero metrics, run-to-run trends, health signals, data intake status, and next best actions in a single glance.
- **📊 Operations Command Center** highlights multi-run trends, production throughput, claims exposure, and recommended next steps driven by the AI research planner.
- **📁 Pipeline Summary** provides a drill-down into the most recent run, including metric tables, charts, the health scorecard, run history, continuous-improvement insights, the autonomous operations plan, and raw HTML exports for compliance snapshots.
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

## Architecture & Strategic Planning
- Review the [System Blueprint](docs/architecture/system_blueprint.md) for an end-to-end view of the layered architecture, autonomous agent responsibilities, and the staged upgrade waves that push InsightFactory toward an elite-yet-lightweight ERP/MES fabric.
- Consult the [Expansion Roadmap](docs/roadmap.md) and [Team Backlog](docs/team_backlog.md) to coordinate execution, CI/CD hardening, and continuous improvement loops aligned with the blueprint.
