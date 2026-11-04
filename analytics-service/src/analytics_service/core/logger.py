"""Logging configuration."""

import logging
import sys
import json

from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Форматтер для вывода логов в формате JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "time": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "task_id"):
            log_record["task_id"] = record.task_id
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)
    
def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
