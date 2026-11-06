"""Instrumentation Analyzer for Financial Tracking.

This module analyzes codebases to identify existing instrumentation and suggest
improvements for financial tracking. It helps product teams implement comprehensive
tracking for key financial metrics like MRR, churn, CAC, and AI costs.

The analyzer:
1. Scans codebases for existing instrumentation
2. Identifies API endpoints and database models
3. Detects subscription management code
4. Finds AI/LLM API usage
5. Performs gap analysis against required financial metrics
6. Generates event schemas for missing tracking
7. Suggests database migrations for financial data storage

This enables teams to instrument financial tracking systematically and ensure
complete coverage of all board-level KPIs.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Framework(str, Enum):
    """Detected web framework."""

    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    RAILS = "rails"
    NEXTJS = "nextjs"
    UNKNOWN = "unknown"


class DatabaseType(str, Enum):
    """Database type for migration scripts."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    """Priority level for instrumentation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Category of tracking event."""

    SUBSCRIPTION = "subscription"
    USAGE = "usage"
    BILLING = "billing"
    CUSTOMER = "customer"
    AI = "ai"
    SUPPORT = "support"


@dataclass
class FilePattern:
    """Pattern for identifying specific code patterns."""

    pattern: str
    description: str
    category: str


class ExistingInstrumentation(BaseModel):
    """Represents existing instrumentation found in codebase."""

    event_name: str = Field(description="Name of tracked event")
    location: str = Field(description="File path where tracking is implemented")
    data_captured: list[str] = Field(description="Data points captured")
    quality: str = Field(description="Quality assessment")
    framework: Optional[str] = Field(default=None, description="Framework used")


class InstrumentationGap(BaseModel):
    """Represents a gap in current instrumentation."""

    metric: str = Field(description="Metric that cannot be calculated")
    missing_data: list[str] = Field(description="Missing data points")
    impact: Priority = Field(description="Impact of this gap")
    enables_metrics: list[str] = Field(
        default_factory=list, description="Metrics this would enable"
    )


class EventSchema(BaseModel):
    """Schema for a tracking event."""

    event_name: str = Field(description="Event name")
    event_category: EventCategory = Field(description="Event category")
    description: str = Field(description="What this event represents")
    trigger: str = Field(description="When/where to emit this event")
    priority: Priority = Field(description="Implementation priority")
    required_fields: list[dict[str, str]] = Field(
        description="Required data fields"
    )
    optional_fields: list[dict[str, str]] = Field(
        default_factory=list, description="Optional data fields"
    )
    enables_metrics: list[str] = Field(description="Metrics this enables")
    implementation_location: Optional[str] = Field(
        default=None, description="Suggested implementation location"
    )
    example_code: Optional[str] = Field(
        default=None, description="Example implementation"
    )


class DatabaseMigration(BaseModel):
    """Database migration suggestion."""

    migration_type: str = Field(description="Type of migration")
    table_name: str = Field(description="Table name")
    purpose: str = Field(description="Purpose of this change")
    priority: Priority = Field(description="Implementation priority")
    postgresql_script: Optional[str] = Field(
        default=None, description="PostgreSQL migration script"
    )
    mysql_script: Optional[str] = Field(
        default=None, description="MySQL migration script"
    )


class CodebaseAnalysis(BaseModel):
    """Analysis results from codebase scan."""

    framework: Framework = Field(description="Detected framework")
    database_type: DatabaseType = Field(description="Detected database")
    has_subscription_model: bool = Field(
        default=False, description="Has subscription/billing model"
    )
    has_ai_integration: bool = Field(default=False, description="Uses AI APIs")
    api_endpoints_found: int = Field(default=0, description="Number of API endpoints")
    models_found: int = Field(default=0, description="Number of database models")
    existing_tracking_count: int = Field(
        default=0, description="Existing tracking events found"
    )
    ai_providers_detected: list[str] = Field(
        default_factory=list, description="AI providers detected"
    )
    payment_providers_detected: list[str] = Field(
        default_factory=list, description="Payment providers detected"
    )


class InstrumentationPlan(BaseModel):
    """Complete instrumentation plan output."""

    metadata: dict = Field(description="Plan metadata")
    codebase_analysis: CodebaseAnalysis = Field(description="Codebase analysis results")
    existing_instrumentation: list[ExistingInstrumentation] = Field(
        default_factory=list, description="Existing tracking found"
    )
    gaps: list[InstrumentationGap] = Field(
        default_factory=list, description="Instrumentation gaps"
    )
    recommended_events: list[EventSchema] = Field(
        default_factory=list, description="Events to implement"
    )
    database_migrations: list[DatabaseMigration] = Field(
        default_factory=list, description="Database changes needed"
    )
    implementation_phases: list[dict] = Field(
        default_factory=list, description="Phased implementation plan"
    )
    estimated_effort_days: int = Field(
        default=0, description="Estimated implementation effort"
    )

    @field_validator("estimated_effort_days")
    @classmethod
    def validate_effort(cls, v: int) -> int:
        """Ensure effort is reasonable."""
        if v < 0:
            raise ValueError("Effort cannot be negative")
        if v > 365:
            raise ValueError("Effort seems unreasonably high (>1 year)")
        return v


class InstrumentationAnalyzer:
    """Analyzes codebases for financial tracking instrumentation."""

    # Pattern definitions for codebase analysis
    FRAMEWORK_PATTERNS = {
        Framework.DJANGO: [
            r"from django\.",
            r"import django",
            r"Django",
            r"settings\.py",
        ],
        Framework.FLASK: [r"from flask import", r"Flask\(", r"@app\.route"],
        Framework.FASTAPI: [
            r"from fastapi import",
            r"FastAPI\(",
            r"@app\.(get|post|put|delete)",
        ],
        Framework.EXPRESS: [
            r"require\(['\"]express['\"]\)",
            r"express\(\)",
            r"app\.(get|post|put|delete)",
        ],
        Framework.RAILS: [
            r"Rails\.application",
            r"ApplicationController",
            r"ActiveRecord::Base",
        ],
        Framework.NEXTJS: [r"next/", r"getServerSideProps", r"getStaticProps"],
    }

    DATABASE_PATTERNS = {
        DatabaseType.POSTGRESQL: [r"postgresql", r"psycopg2", r"postgres"],
        DatabaseType.MYSQL: [r"mysql", r"pymysql", r"MySQLdb"],
        DatabaseType.SQLITE: [r"sqlite3", r"\.db$"],
        DatabaseType.MONGODB: [r"mongodb", r"pymongo", r"mongoose"],
    }

    SUBSCRIPTION_PATTERNS = [
        r"subscription",
        r"billing",
        r"payment",
        r"invoice",
        r"plan",
        r"tier",
        r"mrr",
        r"arr",
    ]

    AI_PROVIDER_PATTERNS = {
        "anthropic": [r"anthropic", r"claude", r"from anthropic import"],
        "openai": [r"openai", r"gpt-", r"from openai import"],
        "google": [r"google\.generativeai", r"gemini", r"palm"],
        "aws_bedrock": [r"bedrock", r"boto3.*bedrock"],
        "azure_openai": [r"azure.*openai", r"AzureOpenAI"],
    }

    PAYMENT_PROVIDER_PATTERNS = {
        "stripe": [r"stripe", r"from stripe import"],
        "paypal": [r"paypal", r"braintree"],
        "square": [r"square", r"from square"],
        "paddle": [r"paddle"],
        "chargebee": [r"chargebee"],
    }

    TRACKING_PATTERNS = [
        r"track\(",
        r"analytics\.",
        r"segment\.",
        r"amplitude\.",
        r"mixpanel\.",
        r"log_event",
        r"emit_event",
        r"send_event",
    ]

    def __init__(self, codebase_path: str):
        """Initialize analyzer with path to codebase.

        Args:
            codebase_path: Path to codebase root directory
        """
        self.codebase_path = Path(codebase_path)
        if not self.codebase_path.exists():
            raise ValueError(f"Codebase path does not exist: {codebase_path}")

        self.analysis = CodebaseAnalysis(
            framework=Framework.UNKNOWN, database_type=DatabaseType.UNKNOWN
        )
        self.existing_instrumentation: list[ExistingInstrumentation] = []
        self.gaps: list[InstrumentationGap] = []
        self.recommended_events: list[EventSchema] = []
        self.database_migrations: list[DatabaseMigration] = []

    def analyze(self) -> InstrumentationPlan:
        """Perform complete codebase analysis and generate instrumentation plan.

        Returns:
            Complete instrumentation plan
        """
        print("Starting codebase analysis...")

        # Step 1: Detect framework and database
        self._detect_framework()
        self._detect_database()

        # Step 2: Scan for existing instrumentation
        self._scan_existing_instrumentation()

        # Step 3: Detect subscription and AI patterns
        self._detect_subscription_patterns()
        self._detect_ai_patterns()
        self._detect_payment_providers()

        # Step 4: Identify gaps
        self._identify_gaps()

        # Step 5: Generate recommendations
        self._generate_event_recommendations()
        self._generate_database_migrations()

        # Step 6: Create implementation phases
        phases = self._create_implementation_phases()

        # Step 7: Estimate effort
        effort = self._estimate_effort()

        # Build plan
        plan = InstrumentationPlan(
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "codebase_path": str(self.codebase_path),
                "version": "1.0.0",
                "author": "product-finance instrumentation analyzer",
            },
            codebase_analysis=self.analysis,
            existing_instrumentation=self.existing_instrumentation,
            gaps=self.gaps,
            recommended_events=self.recommended_events,
            database_migrations=self.database_migrations,
            implementation_phases=phases,
            estimated_effort_days=effort,
        )

        print("\nAnalysis complete!")
        print(f"Framework: {self.analysis.framework.value}")
        print(f"Database: {self.analysis.database_type.value}")
        print(f"Existing tracking: {len(self.existing_instrumentation)} events")
        print(f"Gaps identified: {len(self.gaps)}")
        print(f"Recommended events: {len(self.recommended_events)}")
        print(f"Database migrations: {len(self.database_migrations)}")
        print(f"Estimated effort: {effort} days")

        return plan

    def _scan_files(self, pattern: str = "*") -> list[Path]:
        """Recursively scan codebase for files matching pattern.

        Args:
            pattern: Glob pattern for files to scan

        Returns:
            List of matching file paths
        """
        files = []
        try:
            for file_path in self.codebase_path.rglob(pattern):
                if file_path.is_file():
                    # Skip common directories
                    skip_dirs = {
                        "node_modules",
                        "venv",
                        ".git",
                        "__pycache__",
                        "dist",
                        "build",
                        ".next",
                    }
                    if not any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                        files.append(file_path)
        except PermissionError:
            pass
        return files

    def _read_file_content(self, file_path: Path) -> str:
        """Safely read file content.

        Args:
            file_path: Path to file

        Returns:
            File content as string, empty string if not readable
        """
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _detect_framework(self) -> None:
        """Detect web framework used in codebase."""
        print("Detecting framework...")

        # Scan Python files
        python_files = self._scan_files("*.py")[:100]  # Sample first 100 files
        js_files = self._scan_files("*.js")[:50]
        ts_files = self._scan_files("*.ts")[:50]

        all_files = python_files + js_files + ts_files

        framework_scores = {fw: 0 for fw in Framework}

        for file_path in all_files:
            content = self._read_file_content(file_path)

            for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        framework_scores[framework] += 1

        # Get framework with highest score
        max_score = max(framework_scores.values())
        if max_score > 0:
            self.analysis.framework = max(
                framework_scores, key=framework_scores.get
            )
        else:
            self.analysis.framework = Framework.UNKNOWN

    def _detect_database(self) -> None:
        """Detect database type used in codebase."""
        print("Detecting database...")

        files = self._scan_files("*.py")[:50] + self._scan_files("*.js")[:50]

        db_scores = {db: 0 for db in DatabaseType}

        for file_path in files:
            content = self._read_file_content(file_path)

            for db_type, patterns in self.DATABASE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        db_scores[db_type] += 1

        max_score = max(db_scores.values())
        if max_score > 0:
            self.analysis.database_type = max(db_scores, key=db_scores.get)
        else:
            self.analysis.database_type = DatabaseType.UNKNOWN

    def _scan_existing_instrumentation(self) -> None:
        """Scan for existing tracking and instrumentation."""
        print("Scanning for existing instrumentation...")

        files = self._scan_files("*.py") + self._scan_files("*.js") + self._scan_files("*.ts")

        for file_path in files[:200]:  # Sample files
            content = self._read_file_content(file_path)

            for pattern in self.TRACKING_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Try to extract event name
                    line_start = max(0, match.start() - 50)
                    line_end = min(len(content), match.end() + 100)
                    context = content[line_start:line_end]

                    # Basic event name extraction
                    event_name = "unknown_event"
                    event_match = re.search(r"['\"]([a-z_]+)['\"]", context)
                    if event_match:
                        event_name = event_match.group(1)

                    # Check if already tracked
                    if not any(
                        e.event_name == event_name and e.location == str(file_path)
                        for e in self.existing_instrumentation
                    ):
                        self.existing_instrumentation.append(
                            ExistingInstrumentation(
                                event_name=event_name,
                                location=str(file_path.relative_to(self.codebase_path)),
                                data_captured=["unknown"],
                                quality="unknown",
                                framework=self.analysis.framework.value,
                            )
                        )

        self.analysis.existing_tracking_count = len(self.existing_instrumentation)

    def _detect_subscription_patterns(self) -> None:
        """Detect subscription management code."""
        print("Detecting subscription patterns...")

        files = self._scan_files("*.py") + self._scan_files("*.js")

        subscription_score = 0
        for file_path in files[:100]:
            content = self._read_file_content(file_path)
            for pattern in self.SUBSCRIPTION_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    subscription_score += 1

        self.analysis.has_subscription_model = subscription_score > 5

    def _detect_ai_patterns(self) -> None:
        """Detect AI/LLM API usage."""
        print("Detecting AI patterns...")

        files = self._scan_files("*.py") + self._scan_files("*.js")

        providers_found = set()
        for file_path in files[:100]:
            content = self._read_file_content(file_path)

            for provider, patterns in self.AI_PROVIDER_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        providers_found.add(provider)

        self.analysis.ai_providers_detected = list(providers_found)
        self.analysis.has_ai_integration = len(providers_found) > 0

    def _detect_payment_providers(self) -> None:
        """Detect payment provider integrations."""
        print("Detecting payment providers...")

        files = self._scan_files("*.py") + self._scan_files("*.js")

        providers_found = set()
        for file_path in files[:100]:
            content = self._read_file_content(file_path)

            for provider, patterns in self.PAYMENT_PROVIDER_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        providers_found.add(provider)

        self.analysis.payment_providers_detected = list(providers_found)

    def _identify_gaps(self) -> None:
        """Identify instrumentation gaps."""
        print("Identifying instrumentation gaps...")

        # Define required metrics and their dependencies
        required_metrics = {
            "MRR": ["subscription_created", "subscription_upgraded", "subscription_downgraded", "subscription_cancelled"],  # noqa: E501
            "Churn Rate": ["subscription_cancelled", "customer_id", "subscription_start_date"],
            "CAC": ["customer_created", "marketing_spend", "sales_expense"],
            "LTV": ["subscription_created", "payment_received", "subscription_lifetime"],
            "AI Cost": ["ai_request_completed", "ai_cost_incurred"],
            "Net Revenue Retention": ["subscription_upgraded", "subscription_downgraded", "subscription_cancelled"],  # noqa: E501
        }

        # Check what's missing
        tracked_events = {inst.event_name for inst in self.existing_instrumentation}

        for metric, required_events in required_metrics.items():
            missing = [e for e in required_events if e not in tracked_events]

            if missing:
                # Determine impact based on metric importance
                impact = Priority.HIGH
                if metric in ["MRR", "Churn Rate"]:
                    impact = Priority.CRITICAL
                elif metric in ["CAC", "LTV"]:
                    impact = Priority.HIGH
                else:
                    impact = Priority.MEDIUM

                self.gaps.append(
                    InstrumentationGap(
                        metric=metric,
                        missing_data=missing,
                        impact=impact,
                        enables_metrics=[metric],
                    )
                )

    def _generate_event_recommendations(self) -> None:
        """Generate recommended events to implement."""
        print("Generating event recommendations...")

        # Subscription events (if subscription model detected)
        if self.analysis.has_subscription_model:
            self.recommended_events.extend(self._generate_subscription_events())

        # AI events (if AI integration detected)
        if self.analysis.has_ai_integration:
            self.recommended_events.extend(self._generate_ai_events())

        # Standard business events
        self.recommended_events.extend(self._generate_standard_events())

    def _generate_subscription_events(self) -> list[EventSchema]:
        """Generate subscription tracking event schemas."""
        events = []

        # Subscription created
        events.append(
            EventSchema(
                event_name="subscription_created",
                event_category=EventCategory.SUBSCRIPTION,
                description="Emitted when a new subscription is created",
                trigger="When customer completes signup and subscription is activated",
                priority=Priority.CRITICAL,
                required_fields=[
                    {"field_name": "customer_id", "field_type": "string", "description": "Unique customer identifier"},  # noqa: E501
                    {"field_name": "subscription_id", "field_type": "string", "description": "Unique subscription identifier"},  # noqa: E501
                    {"field_name": "plan", "field_type": "string", "description": "Subscription plan name"},  # noqa: E501
                    {"field_name": "mrr", "field_type": "number", "description": "Monthly recurring revenue"},  # noqa: E501
                    {"field_name": "start_date", "field_type": "date", "description": "Subscription start date"},  # noqa: E501
                ],
                optional_fields=[
                    {"field_name": "trial", "field_type": "boolean", "description": "Whether this is a trial"},  # noqa: E501
                    {"field_name": "source", "field_type": "string", "description": "Acquisition source"},  # noqa: E501
                ],
                enables_metrics=["MRR", "ARR", "New Subscriptions", "Customer Count"],
                example_code=self._get_example_code("subscription_created"),
            )
        )

        # Subscription cancelled
        events.append(
            EventSchema(
                event_name="subscription_cancelled",
                event_category=EventCategory.SUBSCRIPTION,
                description="Emitted when a subscription is cancelled",
                trigger="When customer cancels subscription",
                priority=Priority.CRITICAL,
                required_fields=[
                    {"field_name": "customer_id", "field_type": "string", "description": "Unique customer identifier"},  # noqa: E501
                    {"field_name": "subscription_id", "field_type": "string", "description": "Unique subscription identifier"},  # noqa: E501
                    {"field_name": "churned_mrr", "field_type": "number", "description": "MRR lost"},  # noqa: E501
                    {"field_name": "cancellation_reason", "field_type": "string", "description": "Reason for cancellation"},  # noqa: E501
                    {"field_name": "subscription_lifetime_days", "field_type": "integer", "description": "Days subscribed"},  # noqa: E501
                ],
                enables_metrics=["Churn Rate", "Churned MRR", "Average Lifetime"],
                example_code=self._get_example_code("subscription_cancelled"),
            )
        )

        return events

    def _generate_ai_events(self) -> list[EventSchema]:
        """Generate AI tracking event schemas."""
        events = []

        # AI request completed
        events.append(
            EventSchema(
                event_name="ai_request_completed",
                event_category=EventCategory.AI,
                description="Emitted when an AI API request completes",
                trigger="After successful AI API call completion",
                priority=Priority.HIGH,
                required_fields=[
                    {"field_name": "user_id", "field_type": "string", "description": "User identifier"},  # noqa: E501
                    {"field_name": "request_id", "field_type": "string", "description": "Request identifier"},  # noqa: E501
                    {"field_name": "model", "field_type": "string", "description": "AI model used"},
                    {"field_name": "provider", "field_type": "string", "description": "AI provider"},  # noqa: E501
                    {"field_name": "tokens_input", "field_type": "integer", "description": "Input tokens"},  # noqa: E501
                    {"field_name": "tokens_output", "field_type": "integer", "description": "Output tokens"},  # noqa: E501
                    {"field_name": "cost", "field_type": "number", "description": "Cost in USD"},
                ],
                enables_metrics=["AI Cost per Request", "AI Cost per User", "Token Usage"],
                example_code=self._get_example_code("ai_request_completed"),
            )
        )

        return events

    def _generate_standard_events(self) -> list[EventSchema]:
        """Generate standard business event schemas."""
        events = []

        # Payment received
        events.append(
            EventSchema(
                event_name="payment_received",
                event_category=EventCategory.BILLING,
                description="Emitted when payment is successfully received",
                trigger="When payment processor confirms payment",
                priority=Priority.HIGH,
                required_fields=[
                    {"field_name": "customer_id", "field_type": "string", "description": "Customer identifier"},  # noqa: E501
                    {"field_name": "payment_id", "field_type": "string", "description": "Payment identifier"},  # noqa: E501
                    {"field_name": "amount", "field_type": "number", "description": "Payment amount"},  # noqa: E501
                    {"field_name": "payment_date", "field_type": "date", "description": "Payment date"},  # noqa: E501
                ],
                enables_metrics=["Revenue", "Payment Collection Efficiency"],
                example_code=self._get_example_code("payment_received"),
            )
        )

        return events

    def _generate_database_migrations(self) -> None:
        """Generate database migration suggestions."""
        print("Generating database migration suggestions...")

        # Subscription tracking table (if needed)
        if self.analysis.has_subscription_model and not any(
            "subscription" in inst.event_name.lower()
            for inst in self.existing_instrumentation
        ):
            self.database_migrations.append(
                DatabaseMigration(
                    migration_type="new_table",
                    table_name="financial_events",
                    purpose="Store subscription lifecycle events for financial analytics",
                    priority=Priority.HIGH,
                    postgresql_script=self._generate_postgresql_migration("financial_events"),
                    mysql_script=self._generate_mysql_migration("financial_events"),
                )
            )

        # AI cost tracking table (if needed)
        if self.analysis.has_ai_integration:
            self.database_migrations.append(
                DatabaseMigration(
                    migration_type="new_table",
                    table_name="ai_usage_events",
                    purpose="Track AI API usage and costs for ROI analysis",
                    priority=Priority.HIGH,
                    postgresql_script=self._generate_postgresql_migration("ai_usage_events"),
                    mysql_script=self._generate_mysql_migration("ai_usage_events"),
                )
            )

    def _generate_postgresql_migration(self, table_name: str) -> str:
        """Generate PostgreSQL migration script.

        Args:
            table_name: Name of table to create

        Returns:
            SQL migration script
        """
        if table_name == "financial_events":
            return """
-- Create financial_events table for subscription tracking
CREATE TABLE IF NOT EXISTS financial_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),
    event_data JSONB NOT NULL,
    mrr_impact DECIMAL(10, 2),
    arr_impact DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_customer_id (customer_id),
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_event_name (event_name),
    INDEX idx_created_at (created_at)
);

-- Create index for JSONB queries
CREATE INDEX idx_event_data_gin ON financial_events USING GIN (event_data);

COMMENT ON TABLE financial_events IS 'Subscription lifecycle events for financial metrics';
"""
        elif table_name == "ai_usage_events":
            return """
-- Create ai_usage_events table for AI cost tracking
CREATE TABLE IF NOT EXISTS ai_usage_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER,
    feature VARCHAR(255),
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_model (model),
    INDEX idx_created_at (created_at)
);

-- Create index for cost analysis
CREATE INDEX idx_cost_analysis ON ai_usage_events (customer_id, created_at, cost_usd);

COMMENT ON TABLE ai_usage_events IS 'Tracks AI API usage and costs for ROI calculation';
"""
        return ""

    def _generate_mysql_migration(self, table_name: str) -> str:
        """Generate MySQL migration script.

        Args:
            table_name: Name of table to create

        Returns:
            SQL migration script
        """
        if table_name == "financial_events":
            return """
-- Create financial_events table for subscription tracking
CREATE TABLE IF NOT EXISTS financial_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),
    event_data JSON NOT NULL,
    mrr_impact DECIMAL(10, 2),
    arr_impact DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_event_name (event_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
        elif table_name == "ai_usage_events":
            return """
-- Create ai_usage_events table for AI cost tracking
CREATE TABLE IF NOT EXISTS ai_usage_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER,
    feature VARCHAR(255),
    event_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_model (model),
    INDEX idx_created_at (created_at),
    INDEX idx_cost_analysis (customer_id, created_at, cost_usd)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
        return ""

    def _get_example_code(self, event_name: str) -> str:
        """Get example implementation code for event.

        Args:
            event_name: Name of event

        Returns:
            Example code snippet
        """
        if self.analysis.framework == Framework.DJANGO:
            return self._get_django_example(event_name)
        elif self.analysis.framework == Framework.FLASK:
            return self._get_flask_example(event_name)
        elif self.analysis.framework == Framework.FASTAPI:
            return self._get_fastapi_example(event_name)
        elif self.analysis.framework == Framework.EXPRESS:
            return self._get_express_example(event_name)
        else:
            return self._get_generic_example(event_name)

    def _get_django_example(self, event_name: str) -> str:
        """Get Django-specific example code."""
        if event_name == "subscription_created":
            return """
# In your subscription creation view or signal
from datetime import datetime
import json

def create_subscription(customer, plan):
    subscription = Subscription.objects.create(
        customer=customer,
        plan=plan,
        start_date=datetime.now()
    )

    # Track financial event
    track_event('subscription_created', {
        'customer_id': str(customer.id),
        'subscription_id': str(subscription.id),
        'plan': plan.name,
        'mrr': float(plan.monthly_price),
        'arr': float(plan.monthly_price * 12),
        'start_date': subscription.start_date.isoformat(),
        'timestamp': datetime.utcnow().isoformat(),
    })

    return subscription
"""
        return ""

    def _get_flask_example(self, event_name: str) -> str:
        """Get Flask-specific example code."""
        if event_name == "subscription_created":
            return """
# In your subscription route
from datetime import datetime

@app.route('/subscriptions', methods=['POST'])
def create_subscription():
    data = request.get_json()

    subscription = {
        'id': generate_id(),
        'customer_id': data['customer_id'],
        'plan': data['plan'],
        'start_date': datetime.utcnow().isoformat()
    }

    # Track financial event
    track_event('subscription_created', {
        'customer_id': subscription['customer_id'],
        'subscription_id': subscription['id'],
        'plan': subscription['plan'],
        'mrr': data['monthly_price'],
        'start_date': subscription['start_date'],
        'timestamp': datetime.utcnow().isoformat(),
    })

    return jsonify(subscription), 201
"""
        return ""

    def _get_fastapi_example(self, event_name: str) -> str:
        """Get FastAPI-specific example code."""
        if event_name == "subscription_created":
            return """
# In your subscription router
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

@router.post('/subscriptions')
async def create_subscription(subscription_data: SubscriptionCreate):
    subscription = await db.subscriptions.insert_one({
        'customer_id': subscription_data.customer_id,
        'plan': subscription_data.plan,
        'start_date': datetime.utcnow()
    })

    # Track financial event
    await track_event('subscription_created', {
        'customer_id': subscription_data.customer_id,
        'subscription_id': str(subscription.inserted_id),
        'plan': subscription_data.plan,
        'mrr': subscription_data.monthly_price,
        'timestamp': datetime.utcnow().isoformat(),
    })

    return subscription
"""
        return ""

    def _get_express_example(self, event_name: str) -> str:
        """Get Express-specific example code."""
        if event_name == "subscription_created":
            return """
// In your subscription route
app.post('/subscriptions', async (req, res) => {
    const { customer_id, plan, monthly_price } = req.body;

    const subscription = await db.subscriptions.create({
        customer_id,
        plan,
        start_date: new Date()
    });

    // Track financial event
    await trackEvent('subscription_created', {
        customer_id,
        subscription_id: subscription.id,
        plan,
        mrr: monthly_price,
        arr: monthly_price * 12,
        start_date: subscription.start_date.toISOString(),
        timestamp: new Date().toISOString(),
    });

    res.status(201).json(subscription);
});
"""
        return ""

    def _get_generic_example(self, event_name: str) -> str:
        """Get generic example code."""
        return f"""
# Track event: {event_name}
track_event('{event_name}', {{
    'customer_id': customer.id,
    'timestamp': datetime.utcnow().isoformat(),
    # Add required fields based on event schema
}})
"""

    def _create_implementation_phases(self) -> list[dict]:
        """Create phased implementation plan.

        Returns:
            List of implementation phases
        """
        phases = []

        # Phase 1: Critical subscription tracking
        phase1_events = [
            e for e in self.recommended_events if e.priority == Priority.CRITICAL
        ]
        if phase1_events:
            phases.append(
                {
                    "phase_number": 1,
                    "phase_name": "Critical Subscription Tracking",
                    "duration": "1-2 weeks",
                    "objectives": [
                        "Implement core subscription lifecycle tracking",
                        "Enable MRR/ARR calculation",
                        "Enable churn rate tracking",
                    ],
                    "events_to_implement": [e.event_name for e in phase1_events],
                    "metrics_enabled": ["MRR", "ARR", "Churn Rate", "New Subscriptions"],
                }
            )

        # Phase 2: AI cost tracking (if applicable)
        if self.analysis.has_ai_integration:
            ai_events = [
                e
                for e in self.recommended_events
                if e.event_category == EventCategory.AI
            ]
            if ai_events:
                phases.append(
                    {
                        "phase_number": 2,
                        "phase_name": "AI Cost Tracking",
                        "duration": "1 week",
                        "objectives": [
                            "Track AI API usage and costs",
                            "Enable AI ROI calculation",
                        ],
                        "events_to_implement": [e.event_name for e in ai_events],
                        "metrics_enabled": [
                            "AI Cost per Request",
                            "AI Cost per User",
                            "AI ROI",
                        ],
                    }
                )

        # Phase 3: Additional business metrics
        remaining_events = [
            e
            for e in self.recommended_events
            if e.priority in [Priority.HIGH, Priority.MEDIUM]
            and e not in phase1_events
        ]
        if remaining_events:
            phases.append(
                {
                    "phase_number": len(phases) + 1,
                    "phase_name": "Additional Business Metrics",
                    "duration": "1-2 weeks",
                    "objectives": ["Complete instrumentation coverage"],
                    "events_to_implement": [e.event_name for e in remaining_events],
                    "metrics_enabled": ["CAC", "LTV", "Payment Efficiency"],
                }
            )

        return phases

    def _estimate_effort(self) -> int:
        """Estimate implementation effort in days.

        Returns:
            Estimated effort in days
        """
        # Base effort
        effort = 0

        # Events: 0.5-2 days per event depending on priority
        for event in self.recommended_events:
            if event.priority == Priority.CRITICAL:
                effort += 2
            elif event.priority == Priority.HIGH:
                effort += 1
            else:
                effort += 0.5

        # Database migrations: 1-2 days per migration
        effort += len(self.database_migrations) * 1.5

        # Testing and QA: 30% overhead
        effort *= 1.3

        # Round up
        return int(effort) + 1


def main() -> None:
    """CLI entry point for instrumentation analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze codebase and generate financial instrumentation plan"
    )
    parser.add_argument(
        "codebase_path", type=str, help="Path to codebase root directory"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="instrumentation-plan.json",
        help="Output file path (default: instrumentation-plan.json)",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    try:
        # Create analyzer and run analysis
        analyzer = InstrumentationAnalyzer(args.codebase_path)
        plan = analyzer.analyze()

        # Convert to dict for JSON serialization
        plan_dict = plan.model_dump()

        # Write output
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            if args.pretty:
                json.dump(plan_dict, f, indent=2, default=str)
            else:
                json.dump(plan_dict, f, default=str)

        print(f"\nInstrumentation plan written to: {output_path}")
        print(
            "\nNext steps:\n"
            "1. Review the generated plan\n"
            "2. Implement recommended events in phases\n"
            "3. Run database migrations\n"
            "4. Validate data quality\n"
        )

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
