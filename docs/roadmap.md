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
1. Implement FastAPI service for KPI exposure.
2. Configure CopilotKit project consuming the new API endpoints.
3. Capture DeepResearch briefs and push into `reports/latest_research.md`.
4. Review telemetry and iterate on UX + automation coverage.
