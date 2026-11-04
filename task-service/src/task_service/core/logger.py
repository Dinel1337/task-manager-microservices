import logging
import sys
import json

from datetime import datetime
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union

from task_service.core.config import settings

LOG_COLORS = {
    logging.DEBUG: "\033[36m",  # Cyan
    logging.INFO: "\033[32m",  # Green
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[35m",  # Magenta
}

RESET_COLOR = "\033[0m"

FuncType = TypeVar("FuncType", bound=Callable[..., Union[Any, Awaitable[Any]]])


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "task_id"):
            log_record["task_id"] = record.task_id
        return json.dumps(log_record)


def is_coroutine_function(func: Callable[..., Any]) -> bool:
    return bool(func.__code__.co_flags & 0x80)


def setup_logging() -> None:
    """Настройка базового логирования."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Убираем все существующие handlers
    root_logger.handlers.clear()
    
    # Добавляем наш colored handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        JsonFormatter()
    )
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = True  # Используем root logger
    return logger


async def _async_log_execution(
    logger: logging.Logger,
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    **kwargs: Any,
) -> Any:
    try:
        result = await func(*args, **kwargs)
        logger.info(f"Successfully executed {func.__name__}")
        return result
    except Exception as error:
        logger.error(f"Error in {func.__name__}: {error}")
        raise error


def _sync_log_execution(
    logger: logging.Logger,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    try:
        result = func(*args, **kwargs)
        logger.info(f"Successfully executed {func.__name__}")
        return result
    except Exception as error:
        logger.error(f"Error in {func.__name__}: {error}")
        raise error


def log(logger: logging.Logger) -> Callable[[FuncType], FuncType]:
    def decorator(func: FuncType) -> FuncType:
        if is_coroutine_function(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _async_log_execution(logger, func, *args, **kwargs)

            return async_wrapper  # type: ignore
        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return _sync_log_execution(logger, func, *args, **kwargs)

            return sync_wrapper  # type: ignore

    return decorator
