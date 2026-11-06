# data-strategy Frameworks Reference

Six frameworks across four analytical domains. Domain agents load only their own section via §-markers.

---

<!-- §strategy-start -->
## Strategy Domain Frameworks

### DAMA-DMBOK (Data Management Body of Knowledge, 2nd ed.)

The 11 DAMA Knowledge Areas (KAs) define the scope of data management maturity:
1. Data Governance — policies, oversight, stewardship
2. Data Architecture — enterprise data models, standards
3. Data Modeling & Design — logical and physical data models
4. Data Storage & Operations — physical media, performance
5. Data Security — privacy, access control, classification
6. Data Integration & Interoperability — ETL/ELT, API, CDC
7. Document & Content Management — unstructured data, records
8. Reference & Master Data — MDM, golden records, hierarchies
9. Data Warehousing & Business Intelligence — analytics platforms
10. Metadata Management — business and technical metadata
11. Data Quality — profiling, rules, remediation

**Assessment scale (per KA):**
- 0 — Not aware / no practice
- 1 — Initial / ad hoc
- 2 — Repeatable / managed
- 3 — Defined / proactive
- 4 — Optimised / data-driven

**Gap thresholds:** avg < 2.0 = major, 2.0–3.0 = minor, ≥ 3.0 = none

---

### Gartner D&A Maturity Model

Five maturity levels, each building on the previous:
1. **Descriptive** — What happened? (reporting, dashboards, KPIs)
2. **Diagnostic** — Why did it happen? (drill-down, root cause, segmentation)
3. **Predictive** — What will happen? (ML models, forecasting, scoring)
4. **Prescriptive** — What should we do? (optimisation, decision automation)
5. **Cognitive** — Automated decision-making (AI-driven, self-optimising)

**Key principle:** Most companies stall at Level 2. Jumping from Level 2 to Level 4 without Level 3 ML foundations is a common failure mode.

**Assessment dimensions:** reporting, analytics, predictive, prescriptive, automation — scored 0–4 per dimension.
<!-- §strategy-end -->

---

<!-- §platform-start -->
## Platform Domain Frameworks

### Data Mesh — Zhamak Dehghani (2022)

Four principles that define a decentralised data architecture:

**P1 — Domain Ownership:** The business domain that produces data owns, maintains, and serves it as analytical data product. Central data teams create bottlenecks. Each domain team is accountable for its data products.

**P2 — Data as a Product:** Analytical data must have quality SLAs, discoverability, documentation, and versioning. It is a product with consumers — not a byproduct of operations. Product thinking applied to data.

**P3 — Self-Serve Data Infrastructure:** A platform team enables domains to produce and consume data without central coordination. Infrastructure is a product too. Reduces cognitive load on domain teams.

**P4 — Federated Computational Governance:** Global interoperability rules (schemas, lineage, privacy) with local domain autonomy. Central enforcement of standards, local implementation freedom.

**Scoring scale (per principle):** 0.0 (none) → 1.0 (fully realised)
**Compliance thresholds:** < 0.3 = low, 0.3–0.7 = partial, > 0.7 = high

⚠️ **Governance tension:** P4 (federated governance) conflicts with DAMA-DMBOK's assumption of centralised stewardship. This tension MUST be surfaced to the synthesizer. Set `framework_conflict: detected` in your YAML header if the company's context makes this tension material.

---

### Data Engineering Lifecycle — Joe Reis + Matt Housley (2022)

Five lifecycle stages, each with distinct technology choices and failure modes:
1. **Generation** — Source systems: databases, APIs, streams, IoT
2. **Storage** — Raw/processed layers: data lake, warehouse, lakehouse
3. **Ingestion** — Batch, micro-batch, streaming; CDC for operational DBs
4. **Transformation** — dbt, Spark, Flink; ELT vs ETL; data quality checks
5. **Serving** — OLAP queries, ML feature serving, reverse ETL to SaaS

**Undercurrents** (cross-cutting at every stage): Security, data management, DataOps (CI/CD for pipelines), orchestration (Airflow/Dagster/Prefect), software engineering best practices.

**Feature Stores + Ground Truth:** Online store (inference, low latency) + offline store (training, historical). Capturing production labels closes the training feedback loop — the most commonly missed ML architecture requirement.
<!-- §platform-end -->

---

<!-- §products-start -->
## Products Domain Frameworks

### Data as a Product — DJ Patil + Dehghani P2

A data product is a self-contained unit of analytical value with:
- **Owner** — a named team accountable for quality and freshness
- **Consumers** — known downstream users with documented needs
- **Quality SLA** — latency, freshness, and completeness guarantees
- **Versioning** — schema changes are managed, not surprise-breaking
- **Documentation** — discoverable, understandable without tribal knowledge

**Product completeness scoring:** 6 attributes (owner, consumers, quality_sla, versioned, documented, schema_defined) scored as boolean → completeness = sum/6

**Portfolio maturity:** avg completeness < 0.4 = nascent, 0.4–0.7 = developing, > 0.7 = mature

---

### Data Contracts — Andrew Jones (2023)

A data contract is a formal agreement between data producers and consumers defining:
- **Schema** — field names, types, constraints — machine-readable
- **SLA** — freshness, latency, completeness — measurable
- **Deprecation policy** — how and when breaking changes will be communicated

**Contract maturity:** none (0 of 3 attributes) → partial (1–2) → defined (all 3)

**Key principle:** Data contracts prevent the "data swamp" — the accumulation of undocumented, unreliable data that consumers stop trusting. Contracts shift data quality responsibility to producers.
<!-- §products-end -->

---

<!-- §synthesis-start -->
## Synthesis: Cross-Framework Tensions

This section is loaded by the synthesizer only when `framework_conflict: detected` appears in any domain YAML header.

### The DAMA-vs-Data-Mesh Governance Tension

**DAMA-DMBOK position:** Centralised stewardship is the foundation of data governance. A Chief Data Officer (CDO) or central data governance committee sets standards, manages quality, and enforces policy across the enterprise. Accountability is centralised.

**Data Mesh position:** Federated governance enables speed. Domains own their data and govern themselves within global interoperability standards. Central governance creates bottlenecks and misaligned incentives. Accountability is distributed.

**These are not reconcilable in their pure forms.** The synthesizer must make a contextual recommendation:

| Context | Recommendation |
|---------|---------------|
| Regulated industry (finance, healthcare) | DAMA-first: centralised stewardship is non-negotiable for compliance |
| < 50 engineers, early-stage | Neither: governance overhead is premature; lightweight standards suffice |
| Product-led, > 50 engineers, distributed teams | Data Mesh P4: federated governance with global schema standards |
| Enterprise with existing CDO + mature DAMA | Hybrid: DAMA for governance policy + Data Mesh P1/P2 for execution |

**Frame this explicitly in the ADR deliverable.** Do not leave the tension implicit.
<!-- §synthesis-end -->
