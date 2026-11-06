"""
Shared enums for the product-finance plugin.

Single source of truth — all scripts import from here.
DO NOT re-define these enums in individual scripts.
"""
from enum import Enum


class MetricHealth(str, Enum):
    """Health status for any calculated metric."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class GrowthStage(str, Enum):
    """Company growth stage. ARR thresholds defined in constants.py."""
    EARLY = "early"
    GROWTH = "growth"
    SCALE = "scale"
    MATURE = "mature"


class AIProvider(str, Enum):
    """AI/LLM provider types (union of generic + ai_roi-specific providers)."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AWS = "aws"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"
    OTHER = "other"


class Framework(str, Enum):
    """Web/application frameworks for instrumentation."""
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    ANGULAR = "angular"
    DJANGO = "django"
    FASTAPI = "fastapi"
    EXPRESS = "express"
    OTHER = "other"


class DatabaseType(str, Enum):
    """Database types for migration generation."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    OTHER = "other"


class Priority(str, Enum):
    """Priority levels for instrumentation gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventCategory(str, Enum):
    """Event categories for financial instrumentation."""
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"
    USAGE = "usage"
    AI_USAGE = "ai_usage"
    CONVERSION = "conversion"
    CHURN = "churn"
    EXPANSION = "expansion"
