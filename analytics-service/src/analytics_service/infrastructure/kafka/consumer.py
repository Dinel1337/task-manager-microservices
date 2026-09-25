"""Kafka consumer using pure aiokafka."""

import json

from aiokafka import AIOKafkaConsumer

from analytics_service.core.config import settings
from analytics_service.core.logger import get_logger
from analytics_service.core.providers.setup import container
from analytics_service.domain.use_cases.process_task_event import ProcessTaskEventUseCase
from analytics_service.schemas.events import TaskEventSchema

logger = get_logger(__name__)


async def start_kafka_consumer():
    """Start Kafka consumer using aiokafka."""
    logger.info(f"🚀 Starting Kafka consumer: {settings.KAFKA_BOOTSTRAP_SERVERS}, topic: {settings.KAFKA_TOPIC_TASK_EVENTS}")
    
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_TASK_EVENTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
    )
    
    try:
        await consumer.start()
        logger.info(f"✅ Kafka consumer connected and ready!")
        
        async for msg in consumer:
            try:
                # Decode message
                data = json.loads(msg.value.decode('utf-8'))
                event = TaskEventSchema(**data)
                
                # Process event
                async with container() as request_container:
                    use_case = await request_container.get(ProcessTaskEventUseCase)
                    await use_case.execute(event)
                
                logger.info(f"✅ Processed: {event.event_type}, task_id={event.payload.get('task_id')}, offset={msg.offset}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process message: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"💥 Kafka consumer error: {e}", exc_info=True)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
