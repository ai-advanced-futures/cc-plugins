# Product Finance Plugin Integration Guide

This guide covers how to integrate the Product Finance plugin with other Claude Code plugins, external systems, and how to build custom integrations.

## Table of Contents

1. [JTBD Plugin Integration](#jtbd-plugin-integration)
2. [Standard File Format Integration](#standard-file-format-integration)
3. [Custom Integration Patterns](#custom-integration-patterns)

---

## JTBD Plugin Integration

The JTBD plugin (`jtbd-market-discovery`) writes its findings as result files in `.jtbd-market-discovery/results/`. A result of kind `customer_segment` names a segment. A result of kind `willingness_to_pay` gives a monthly price for one segment, named in `value.segment`.

`/product-finance:discover` reads one of these files:

- **A person's run** reads the newest result file that holds a segment or a willingness-to-pay result. It sets the willingness to pay on the person's segments of the same name, and never replaces a value the person wrote.
- **A plugin run** reads only the result file that its `inputs_from` entry names.

The **Person run** and **Plugin run** sections of `commands/discover.md` hold the exact rules. The ACV of a segment is 12 times its monthly willingness to pay.

When no jtbd result is found, `/discover` sizes the market from the person's answers.

---

## Standard File Format Integration

The Product Finance plugin uses standardized JSON schemas for all data files, enabling easy integration with external systems and other plugins.

### JSON Schema Compatibility

All Product Finance data files follow JSON Schema Draft-07. Schemas are located in:

```
plugins/product-finance/templates/
├── assumptions.json          # Financial assumptions schema
├── metrics.json              # Current metrics schema
├── ai-economics.json         # AI cost/ROI schema
├── instrumentation-plan.json # Instrumentation schema
└── event-schemas/
    ├── subscription_events.json
    └── ai_usage_events.json
```

#### Validating Against Schemas

```bash
# Using jsonschema (Python)
pip install jsonschema

python -c "
import json
from jsonschema import validate

with open('templates/assumptions.json') as schema_file:
    schema = json.load(schema_file)

with open('.product-finance/assumptions.json') as data_file:
    data = json.load(data_file)

validate(instance=data, schema=schema)
print('Validation successful!')
"
```

### How Other Plugins Can Read Product Finance Data

#### 1. Reading Assumptions

Other plugins can read baseline financial assumptions:

```python
import json
import os

def read_product_finance_assumptions(working_dir: str) -> dict:
    """Read financial assumptions from Product Finance plugin."""
    path = os.path.join(working_dir, '.product-finance', 'assumptions.json')

    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)

    return {}

# Example usage in another plugin
assumptions = read_product_finance_assumptions('.')

# Access pricing data
pricing_model = assumptions.get('pricing', {}).get('model')
tiers = assumptions.get('pricing', {}).get('tiers', [])

# Access cost data
cac_by_channel = assumptions.get('costs', {}).get('sales_marketing', {}).get('cac_by_channel', {})

# Access retention targets
ltv_cac_target = assumptions.get('targets', {}).get('ltv_cac_ratio_target', 3.0)
```

#### 2. Reading Metrics

Current financial metrics are available for dashboards and reports:

```python
def read_current_metrics(working_dir: str) -> dict:
    """Read current financial metrics."""
    path = os.path.join(working_dir, '.product-finance', 'metrics.json')

    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)

    return {}

# Example: Get unit economics for display
metrics = read_current_metrics('.')
unit_economics = metrics.get('unit_economics', {})

cac = unit_economics.get('cac')
ltv = unit_economics.get('ltv')
ltv_cac_ratio = unit_economics.get('ltv_cac_ratio')
payback_months = unit_economics.get('cac_payback_months')
```

#### 3. Reading Feature ROI Data

```python
import glob

def list_feature_roi_analyses(working_dir: str) -> list:
    """List all feature ROI analyses."""
    pattern = os.path.join(working_dir, '.product-finance', 'feature-roi-*.json')
    return glob.glob(pattern)

def read_feature_roi(working_dir: str, feature_name: str) -> dict:
    """Read specific feature ROI analysis."""
    sanitized = feature_name.lower().replace(' ', '-')
    path = os.path.join(working_dir, '.product-finance', f'feature-roi-{sanitized}.json')

    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)

    return {}

# Example: Get ROI recommendation
roi_data = read_feature_roi('.', 'Advanced Analytics Dashboard')
recommendation = roi_data.get('decision', {}).get('recommendation')  # BUILD, DEFER, or DON'T BUILD
roi_pct = roi_data.get('financial_analysis', {}).get('roi', {}).get('percentage')
```

### How Other Plugins Can Write Product Finance Data

#### 1. Contributing Metrics Updates

External systems can update metrics:

```python
import json
from datetime import datetime

def update_metrics(working_dir: str, updates: dict) -> None:
    """Update financial metrics from external source."""
    path = os.path.join(working_dir, '.product-finance', 'metrics.json')

    # Read existing metrics
    if os.path.exists(path):
        with open(path, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = {}

    # Deep merge updates
    metrics = deep_merge(metrics, updates)

    # Add metadata
    metrics['metadata'] = metrics.get('metadata', {})
    metrics['metadata']['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    metrics['metadata']['updated_by'] = 'external_integration'

    # Write back
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

# Example: Update from billing system
update_metrics('.', {
    'growth_metrics': {
        'arr': 1200000,
        'mrr': 100000
    },
    'customer_metrics': {
        'total_customers': 250,
        'new_customers_current_period': 15
    }
})
```

#### 2. Writing AI Usage Events

For AI economics tracking:

```python
def log_ai_usage_event(working_dir: str, event: dict) -> None:
    """Log AI usage event for cost tracking."""
    events_dir = os.path.join(working_dir, '.product-finance', 'events', 'ai_usage')
    os.makedirs(events_dir, exist_ok=True)

    # Append to daily log
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    log_path = os.path.join(events_dir, f'{date_str}.jsonl')

    event['timestamp'] = datetime.utcnow().isoformat() + 'Z'

    with open(log_path, 'a') as f:
        f.write(json.dumps(event) + '\n')

# Example: Log LLM API call
log_ai_usage_event('.', {
    'event_type': 'llm_api_call',
    'model': 'claude-sonnet-4',
    'provider': 'anthropic',
    'input_tokens': 1500,
    'output_tokens': 800,
    'cost_usd': 0.012,
    'user_id': 'user_123',
    'feature': 'ai_search'
})
```

### API-Like Patterns for Plugin Communication

#### 1. Request-Response Pattern

Plugins can request financial calculations:

```python
# Plugin A writes request
request = {
    'request_type': 'calculate_roi',
    'feature_name': 'New Feature',
    'build_cost': 50000,
    'monthly_revenue_impact': 5000,
    'time_horizon_months': 36
}

with open('.product-finance/requests/roi_request_001.json', 'w') as f:
    json.dump(request, f)

# Product Finance processes and writes response
# .product-finance/responses/roi_response_001.json

# Plugin A reads response
with open('.product-finance/responses/roi_response_001.json', 'r') as f:
    response = json.load(f)
    print(f"ROI: {response['roi_pct']}%")
```

#### 2. Event Stream Pattern

Real-time event consumption:

```python
# Financial event types
EVENT_TYPES = [
    'subscription_created',
    'subscription_upgraded',
    'subscription_churned',
    'ai_usage_recorded',
    'revenue_recognized',
    'cost_incurred'
]

# Event file structure
# .product-finance/events/{event_type}/{date}.jsonl

def read_events_since(working_dir: str, event_type: str, since: datetime) -> list:
    """Read events of a type since a given time."""
    events = []
    events_dir = os.path.join(working_dir, '.product-finance', 'events', event_type)

    if not os.path.exists(events_dir):
        return events

    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.jsonl'):
            continue

        file_path = os.path.join(events_dir, filename)
        with open(file_path, 'r') as f:
            for line in f:
                event = json.loads(line)
                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                if event_time > since:
                    events.append(event)

    return events
```

### .product-finance/ Directory Structure and Conventions

#### Complete Directory Layout

```
.product-finance/
├── assumptions.json              # Core financial assumptions
├── metrics.json                  # Current financial metrics
├── ai-economics.json             # AI cost and ROI data
├── discovery-report.json         # Market discovery output
├── discovery-report.md           # Human-readable discovery report
│
├── feature-roi-*.json            # Per-feature ROI analyses
│   └── feature-roi-analytics-dashboard.json
│
├── models/                       # Scenario models
│   ├── scenario-base.json
│   ├── scenario-optimistic.json
│   └── scenario-pessimistic.json
│
├── reports/                      # Generated reports
│   ├── health-check-2026-01-23.md
│   ├── feature-roi-analytics-dashboard-2026-01-23.md
│   └── unit-economics-2026-Q1.md
│
├── instrumentation/              # Instrumentation artifacts
│   ├── plan.json
│   ├── events.json
│   └── migrations/
│       └── 001_create_subscription_events.sql
│
├── events/                       # Event logs (for tracking)
│   ├── subscription/
│   │   └── 2026-01-23.jsonl
│   ├── ai_usage/
│   │   └── 2026-01-23.jsonl
│   └── cost/
│       └── 2026-01-23.jsonl
│
├── requests/                     # Inter-plugin requests
│   └── *.json
│
├── responses/                    # Inter-plugin responses
│   └── *.json
│
└── cache/                        # Calculation cache
    └── *.json
```

#### File Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Core config | `{type}.json` | `assumptions.json` |
| Feature ROI | `feature-roi-{sanitized-name}.json` | `feature-roi-ai-search.json` |
| Reports | `{report-type}-{date}.md` | `health-check-2026-01-23.md` |
| Events | `{date}.jsonl` | `2026-01-23.jsonl` |
| Scenarios | `scenario-{name}.json` | `scenario-optimistic.json` |
| Migrations | `{number}_{description}.sql` | `001_create_events.sql` |

#### Sanitization Rules

Feature names and identifiers are sanitized:

```python
def sanitize_name(name: str) -> str:
    """Sanitize name for use in filenames."""
    # Lowercase
    sanitized = name.lower()
    # Replace spaces with hyphens
    sanitized = sanitized.replace(' ', '-')
    # Remove special characters
    sanitized = re.sub(r'[^a-z0-9\-]', '', sanitized)
    # Collapse multiple hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    return sanitized

# Examples:
# "Advanced Analytics Dashboard" -> "advanced-analytics-dashboard"
# "AI-Powered Search (Beta)" -> "ai-powered-search-beta"
# "Feature #1: SSO" -> "feature-1-sso"
```

---

## Custom Integration Patterns

### Building Custom Integrations

#### 1. Creating a Custom Data Source

To feed external data into Product Finance:

```python
# custom_integration.py

import json
import os
from datetime import datetime

class ProductFinanceIntegration:
    """Base class for Product Finance integrations."""

    def __init__(self, working_dir: str = '.'):
        self.working_dir = working_dir
        self.pf_dir = os.path.join(working_dir, '.product-finance')

    def ensure_directory(self) -> None:
        """Ensure .product-finance directory exists."""
        os.makedirs(self.pf_dir, exist_ok=True)

    def read_assumptions(self) -> dict:
        """Read current assumptions."""
        path = os.path.join(self.pf_dir, 'assumptions.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def write_metrics_update(self, metrics: dict) -> None:
        """Write metrics update with merge behavior."""
        self.ensure_directory()
        path = os.path.join(self.pf_dir, 'metrics.json')

        existing = {}
        if os.path.exists(path):
            with open(path, 'r') as f:
                existing = json.load(f)

        # Deep merge
        merged = self._deep_merge(existing, metrics)
        merged['metadata'] = merged.get('metadata', {})
        merged['metadata']['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        with open(path, 'w') as f:
            json.dump(merged, f, indent=2)

    def log_event(self, event_type: str, event_data: dict) -> None:
        """Log an event to the appropriate event stream."""
        events_dir = os.path.join(self.pf_dir, 'events', event_type)
        os.makedirs(events_dir, exist_ok=True)

        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        log_path = os.path.join(events_dir, f'{date_str}.jsonl')

        event_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        with open(log_path, 'a') as f:
            f.write(json.dumps(event_data) + '\n')

    @staticmethod
    def _deep_merge(base: dict, update: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ProductFinanceIntegration._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


# Example: Stripe Integration
class StripeIntegration(ProductFinanceIntegration):
    """Sync financial data from Stripe."""

    def sync_mrr(self, stripe_mrr: float) -> None:
        """Update MRR from Stripe."""
        self.write_metrics_update({
            'growth_metrics': {
                'mrr': stripe_mrr,
                'arr': stripe_mrr * 12
            },
            'metadata': {
                'data_sources': ['stripe']
            }
        })

    def log_subscription_event(self, event: dict) -> None:
        """Log Stripe subscription event."""
        self.log_event('subscription', {
            'source': 'stripe',
            'stripe_event_id': event.get('id'),
            'event_type': event.get('type'),
            'customer_id': event.get('data', {}).get('object', {}).get('customer'),
            'amount': event.get('data', {}).get('object', {}).get('amount', 0) / 100
        })


# Usage
stripe_integration = StripeIntegration('.')
stripe_integration.sync_mrr(150000)
stripe_integration.log_subscription_event({
    'id': 'evt_123',
    'type': 'customer.subscription.created',
    'data': {
        'object': {
            'customer': 'cus_123',
            'amount': 9900
        }
    }
})
```

#### 2. Creating a Custom Report Consumer

To consume Product Finance reports:

```python
# report_consumer.py

import json
import os
import glob
from datetime import datetime

class HealthCheckConsumer:
    """Consume health check reports for external dashboards."""

    def __init__(self, working_dir: str = '.'):
        self.reports_dir = os.path.join(working_dir, '.product-finance', 'reports')

    def get_latest_health_check(self) -> dict:
        """Get the most recent health check report."""
        pattern = os.path.join(self.reports_dir, 'health-check-*.json')
        files = glob.glob(pattern)

        if not files:
            return {}

        # Sort by date in filename, get latest
        latest = sorted(files)[-1]

        with open(latest, 'r') as f:
            return json.load(f)

    def get_health_status(self) -> str:
        """Get simple health status for monitoring."""
        report = self.get_latest_health_check()

        if not report:
            return 'UNKNOWN'

        overall = report.get('health_assessment', {}).get('overall', 'unknown')
        return overall.upper()

    def get_key_metrics(self) -> dict:
        """Extract key metrics for dashboard display."""
        report = self.get_latest_health_check()

        if not report:
            return {}

        metrics = report.get('metrics', {})

        return {
            'arr': metrics.get('growth_metrics', {}).get('arr'),
            'mrr': metrics.get('growth_metrics', {}).get('mrr'),
            'ltv_cac_ratio': metrics.get('unit_economics', {}).get('ltv_cac_ratio'),
            'rule_of_40': metrics.get('profitability_metrics', {}).get('rule_of_40'),
            'nrr': metrics.get('retention_expansion', {}).get('nrr_pct'),
            'report_date': report.get('metadata', {}).get('generated_at')
        }


# Usage
consumer = HealthCheckConsumer('.')
status = consumer.get_health_status()
metrics = consumer.get_key_metrics()

print(f"Financial Health: {status}")
print(f"ARR: ${metrics.get('arr', 0):,.0f}")
print(f"LTV:CAC: {metrics.get('ltv_cac_ratio', 0):.1f}:1")
```

### Extending the Plugin

#### 1. Adding Custom Metrics

Extend the metrics schema for domain-specific KPIs:

```json
// .product-finance/extensions/custom-metrics-schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Custom Metrics Extension",
  "type": "object",
  "properties": {
    "marketplace_metrics": {
      "type": "object",
      "description": "Marketplace-specific metrics",
      "properties": {
        "gmv": {
          "type": "number",
          "description": "Gross Merchandise Value"
        },
        "take_rate_pct": {
          "type": "number",
          "description": "Platform take rate percentage"
        },
        "seller_count": {
          "type": "integer"
        },
        "buyer_count": {
          "type": "integer"
        },
        "avg_order_value": {
          "type": "number"
        },
        "orders_per_buyer_monthly": {
          "type": "number"
        }
      }
    }
  }
}
```

#### 2. Adding Custom Commands

Create a custom command by extending the plugin:

```markdown
// commands/custom-roi.md (conceptual)
---
command: custom-roi
description: Custom ROI calculation for marketplace businesses
---

# Custom ROI Command

## Purpose
Marketplace-specific ROI calculation including GMV impact...

[Command specification follows standard format]
```

---

## Reference

### Quick Reference: Reading Product Finance Data

```python
# One-liner to get common metrics
import json

# Get ARR
with open('.product-finance/metrics.json') as f:
    arr = json.load(f).get('growth_metrics', {}).get('arr', 0)

# Get LTV:CAC ratio
with open('.product-finance/metrics.json') as f:
    ltv_cac = json.load(f).get('unit_economics', {}).get('ltv_cac_ratio', 0)

# Get feature ROI recommendation
with open('.product-finance/feature-roi-my-feature.json') as f:
    recommendation = json.load(f).get('decision', {}).get('recommendation')
```

### Quick Reference: Writing Product Finance Data

```python
# Update a single metric
import json
from datetime import datetime

with open('.product-finance/metrics.json', 'r+') as f:
    data = json.load(f)
    data['growth_metrics']['arr'] = 1500000
    data['metadata'] = data.get('metadata', {})
    data['metadata']['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
```

### Related Documentation

- [README.md](../README.md) - Plugin overview and quick start
- [commands/](../commands/) - Command reference
- [METHODOLOGY.md](./METHODOLOGY.md) - Financial methodology
- [KPI_DEFINITIONS.md](./KPI_DEFINITIONS.md) - KPI definitions

---

**Financial Intelligence as Code** - Integrate financial thinking across your entire development workflow.
