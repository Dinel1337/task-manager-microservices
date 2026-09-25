"""Main entry point."""

import asyncio

from analytics_service.app import create_app
from analytics_service.core.config import settings
from analytics_service.core.logger import get_logger
from analytics_service.infrastructure.kafka.consumer import start_kafka_consumer

logger = get_logger(__name__)


async def main():
    """Run the application."""
    import uvicorn
    
    config = uvicorn.Config(
        create_app(),
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
    server = uvicorn.Server(config)
    
    # Run Kafka consumer and FastAPI server in parallel
    await asyncio.gather(
        start_kafka_consumer(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
