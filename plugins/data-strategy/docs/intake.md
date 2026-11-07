# Intake questions

A skill of this plugin reads this file before it asks the person any question. Only a skill asks the person, because Claude Code removes `AskUserQuestion` from every subagent. The skill writes the answers to `context.yaml`. The agents read `context.yaml` and ask nothing.

## Which skill asks which part

| Skill | Parts that it asks |
| --- | --- |
| `data-strategy` | Parts 1 to 5 |
| `strategy` | Parts 1 to 3 |
| `platform` | Parts 1, 4 and 5 |
| `products` | Part 1 |

Ask one part at a time. Ask the rating parts (2, 3 and 4) as one grouped list, not as one question for each item.

## Part 1: company context

Ask these questions one at a time.

1. "What does your company do, and what stage are you at? (Pre-PMF / PMF / Growth / Scale)"
2. "What is your main goal for this assessment? (Improving data quality / building data products / reducing platform complexity / aligning data investment to strategy)"
3. "How would you rate your current data maturity overall? (1 = just starting, 5 = advanced)"

## Part 2: DAMA knowledge areas

Ask the person to rate each area from 0 (none) to 4 (optimised):

> "For each area below, rate your current maturity from 0 (none) to 4 (optimised): Data Governance / Data Architecture / Data Modeling / Data Storage / Data Security / Data Integration / Document & Content Management / Reference & Master Data / Data Warehousing / Metadata Management / Data Quality"

## Part 3: Gartner maturity dimensions

> "Rate your analytics capabilities from 0 to 4: Reporting / Analytics / Predictive Modelling / Prescriptive Analytics / Automation"

## Part 4: Data Mesh self-assessment

> "For each Data Mesh principle, estimate your current adoption from 0.0 (none) to 1.0 (fully adopted): Domain Ownership / Data as a Product / Self-Serve Infrastructure / Federated Governance"

## Part 5: optional codebase scan

> "Do you have a codebase available for scanning? This improves the platform audit. (Yes / No)"

If the person says yes, list the files of the current project with `find` through the Bash tool, and look for signs of data pipelines: Airflow DAGs, dbt configs, `pipeline/` folders, feature store definitions, and CDC configs. The scan reads file names only. Write the names of the tools that you find to `codebase_signals`. If the person says no, write an empty list.

## Key map

| Label that the person sees | Key in `context.yaml` |
| --- | --- |
| Data Governance | `data_governance` |
| Data Architecture | `data_architecture` |
| Data Modeling | `data_modeling` |
| Data Storage | `data_storage` |
| Data Security | `data_security` |
| Data Integration | `data_integration` |
| Document & Content Management | `document_content` |
| Reference & Master Data | `reference_master` |
| Data Warehousing | `data_warehousing` |
| Metadata Management | `metadata_management` |
| Data Quality | `data_quality` |
| Reporting | `reporting` |
| Analytics | `analytics` |
| Predictive Modelling | `predictive` |
| Prescriptive Analytics | `prescriptive` |
| Automation | `automation` |
| Domain Ownership | `domain_ownership` |
| Data as a Product | `data_as_product` |
| Self-Serve Infrastructure | `self_serve` |
| Federated Governance | `federated_governance` |

## The file `context.yaml`

Write `.data-strategy-tmp/<session_id>/context.yaml` with the keys of the key map. Write only the keys of the parts that you asked.

```yaml
session_id: <session_id>
company_stage: <pre-pmf|pmf|growth|scale>
primary_goal: <string>
self_rated_maturity: <1-5>
dama_answers:
  data_governance: <0-4>
  data_architecture: <0-4>
  data_modeling: <0-4>
  data_storage: <0-4>
  data_security: <0-4>
  data_integration: <0-4>
  document_content: <0-4>
  reference_master: <0-4>
  data_warehousing: <0-4>
  metadata_management: <0-4>
  data_quality: <0-4>
gartner_answers:
  reporting: <0-4>
  analytics: <0-4>
  predictive: <0-4>
  prescriptive: <0-4>
  automation: <0-4>
mesh_answers:
  domain_ownership: <0.0-1.0>
  data_as_product: <0.0-1.0>
  self_serve: <0.0-1.0>
  federated_governance: <0.0-1.0>
codebase_signals: []  # empty if no scan, else the names of the tools found
```
