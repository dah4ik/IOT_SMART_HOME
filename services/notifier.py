"""
Notification service
"""

from datetime import datetime
from pathlib import Path

from config import DATA_DIR
from core.logging_setup import get_logger


logger = get_logger("iot_smart_home.notifier")

NOTIFICATION_LOG = Path(DATA_DIR) / "notifications.log"


class Notifier:
    """
    Simple notification service.
    """

    def __init__(self):
        self.notification_log = NOTIFICATION_LOG

    def notify(
            self,
            severity: str,
            subject: str,
            message: str,
    ):
        """
        Send notification.
        """

        timestamp = datetime.now().isoformat(timespec="seconds")

        notification_text = (
            f"{timestamp} | "
            f"{severity} | "
            f"{subject} | "
            f"{message}"
        )

        print("NOTIFICATION:", notification_text)
        logger.warning(notification_text)

        with open(self.notification_log, "a", encoding="utf-8") as file:
            file.write(notification_text + "\n")