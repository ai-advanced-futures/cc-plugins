"""
Competitive Intelligence Plugin - Phase 3: Intelligence Gathering

Orchestrates data collection from multiple sources.

Key Features:
- Multi-source data collection orchestration
- Plugin integration coordination
- Web research coordination
- Script execution coordination
- Task tracking and status management
- Data validation

Data Sources:
- PLUGIN: Claude Code plugins (GitHub, databases, APIs)
- WEB_RESEARCH: Web scraping and research
- SCRIPT: Custom data collection scripts
- MANUAL: Manual data entry/research
"""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DataSourceType(Enum):
    """
    Types of data sources.

    - PLUGIN: Claude Code plugins (GitHub, APIs, etc.)
    - WEB_RESEARCH: Web research and scraping
    - SCRIPT: Custom scripts for data collection
    - MANUAL: Manual research and data entry
    """
    PLUGIN = "plugin"
    WEB_RESEARCH = "web_research"
    SCRIPT = "script"
    MANUAL = "manual"


class GatheringTaskStatus(Enum):
    """
    Status of gathering task.

    - PENDING: Task created, not yet started
    - IN_PROGRESS: Task currently executing
    - COMPLETED: Task finished successfully
    - FAILED: Task failed with error
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DataSource:
    """
    Data source configuration.

    Attributes:
        source_type: Type of data source
        name: Name/identifier of source
        config: Configuration for source
        priority: Priority level (high/medium/low)
    """
    source_type: DataSourceType
    name: str
    config: Dict[str, Any]
    priority: str  # "high", "medium", "low"


@dataclass
class GatheringTask:
    """
    Data gathering task.

    Attributes:
        task_id: Unique task identifier
        source: Data source for this task
        target: Target (competitor ID) for gathering
        status: Current status of task
        result: Gathered data (when completed)
        error: Error message (when failed)
    """
    task_id: str
    source: DataSource
    target: str
    status: GatheringTaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IntelligenceGatherer:
    """
    Intelligence Gathering coordinator.

    Orchestrates data collection from multiple sources.

    Workflow:
    1. Identify data sources based on context
    2. Create gathering tasks for each competitor/source
    3. Execute tasks (plugin calls, web research, scripts)
    4. Track task status and results
    5. Validate gathered data
    6. Return results to workflow engine
    """

    def __init__(self, engine):
        """
        Initialize intelligence gatherer.

        Args:
            engine: WorkflowEngine instance
        """
        self.engine = engine
        self.tasks: List[GatheringTask] = []
        self.data_sources: List[DataSource] = []

    def add_data_source(self, source: DataSource):
        """
        Add data source.

        Args:
            source: DataSource to add
        """
        self.data_sources.append(source)

    def create_task(
        self,
        source: DataSource,
        target: str,
        task_id: Optional[str] = None
    ) -> GatheringTask:
        """
        Create gathering task.

        Args:
            source: Data source
            target: Target competitor
            task_id: Optional task ID

        Returns:
            GatheringTask
        """
        if task_id is None:
            task_id = f"task-{uuid.uuid4().hex[:8]}"

        task = GatheringTask(
            task_id=task_id,
            source=source,
            target=target,
            status=GatheringTaskStatus.PENDING,
            result=None,
            error=None
        )

        self.tasks.append(task)
        return task

    def get_tasks_by_status(self, status: GatheringTaskStatus) -> List[GatheringTask]:
        """
        Get tasks by status.

        Args:
            status: Task status to filter by

        Returns:
            List of tasks with that status
        """
        return [t for t in self.tasks if t.status == status]

    def execute_task(self, task: GatheringTask) -> Dict[str, Any]:
        """
        Execute gathering task.

        In real implementation, would call plugins, run scripts, etc.
        For now, returns placeholder data.

        Args:
            task: Task to execute

        Returns:
            Gathered data
        """
        task.status = GatheringTaskStatus.IN_PROGRESS

        try:
            # Placeholder implementation
            # Real implementation would:
            # - Call plugin if source_type is PLUGIN
            # - Run web research if source_type is WEB_RESEARCH
            # - Execute script if source_type is SCRIPT
            # - Prompt for manual entry if source_type is MANUAL

            data = {
                "competitor_id": task.target,
                "source": task.source.name,
                "source_type": task.source.source_type.value,
                "data": {
                    "name": task.target,
                    "description": f"Data gathered from {task.source.name}",
                    "features": [],
                    "pricing": {}
                }
            }

            task.result = data
            task.status = GatheringTaskStatus.COMPLETED

            return data

        except Exception as e:
            task.status = GatheringTaskStatus.FAILED
            task.error = str(e)
            return {}

    def run_gathering(self) -> Dict[str, Any]:
        """
        Run intelligence gathering process.

        Returns:
            Dict with gathering results
        """
        # Get competitors from engine state
        competitors = self.engine.state.data.get("competitors", [])

        if not competitors:
            return {
                "tasks_created": 0,
                "tasks_completed": 0,
                "data_collected": {}
            }

        # Create tasks for each competitor/source combination
        for competitor in competitors:
            for source in self.data_sources:
                self.create_task(source, competitor)

        # Execute tasks
        completed_count = 0
        data_collected = {}

        for task in self.tasks:
            if task.status == GatheringTaskStatus.PENDING:
                result = self.execute_task(task)

                if task.status == GatheringTaskStatus.COMPLETED:
                    completed_count += 1

                    # Store result
                    if task.target not in data_collected:
                        data_collected[task.target] = []

                    data_collected[task.target].append(result)

        # Update engine state
        self.engine.update_data({
            "gathered_data": data_collected,
            "gathering_completed": True
        })

        return {
            "tasks_created": len(self.tasks),
            "tasks_completed": completed_count,
            "data_collected": data_collected
        }


def create_gathering_task(
    source: DataSource,
    target: str,
    task_id: Optional[str] = None
) -> GatheringTask:
    """
    Convenience function to create gathering task.

    Args:
        source: Data source
        target: Target competitor
        task_id: Optional task ID

    Returns:
        GatheringTask
    """
    if task_id is None:
        task_id = f"task-{uuid.uuid4().hex[:8]}"

    return GatheringTask(
        task_id=task_id,
        source=source,
        target=target,
        status=GatheringTaskStatus.PENDING,
        result=None,
        error=None
    )


def validate_gathered_data(
    data: Dict[str, Any],
    required_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate gathered data.

    Args:
        data: Data to validate
        required_fields: Optional list of required fields

    Returns:
        Dict with validation result
    """
    if not data:
        return {
            "valid": False,
            "errors": ["Data is empty"]
        }

    errors = []

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

    if errors:
        return {
            "valid": False,
            "errors": errors
        }

    return {
        "valid": True
    }


def gather_intelligence(
    competitors: List[str],
    sources: List[DataSource]
) -> Dict[str, Any]:
    """
    Gather intelligence for competitors from sources.

    Args:
        competitors: List of competitor IDs
        sources: List of data sources

    Returns:
        Dict with gathered intelligence
    """
    data_collected = {}

    for competitor in competitors:
        competitor_data = []

        for source in sources:
            # Placeholder data gathering
            # Real implementation would call actual sources

            data = {
                "competitor_id": competitor,
                "source": source.name,
                "source_type": source.source_type.value,
                "data": {
                    "name": competitor,
                    "features": [],
                    "pricing": {}
                }
            }

            competitor_data.append(data)

        data_collected[competitor] = competitor_data

    return {
        "competitors": competitors,
        "data_collected": data_collected,
        "sources_used": [s.name for s in sources]
    }


# Convenience functions

def create_plugin_source(
    name: str,
    config: Dict[str, Any],
    priority: str = "high"
) -> DataSource:
    """
    Create plugin data source.

    Args:
        name: Plugin name
        config: Plugin configuration
        priority: Priority level

    Returns:
        DataSource
    """
    return DataSource(
        source_type=DataSourceType.PLUGIN,
        name=name,
        config=config,
        priority=priority
    )


def create_web_research_source(
    name: str,
    config: Dict[str, Any],
    priority: str = "medium"
) -> DataSource:
    """
    Create web research data source.

    Args:
        name: Source name
        config: Research configuration
        priority: Priority level

    Returns:
        DataSource
    """
    return DataSource(
        source_type=DataSourceType.WEB_RESEARCH,
        name=name,
        config=config,
        priority=priority
    )


def create_script_source(
    name: str,
    config: Dict[str, Any],
    priority: str = "medium"
) -> DataSource:
    """
    Create script data source.

    Args:
        name: Script name
        config: Script configuration
        priority: Priority level

    Returns:
        DataSource
    """
    return DataSource(
        source_type=DataSourceType.SCRIPT,
        name=name,
        config=config,
        priority=priority
    )
