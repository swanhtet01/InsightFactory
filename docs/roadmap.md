# InsightFactory Expansion Roadmap

## Current Status
- Automated Drive sync, KPI, claim, and document extraction pipelines feed `reports/` artifacts.
- AI Research Planner generates CopilotKit and Tongyi DeepResearch integration steps after every run.
- Streamlit Pipeline Summary page presents KPIs, claims, documents, and AI recommendations.

## Near-Term Enhancements
1. **CopilotKit Embedding**
   - Serve KPI/claim APIs through FastAPI to stream structured context into CopilotKit agents.
   - Embed CopilotKit React components inside Streamlit using iframe or component bridge.
   - Offer shift-handover and anomaly-explanation copilots leveraging OpenAI/Gemini models.
2. **Tongyi DeepResearch Automation**
   - Push KPI deltas and claim anomalies to DeepResearch tasks nightly.
   - Collect generated research briefs and surface highlights inside the dashboard.
   - Use briefs to trigger maintenance or quality workflows in ERP modules.
3. **MES/ERP Modules**
   - Extend data warehouse schema for inventory, maintenance, and workforce planning.
   - Build modular Streamlit pages for production scheduling, claims, and compliance documentation.
   - Introduce RBAC and audit logging for regulated operations.

## Mid-Term Vision
- Event-driven processing using Pub/Sub or Kafka for sub-minute KPI refresh.
- Historical KPI lakehouse using DuckDB + Iceberg for cheap analytics at scale.
- Unified search across documents, KPIs, and claims with vector indexes.
- Automated CI/CD gates that lint data contracts, run regression tests, and publish container images.

## Long-Term Opportunities
- Predictive maintenance models fed by CopilotKit-collected operator feedback.
- Closed-loop optimization: DeepResearch results auto-create Jira/Linear tickets.
- Multi-plant digital twin with scenario simulations and AI-assisted scheduling.

## Next Loop
1. Ship a lightweight FastAPI gateway that streams KPI, claim, and document metrics for CopilotKit and
   external ERP consumers.
2. Attach the Drive watcher to an async task runner (Celery or RQ) so each change triggers an isolated
   pipeline execution with retry/backoff semantics.
3. Persist per-plant historical summaries (OEE, FPY, claims) to a warehouse-friendly format to unlock
   trend visualisations in the Streamlit UI.
4. Integrate alerting by pushing high-severity research planner recommendations to Slack or email so
   operations staff can act immediately.
5. Extend the new data profiling layer with schema drift detection, row-count parity checks, and automated
   data quality scoring to guarantee reliable ERP/MES reporting inputs.
