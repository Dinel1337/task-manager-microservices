"""Use case for processing task events."""

from analytics_service.core.logger import get_logger
from analytics_service.infrastructure.postgres.database import Database
from analytics_service.infrastructure.postgres.repository import AnalyticsRepository
from analytics_service.schemas.events import TaskEventSchema

logger = get_logger(__name__)


class ProcessTaskEventUseCase:
    """Use case for processing task events from Kafka."""

    def __init__(self, database: Database, repository: AnalyticsRepository):
        self._database = database
        self._repository = repository

    async def execute(self, event: TaskEventSchema) -> None:
        """Process task event."""
        async with self._database.session() as session:
            await self._repository.save_task_event(session, event)
        
        logger.info(f"Processed task event: {event.event_type} for task {event.payload.get('task_id')}")
