"""
Data Manager for IOT_SMART_HOME.
"""

import json
import sys
import threading
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from config import TOPICS, THRESHOLDS
from core.logging_setup import setup_logging, get_logger
from core.message_schema import parse_payload, numeric_fields
from core.mqtt_agent import MqttAgent
from database import SmartHomeDB
from manager.rule_engine import RuleEngine
from services.notifier import Notifier


setup_logging()

logger = get_logger("iot_smart_home.manager")


class DataManager:
    """
    Central Data Manager
    """

    def __init__(self):
        self.db = SmartHomeDB()
        self.rule_engine = RuleEngine()
        self.notifier = Notifier()

        self.relay_state = 0
        self.last_seen = {}

        self.agent = MqttAgent(
            name="data_manager",
            on_message=self.on_message,
        )

    def start(self):
        """
        Start MQTT manager.
        """

        logger.info("Starting Data Manager")

        self.agent.connect()
        self.agent.subscribe(
            topic=TOPICS["all"],
            qos=1,
        )

        self.agent.publish(
            topic=TOPICS["manager_status"],
            payload={
                "device": "DATA_MANAGER",
                "type": "status",
                "status": "online",
                "timestamp": int(time.time()),
            },
            qos=1,
            retain=True,
        )

        health_thread = threading.Thread(
            target=self.device_health_monitor,
            daemon=True,
        )

        health_thread.start()

        print("Data Manager is running.")
        print("Subscribed to:", TOPICS["all"])
        print("Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("Stopping Data Manager...")

        finally:
            self.stop()

    def stop(self):
        """
        Stop MQTT manager.
        """

        self.agent.publish(
            topic=TOPICS["manager_status"],
            payload={
                "device": "DATA_MANAGER",
                "type": "status",
                "status": "offline",
                "timestamp": int(time.time()),
            },
            qos=1,
            retain=True,
        )

        self.agent.disconnect()

    def on_message(self, topic: str, payload: str):
        """
        Handle incoming MQTT message.
        """

        logger.info(
            "Incoming MQTT message: topic=%s payload=%s",
            topic,
            payload,
        )

        parsed = parse_payload(payload)

        if not parsed.ok:
            logger.warning(
                "Invalid MQTT payload: topic=%s error=%s payload=%s",
                topic,
                parsed.error,
                payload,
            )

            self.db.add_event(
                device="UNKNOWN",
                event_type="invalid_message",
                event_value=parsed.error,
                description="Invalid MQTT payload received",
                raw_message=payload,
            )

            return

        data = parsed.data
        device = data.get("device", "UNKNOWN")

        self.last_seen[device] = time.time()
        self.db.update_device_status(device, "online")

        values = numeric_fields(data)

        if values:
            self.db.add_telemetry(
                device=device,
                topic=topic,
                values=values,
                raw_message=payload,
            )

        if data.get("type") == "event":
            self.db.add_event(
                device=device,
                event_type="device_event",
                event_value=data.get("value", ""),
                description="Device event received",
                raw_message=payload,
            )

        if topic == TOPICS["relay_status"]:
            self.db.add_event(
                device=device,
                event_type="relay_status",
                event_value=data.get("value", ""),
                description=f"Relay status updated: {data.get('state', '')}",
                raw_message=payload,
            )

        triggered_rules = self.rule_engine.evaluate(data)

        for rule in triggered_rules:
            self.handle_rule(
                rule=rule,
                data=data,
                raw_message=payload,
            )

    def handle_rule(
            self,
            rule: dict,
            data: dict,
            raw_message: str,
    ):
        """
        Handle triggered rule.
        """

        device = data.get("device", "UNKNOWN")

        rule_id = rule.get("id", "unknown_rule")
        severity = rule.get("severity", "INFO")
        alarm_type = rule.get("alarm_type", "rule")
        message = rule.get("message", "Rule triggered")
        actual_value = rule.get("actual_value", "")

        full_message = (
            f"{message}. "
            f"Actual value: {actual_value}. "
            f"Rule ID: {rule_id}"
        )

        actions = rule.get("actions", [])

        if "create_alarm" in actions:
            self.create_alarm(
                severity=severity,
                device=device,
                alarm_type=alarm_type,
                message=full_message,
                raw_message=raw_message,
            )

        if "create_event" in actions:
            self.db.add_event(
                device=device,
                event_type=alarm_type,
                event_value=actual_value,
                description=full_message,
                raw_message=raw_message,
            )

        if "relay_on" in actions:
            self.command_relay(
                value=1,
                reason=rule_id,
                source=device,
            )

        if "relay_off" in actions:
            self.command_relay(
                value=0,
                reason=rule_id,
                source=device,
            )

        if "relay_toggle" in actions:
            self.toggle_relay(
                reason=rule_id,
                source=device,
            )

    def create_alarm(
            self,
            severity: str,
            device: str,
            alarm_type: str,
            message: str,
            raw_message: str,
    ):
        """
        Create alarm and publish it to MQTT alarm topic.
        """

        alarm_payload = {
            "device": device,
            "type": "alarm",
            "severity": severity,
            "alarm_type": alarm_type,
            "message": message,
            "timestamp": int(time.time()),
        }

        self.db.add_alarm(
            severity=severity,
            device=device,
            alarm_type=alarm_type,
            message=message,
            raw_message=raw_message,
        )

        self.agent.publish(
            topic=TOPICS["alarms"],
            payload=alarm_payload,
            qos=1,
            retain=False,
        )

        self.notifier.notify(
            severity=severity,
            subject=f"{device} - {alarm_type}",
            message=message,
        )

    def command_relay(
            self,
            value: int,
            reason: str,
            source: str,
    ):
        """
        Send command to relay actuator.
        """

        self.relay_state = 1 if value else 0

        command_payload = {
            "device": "RELAY_ACTUATOR",
            "type": "command",
            "value": self.relay_state,
            "reason": reason,
            "source": source,
            "timestamp": int(time.time()),
        }

        self.db.add_relay_command(
            command=self.relay_state,
            reason=reason,
            source=source,
        )

        self.db.add_event(
            device="RELAY_ACTUATOR",
            event_type="relay_command",
            event_value=self.relay_state,
            description=f"Relay command sent. Reason: {reason}",
            raw_message=json.dumps(command_payload),
        )

        self.agent.publish(
            topic=TOPICS["relay_cmd"],
            payload=command_payload,
            qos=1,
            retain=False,
        )

    def toggle_relay(
            self,
            reason: str,
            source: str,
    ):
        """
        Toggle relay state.
        """

        new_state = 0 if self.relay_state else 1

        self.command_relay(
            value=new_state,
            reason=reason,
            source=source,
        )

    def device_health_monitor(self):
        """
        Monitor device last seen timestamps.
        """

        timeout = THRESHOLDS.get("device_offline_seconds", 45)

        while True:
            current_time = time.time()

            for device, last_seen_time in list(self.last_seen.items()):
                if current_time - last_seen_time > timeout:
                    message = (
                        f"Device {device} is offline for more than "
                        f"{timeout} seconds"
                    )

                    self.create_alarm(
                        severity="WARNING",
                        device=device,
                        alarm_type="device_offline",
                        message=message,
                        raw_message="",
                    )

                    # Prevent repeated alarm every loop.
                    self.last_seen[device] = current_time + 10**9

            time.sleep(10)


def main():
    """
    Data Manager entry point.
    """

    manager = DataManager()
    manager.start()


if __name__ == "__main__":
    main()