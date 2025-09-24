# InsightFactory System Blueprint

## Vision
InsightFactory should operate as a continuously learning manufacturing intelligence fabric that transforms raw plant data into executive-ready insights, orchestrates autonomous agents, and plugs into ERP/MES workflows without heavy manual intervention. The blueprint below captures the current capabilities, gaps, and the staged upgrades required to deliver an elite-yet-lightweight solution.

## Layered Architecture
1. **Experience Layer**
   - Streamlit Control Center (Executive Overview, Operations Command Center, Pipeline Summary, AI Copilot pages)
   - FastAPI gateway powering lightweight portals, CopilotKit embeddings, and downstream ERP consumers
   - Artifact downloads (HTML reports, CSV history, dashboard payloads) for offline review
2. **Intelligence Layer**
   - KPI Engine: calculates FPY, OEE, yield, and anomaly flags from structured sheets
   - Claims Pipeline: aggregates claim spreadsheets, severity scoring, exposure trends
   - Document Processor: OCR/text extraction, word counts, document risk snippets
   - Performance Analyzer: trend mining, forecast projections, volatility alerts
   - Health Evaluator: synthesizes KPI, claims, documents, and intake quality into readiness scores
   - Autonomy Orchestrator: action recommendations, automation pipeline roadmap
   - Research Planner: CopilotKit + Tongyi DeepResearch connectors for AI research briefs
3. **Data Operations Layer**
   - Drive Browser & Sync: multi-folder ingestion with aliasing and metadata capture
   - Data Profiler: intake quality metrics, unreadable files, extension mix, per-source freshness
   - Run History Writer: append-only ledger capturing metrics, artifacts, durations, agent status
   - Serialization helpers: JSON-safe payload conversion, shared report path resolver
4. **Platform Layer**
   - Configuration management via `.env` and `config.py` (REPORTS_DIR, API keys, folder aliases)
   - CI/CD (GitHub Actions) running compilation + pytest suite; future container builds
   - Optional services: Celery/RQ task queues, DuckDB/Iceberg lakehouse, Superset dashboards

## Autonomous Agent Constellation
| Agent | Purpose | Inputs | Outputs | Next Evolution |
| --- | --- | --- | --- | --- |
| **Ingestion Scout** | Monitor Google Drive folders, ignore generated artifacts, trigger pipeline runs | Drive metadata, folder aliases, ignore patterns | Local synchronized datasets, source registry snapshot | Event-driven Pub/Sub ingestion with delta tracking |
| **Intake Analyst** | Profile synced files and detect anomalies in coverage/granularity | Synced file list, profiling heuristics | Intake metrics, drift alerts | Schema contract validation & great expectations integration |
| **KPI Specialist** | Compute production KPIs, FPY, OEE, variance analyses | Structured sheets, KPI rules | KPI tables, anomaly flags | Machine learning for predictive quality + root cause hints |
| **Claims & Compliance Lead** | Consolidate claim records, severity, backlog | Claim sheets, historical run history | Claim metrics, risk ranking | NLP claim summarization, regulatory compliance tagging |
| **Document Curator** | OCR text, track size/readability, highlight risk sentences | Images, PDFs, text files | Extracted text, word counts, document alerts | Embedding search, LLM-based summarization |
| **Performance Strategist** | Project trends, estimate run-to-target, highlight volatility | Run history ledger | Forecast notes, improvement targets | Scenario simulation + Monte Carlo stress tests |
| **Autonomy Coach** | Compose action plan, automation backlog, agent readiness | KPI/claims/document metrics, integration status | Immediate actions, automation opportunities | Ticket auto-creation (Jira/Linear), closed-loop follow-up |
| **Research Liaison** | Coordinate CopilotKit & DeepResearch tasks | API credentials, planner prompts | Research briefs, integration telemetry | Adaptive prompting, multi-agent debate |
| **Experience Designer** | Surface insights via Streamlit & API, maintain UX health | Metrics, insights, action plans | Control Center UI, REST endpoints, HTML reports | Role-aware views, mobile-ready UI, design system integration |

## Gap Analysis
| Area | Current Strength | Gap | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| **Real-time ingestion** | Manual runner & polling watcher | No event-driven queue or incremental diffing | Delayed KPI refresh under bursty updates | Introduce Pub/Sub trigger with Celery workers |
| **Data contracts** | Profiling catches unreadable files | No schema enforcement or lineage graph | Silent KPI drift if columns change | Add Pydantic/Great Expectations contracts + lineage capture |
| **Historical warehousing** | CSV run history | No columnar lakehouse for BI scale | Hard to query long-term trends in BI tools | Persist to DuckDB/Iceberg and expose SQL endpoints |
| **Alerting** | UI surfacing only | No push notifications | Operators must poll dashboards | Hook planner alerts into Slack/Teams/email |
| **UI scalability** | Streamlit multipage app | Not optimized for mobile or role-based access | Hard for execs vs engineers to share same UI | Introduce Streamlit auth + persona-driven layouts, or React portal |
| **CI/CD** | Linting via py_compile + pytest | No dependency scanning, container builds, or data QA tests | Higher risk when integrating vendors | Extend CI with pip-audit, docker build, synthetic data regression |
| **Security** | API key auth, env-based secrets | No secrets rotation guidance, RBAC, or audit logging | Hard to satisfy enterprise infosec | Integrate Vault/Secret Manager, add request logging, sign artifacts |

## ERRC Canvas (Blue Ocean Strategy)
- **Eliminate**: Manual handoffs between ingestion and analytics, redundant spreadsheets for run tracking, UI clutter from legacy pages.
- **Reduce**: Time-to-insight by automating reruns; repeated credential configuration via centralized secret manager; noise in dashboards through curated narratives.
- **Raise**: Transparency of data lineage, autonomy of AI agents, executive confidence via health scoring and forecasts, cross-plant comparisons.
- **Create**: Autonomous improvement loop (CopilotKit/Tongyi orchestration), MES-lite modules (maintenance, quality, claims), integration marketplace (plug-in agents), predictive playbooks.

## Competitive Landscape & Differentiation
- **Versus traditional MES**: InsightFactory emphasizes lightweight deployment (Streamlit, FastAPI) with advanced AI copilots versus heavy monolithic suites.
- **Versus BI dashboards**: Adds automated ingestion, health scoring, action planning, and run history persistence; not just visualization.
- **Versus RPA/Automation tools**: Combines analytics, AI research, and human-in-the-loop UI, enabling hybrid operations teams.
- **Differentiators**: Multi-agent orchestration, CopilotKit/Tongyi integration, modular pipelines, strong profiling, and extensible REST gateway ready for ERP embedding.

## Upgrade Wave Plan
1. **Stabilize & Harden (Weeks 1-2)**
   - Add data contracts (Pydantic schemas, drift monitors) and expand CI (pytest with synthetic fixtures, pip-audit, mypy).
   - Wire Pub/Sub or webhook triggers into the pipeline runner, persisting ingestion events and providing replay.
   - Containerize pipelines + Streamlit + API; publish to registry with version tags.
2. **Scale & Automate (Weeks 3-5)**
   - Deploy Celery/RQ workers for asynchronous processing; attach retry/backoff policies.
   - Build DuckDB/Iceberg historical warehouse; expose SQL endpoints + Superset dashboards.
   - Integrate Slack/Teams alerting for health degradation or urgent planner recommendations.
3. **Elevate Experience (Weeks 6-8)**
   - Introduce persona-based UI (executive, operations, quality) with theming and responsive layout.
   - Embed CopilotKit UI components directly in the Control Center; enable conversational analytics via FastAPI streaming endpoints.
   - Provide AI-generated run summaries, anomaly explanations, and recommended maintenance tickets.
4. **Innovate & Differentiate (Weeks 9-12)**
   - Launch predictive maintenance and root-cause analysis modules leveraging trend history + research briefs.
   - Add integration marketplace concept where new agents (inventory, finance, HR) can be registered via configuration.
   - Formalize governance: artifact signing, audit trails, automated compliance checklists.

## Continuous Improvement Loop
1. **Review**: Weekly system health review combining run history, planner output, CI dashboards, and user feedback.
2. **Plan**: Prioritize backlog items using autonomy coach recommendations + ERRC insights.
3. **Implement**: Execute tasks in focused sprints, ensuring every change has tests, docs, and deployment plan.
4. **Verify**: Run CI/CD, smoke tests, and pilot group validation; monitor telemetry post-deployment.
5. **Strategize Next Move**: Update this blueprint, roadmap, and team backlog to reflect new realities and opportunities.

## Immediate Action Checklist
- [ ] Stand up Pub/Sub-triggered pipeline runner with Celery worker and retry semantics
- [ ] Add data contracts + schema drift detection to KPI and claims pipelines
- [ ] Extend CI with `pip-audit`, `mypy`, and synthetic data regression suite
- [ ] Implement Slack/Teams alerting for health score < 0.7 or stale analytics over 6 hours
- [ ] Design persona-based Streamlit layouts and color-coded health narratives
- [ ] Embed CopilotKit UI components and streaming FastAPI responses for conversational ops

## References & Further Reading
- [CopilotKit](https://github.com/CopilotKit/CopilotKit) for conversational copilots embedded in analytics portals
- [Tongyi DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) for autonomous research workflows
- [Open Manufacturing Platform](https://open-manufacturing.org/) for interoperability standards
- [Blue Ocean Strategy ERRC Grid](https://www.blueoceanstrategy.com/tools/) for innovation framing

This blueprint should be refreshed every major release to capture new capabilities, agent roles, and strategic bets.
