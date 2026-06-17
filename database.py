import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import DB_PATH, DEVICES


def now() -> str:
    """
    Return current timestamp in ISO format.
    """

    return datetime.now().isoformat(timespec="seconds")


class SmartHomeDB:
    """
    SQLite database helper
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        """
        Create database connection.
        """

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """
        Initialize database tables.
        """

        with self.connect() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                                                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                       name TEXT UNIQUE NOT NULL,
                                                       type TEXT NOT NULL,
                                                       room TEXT,
                                                       description TEXT,
                                                       status TEXT DEFAULT 'unknown',
                                                       last_seen TEXT
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         timestamp TEXT NOT NULL,
                                                         device TEXT NOT NULL,
                                                         topic TEXT NOT NULL,
                                                         metric_key TEXT NOT NULL,
                                                         metric_value REAL,
                                                         raw_message TEXT
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                                                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                      timestamp TEXT NOT NULL,
                                                      device TEXT NOT NULL,
                                                      event_type TEXT NOT NULL,
                                                      event_value TEXT,
                                                      description TEXT,
                                                      raw_message TEXT
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS alarms (
                                                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                      timestamp TEXT NOT NULL,
                                                      severity TEXT NOT NULL,
                                                      device TEXT NOT NULL,
                                                      alarm_type TEXT NOT NULL,
                                                      message TEXT NOT NULL,
                                                      active INTEGER DEFAULT 1,
                                                      raw_message TEXT
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS relay_commands (
                                                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                              timestamp TEXT NOT NULL,
                                                              command INTEGER NOT NULL,
                                                              reason TEXT,
                                                              source TEXT
                )
                """
            )

            self._insert_default_devices(cur)

            conn.commit()

    def _insert_default_devices(self, cur):
        """
        Insert default devices from configuration.
        """

        for name, metadata in DEVICES.items():
            cur.execute(
                """
                INSERT OR IGNORE INTO devices (
                    name,
                    type,
                    room,
                    description,
                    status,
                    last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    metadata.get("type", "unknown"),
                    metadata.get("room", ""),
                    metadata.get("description", ""),
                    "registered",
                    now(),
                ),
            )

    def update_device_status(self, device: str, status: str):
        """
        Update device status and last seen timestamp.
        """

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO devices (
                    name,
                    type,
                    room,
                    description,
                    status,
                    last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name)
                DO UPDATE SET
                    status=excluded.status,
                                           last_seen=excluded.last_seen
                """,
                (
                    device,
                    "unknown",
                    "",
                    "",
                    status,
                    now(),
                ),
            )

            conn.commit()

    def add_telemetry(
            self,
            device: str,
            topic: str,
            values: Dict[str, Any],
            raw_message: str,
    ):
        """
        Add telemetry values to database.
        """

        timestamp = now()

        with self.connect() as conn:
            for key, value in values.items():
                if isinstance(value, bool):
                    numeric_value = 1.0 if value else 0.0
                elif isinstance(value, (int, float)):
                    numeric_value = float(value)
                else:
                    continue

                conn.execute(
                    """
                    INSERT INTO telemetry (
                        timestamp,
                        device,
                        topic,
                        metric_key,
                        metric_value,
                        raw_message
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        device,
                        topic,
                        key,
                        numeric_value,
                        raw_message,
                    ),
                )

            conn.commit()

        self.update_device_status(device, "online")

    def add_event(
            self,
            device: str,
            event_type: str,
            event_value: Any,
            description: str,
            raw_message: str = "",
    ):
        """
        Add event to database.
        """

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    timestamp,
                    device,
                    event_type,
                    event_value,
                    description,
                    raw_message
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    now(),
                    device,
                    event_type,
                    str(event_value),
                    description,
                    raw_message,
                ),
            )

            conn.commit()

        self.update_device_status(device, "event")

    def add_alarm(
            self,
            severity: str,
            device: str,
            alarm_type: str,
            message: str,
            raw_message: str = "",
    ):
        """
        Add alarm to database.
        """

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO alarms (
                    timestamp,
                    severity,
                    device,
                    alarm_type,
                    message,
                    active,
                    raw_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now(),
                    severity,
                    device,
                    alarm_type,
                    message,
                    1,
                    raw_message,
                ),
            )

            conn.commit()

    def add_relay_command(
            self,
            command: int,
            reason: str,
            source: str,
    ):
        """
        Add relay command history.
        """

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO relay_commands (
                    timestamp,
                    command,
                    reason,
                    source
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    now(),
                    int(command),
                    reason,
                    source,
                ),
            )

            conn.commit()

    def latest_value(self, metric_key: str) -> Optional[float]:
        """
        Return latest value for selected metric key.
        """

        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT metric_value
                FROM telemetry
                WHERE metric_key = ?
                ORDER BY id DESC
                    LIMIT 1
                """,
                (metric_key,),
            ).fetchone()

            if row is None:
                return None

            return row["metric_value"]

    def latest_values(self) -> Dict[str, float]:
        """
        Return latest value for every metric key.
        """

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT t1.metric_key, t1.metric_value
                FROM telemetry t1
                         JOIN (
                    SELECT metric_key, MAX(id) AS max_id
                    FROM telemetry
                    GROUP BY metric_key
                ) t2
                              ON t1.id = t2.max_id
                """
            ).fetchall()

            return {
                row["metric_key"]: row["metric_value"]
                for row in rows
            }

    def recent_alarms(self, limit: int = 20) -> List[sqlite3.Row]:
        """
        Return recent alarms.
        """

        with self.connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM alarms
                ORDER BY id DESC
                    LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def recent_events(self, limit: int = 20) -> List[sqlite3.Row]:
        """
        Return recent events.
        """

        with self.connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM events
                ORDER BY id DESC
                    LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def telemetry_series(
            self,
            metric_key: str,
            limit: int = 100,
    ) -> List[sqlite3.Row]:
        """
        Return telemetry series for charts.
        """

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, metric_value
                FROM telemetry
                WHERE metric_key = ?
                ORDER BY id DESC
                    LIMIT ?
                """,
                (
                    metric_key,
                    limit,
                ),
            ).fetchall()

            return rows[::-1]