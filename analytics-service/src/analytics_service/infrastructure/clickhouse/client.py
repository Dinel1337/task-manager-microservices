"""ClickHouse client manager."""

import clickhouse_connect

from analytics_service.core.config import ClickHouseSettings
from analytics_service.core.logger import get_logger

logger = get_logger(__name__)


class ClickHouseClient:
    """ClickHouse client wrapper."""

    def __init__(self, settings: ClickHouseSettings) -> None:
        """Initialize ClickHouse client."""
        self.settings = settings
        self.client = None

    async def start(self) -> None:
        """Start ClickHouse client."""
        self.client = clickhouse_connect.get_client(
            host=self.settings.host,
            port=self.settings.port,
            database=self.settings.database,
            username=self.settings.user,
            password=self.settings.password or "",
        )
        
        # Create table if not exists
        self.client.command("""
            CREATE TABLE IF NOT EXISTS task_analytics (
                event_id String,
                event_type String,
                timestamp DateTime64(3),
                task_id String,
                title String,
                description String,
                status String,
                user_id Nullable(String),
                assignee Nullable(String),
                priority Nullable(String),
                created_at DateTime64(3),
                updated_at DateTime64(3)
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, task_id)
        """)
        
        logger.info(f"ClickHouse client connected: {self.settings.host}:{self.settings.port}")

    async def stop(self) -> None:
        """Stop ClickHouse client."""
        if self.client:
            self.client.close()
            logger.info("ClickHouse client closed")

    def get_client(self):
        """Get ClickHouse client."""
        return self.client
