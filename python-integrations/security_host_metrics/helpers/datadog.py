import json
from enum import Enum
from typing import Dict, Any


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warning"
    ERROR = "error"


def log_to_datadog(log_level: LogLevel, msg: str, info: Dict[str, Any]) -> None:
    log_line = {
        "status": log_level,
        "log_level": log_level,
        "msg": msg,
        "info": info,
    }

    print(json.dumps(log_line))
