
# 🧠 Insight Factory Assistant – Developer Brief for GitHub Copilot

## 🎯 Objective

Design and implement a production-ready, mobile-optimized web application that autonomously processes tyre production data (daily, weekly, monthly) from a shared Google Drive folder, computes key manufacturing KPIs, generates executive-level summaries using OpenAI GPT-4o, and presents these insights via interactive dashboards and downloadable reports.

---

## 📂 Input Data Types

- `.xlsx` Excel files from factory reports
- (Future) `.png` screenshots from Viber with structured tabular data (to be processed via OCR)

---

## 🧠 Functional Scope

### 1. Data Ingestion
- Upload interface for Excel files
- Google Drive sync module (auto-ingests new files)
- (Future) Image-to-text pipeline using Tesseract OCR

### 2. Data Cleaning (LLM-Augmented)
- GPT-4o-powered header normalization
- Multi-row header parsing
- Column mapping (Shift, Size, QC, Spec Weight, Actual Weight, etc.)

### 3. KPI Computation
- Total Production (per shift, per day)
- QC Pass Rate (QC/Total)
- Shift Performance (A/B/R)
- Weight Efficiency (Actual vs. Spec)
- Tyre Size-level productivity breakdown

### 4. Trend & Summary Engine
- 7/30/90-day rolling analysis
- Executive summaries via GPT-4o
- Anomaly detection and explanation prompts
- Director-level phrasing and logic

### 5. Reporting
- Streamlit interface for viewing insights
- PDF/HTML export via WeasyPrint
- Report cards with KPI metrics
- Visual trend charts via Plotly

### 6. History + Automation
- Store cleaned data and summaries in `data/processed_data.json` or SQLite
- Drive-watcher module for auto-refresh
- Report timeline view by date/month/shift

### 7. Mobile-First Frontend
- Streamlit layout or React (TailwindCSS) as frontend
- Optimized for directors using phones
- Key metrics upfront, summaries readable on small screens

---

## 📦 Technical Stack

| Component | Technology |
|----------|-------------|
| LLM | OpenAI GPT-4o via `openai` Python SDK |
| Data Processing | `pandas`, `openpyxl` |
| Visualization | `plotly`, `streamlit` |
| Automation | `watchdog`, `google-api-python-client` |
| Storage | `JSON`, optionally `SQLite` |
| Frontend | `streamlit` MVP or `React + Tailwind` in final |
| Export | `weasyprint` for PDF |
| OCR | `pytesseract` (optional future module) |

---

## 📁 Expected Directory Structure

```
InsightFactory/
├── app.py
├── .env
├── config.py
├── requirements.txt
├── helpers/
│   ├── gpt_cleaner.py
│   ├── kpi_engine.py
│   ├── summary_generator.py
│   └── drive_watcher.py
├── data/
│   └── processed_data.json
├── reports/
│   └── exported_pdfs/
└── static/
    └── logo.png
```

---

## 🧩 Integration Points for Copilot

Copilot should:
- Guide `app.py` layout using modular imports
- Implement LLM calls in `gpt_cleaner.py` and `summary_generator.py`
- Structure KPI logic in `kpi_engine.py`
- Enable file sync logic in `drive_watcher.py`
- Maintain a `config.py` for sensitive or reusable paths
- Comment functions with docstrings for maintainability

---

## ✅ Future Considerations

- Burmese ↔ English toggle for interface
- Notifications via LINE/email for daily reports
- Role-based access control (Admin vs. Viewer)
- Real-time GPT Q&A with dataset ("Why was Shift B low in May?")

---
