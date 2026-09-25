"""ClickHouse repository for analytics data."""

import structlog
from clickhouse_connect.driver import Client

from analytics_service.schemas.analytics import TaskAnalyticsRecord

logger = structlog.get_logger()


class AnalyticsRepository:
    """Repository for analytics data in ClickHouse."""

    def __init__(self, client: Client) -> None:
        """Initialize repository."""
        self.client = client

    async def save_task_analytics(self, record: TaskAnalyticsRecord) -> None:
        """Save task analytics record to ClickHouse."""
        try:
            query = """
            INSERT INTO task_analytics (
                event_id,
                event_type,
                event_timestamp,
                task_id,
                task_title,
                task_description,
                task_status,
                user_id,
                task_created_at,
                task_updated_at,
                processing_timestamp
            ) VALUES
            """

            data = [
                [
                    str(record.event_id),
                    record.event_type.value,
                    record.event_timestamp,
                    str(record.task_id),
                    record.task_title,
                    record.task_description,
                    record.task_status.value,
                    str(record.user_id) if record.user_id else None,
                    record.task_created_at,
                    record.task_updated_at,
                    record.processing_timestamp,
                ]
            ]

            self.client.insert(
                table="task_analytics",
                data=data,
                column_names=[
                    "event_id",
                    "event_type",
                    "event_timestamp",
                    "task_id",
                    "task_title",
                    "task_description",
                    "task_status",
                    "user_id",
                    "task_created_at",
                    "task_updated_at",
                    "processing_timestamp",
                ],
            )

            logger.info(
                "Task analytics saved to ClickHouse",
                event_id=str(record.event_id),
                event_type=record.event_type.value,
                task_id=str(record.task_id),
            )

        except Exception as e:
            logger.error(
                "Failed to save task analytics to ClickHouse",
                event_id=str(record.event_id),
                error=str(e),
            )
            raise
