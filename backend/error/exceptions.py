import os
import logging
from datetime import datetime
from typing import Optional
from error.codes import ErrorClassification

# 1. ENVIRONMENT DETECTION (Defaults to 'development' if not set in .env)
ENV = os.getenv("APP_ENV", "development").lower()

logger = logging.getLogger("AgentCore")
logger.setLevel(logging.INFO)

# Avoid adding duplicate handlers if re-initialized by FastAPI reloads
if not logger.handlers:
    #  2. EVERYWHERE CONSOLE HANDLER (Crucial for Local Terminal & Live Systemd/Journald)
    stream_formatter = logging.Formatter("%(asctime)s | [%(levelname)s] | %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    #  3. CONDITIONAL LOCAL FILE LOGGING (Only runs on your local development machine)
    if ENV == "development":
        LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_filename = os.path.join(LOGS_DIR, f"agent_system_{datetime.now().strftime('%Y_%m_%d')}.log")
        
        file_formatter = logging.Formatter("%(asctime)s | [%(levelname)s] | %(message)s")
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


class ToolBaseException(Exception):
    """
    Unified Application Exception. Automatically structures signatures like:
    [TOOL_010-1001] -> Required runtime parameters were missing.
    """
    def __init__(
        self, 
        classification: ErrorClassification, 
        component_id: str, 
        custom_context: Optional[str] = None
    ):
        self.error_code = f"{component_id}-{classification.code_id}"
        self.message = custom_context if custom_context else classification.default_message
        super().__init__(f"[{self.error_code}] {self.message}")

        # Automatically streams out into the terminal (and systemd service log pipeline)
        logger.error(f"{self.error_code} | Failure Context: {self.message}")

    def to_dict(self):
        return {
            "status": "error",
            "error_code": self.error_code,
            "message": self.message
        }