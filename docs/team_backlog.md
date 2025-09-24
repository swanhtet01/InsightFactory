# InsightFactory Team Backlog

## Mission Pods

### Data Engineering Pod
- Automate Drive watcher deployment with containerized services and health probes.
- Harden schema validation (granularity tags, per-plant contracts) before KPI computation.
- Publish incremental extracts to a warehouse (DuckDB/Iceberg) for ERP reporting.

### Analytics & Experience Pod
- Expand Control Center charts to include freshness-sensitive sparklines and plant filters.
- Design lightweight executive emails summarizing hero metrics and freshness score.
- Prototype kiosk-ready layouts for production floor displays.

### AI Orchestration Pod
- Capture CopilotKit/Tongyi responses for longitudinal analysis and feedback loops.
- Launch an alerting bridge that escalates overdue freshness status via Slack or email.
- Evaluate Gemini/GPT actions for automatic ticket creation when anomalies persist.

### Platform Reliability Pod
- Extend CI to run nightly synthetic pipeline jobs against fixture data.
- Add observability hooks (Prometheus exporters) for pipeline duration and freshness age.
- Define SLOs for freshness (<2 hours) and automate run retries to stay within target.

## Current Sprint Focus
1. Ship the new freshness scoring UI to Streamlit and REST consumers.
2. Wire the FastAPI gateway into CopilotKit staging for conversational KPI access.
3. Draft a rollout plan for multi-plant ERP integration using the warehouse extracts.

## Next Planning Cycle
- Evaluate open-source MES connectors for scheduling and maintenance modules.
- Scope a lightweight mobile companion that surfaces freshness alerts and hero metrics.
- Partner with finance stakeholders to align claim metrics with ledger reconciliation.
