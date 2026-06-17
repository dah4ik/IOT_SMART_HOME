"""
Virtual IoT device emulators
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from config import TOPICS
from core.logging_setup import setup_logging, get_logger
from core.mqtt_agent import MqttAgent


setup_logging()

logger = get_logger("iot_smart_home.emulators")


def publish_loop(
        agent: MqttAgent,
        topic: str,
        device: str,
        payload_factory,
        interval: float,
):

    agent.connect()

    try:
        while True:
            payload = payload_factory()
            payload["device"] = device
            payload["timestamp"] = int(time.time())

            agent.publish(
                topic=topic,
                payload=payload,
                qos=1,
                retain=False,
            )

            print(
                f"{device} -> {topic}: "
                f"{json.dumps(payload, indent=2)}"
            )

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"Stopping {device} emulator...")

    finally:
        agent.disconnect()


def run_dht(interval: float):
    """
    Run DHT temperature and humidity sensor emulator.
    """

    def factory():
        return {
            "type": "telemetry",
            "temperature": round(random.uniform(22.0, 38.0), 1),
            "humidity": round(random.uniform(45.0, 88.0), 1),
        }

    publish_loop(
        agent=MqttAgent("dht"),
        topic=TOPICS["dht"],
        device="DHT_SENSOR",
        payload_factory=factory,
        interval=interval,
    )


def run_light(interval: float):
    """
    Run light sensor emulator.
    """

    def factory():
        return {
            "type": "telemetry",
            "light": random.randint(20, 900),
        }

    publish_loop(
        agent=MqttAgent("light"),
        topic=TOPICS["light"],
        device="LIGHT_SENSOR",
        payload_factory=factory,
        interval=interval,
    )


def run_meter(interval: float):
    """
    Run electricity and water meter emulator.
    """

    def factory():
        return {
            "type": "telemetry",
            "electricity": round(random.uniform(0.2, 3.5), 2),
            "water": round(random.uniform(0.005, 0.08), 3),
        }

    publish_loop(
        agent=MqttAgent("meter"),
        topic=TOPICS["meter"],
        device="METER_SENSOR",
        payload_factory=factory,
        interval=interval,
    )


def run_reed(interval: float):
    """
    Run reed door sensor emulator.
    """

    door_state = {
        "open": False,
    }

    def factory():
        if random.random() > 0.65:
            door_state["open"] = not door_state["open"]

        return {
            "type": "telemetry",
            "door_open": door_state["open"],
        }

    publish_loop(
        agent=MqttAgent("reed"),
        topic=TOPICS["reed"],
        device="REED_SENSOR",
        payload_factory=factory,
        interval=interval,
    )


def run_button():
    """
    Run button event emulator.
    """

    agent = MqttAgent("button")
    agent.connect()

    print("BUTTON emulator started.")
    print("Press ENTER to publish button event.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            input()

            payload = {
                "device": "BUTTON_SENSOR",
                "type": "event",
                "value": 1,
                "timestamp": int(time.time()),
            }

            agent.publish(
                topic=TOPICS["button"],
                payload=payload,
                qos=1,
                retain=False,
            )

            print(
                f"BUTTON_SENSOR -> {TOPICS['button']}: "
                f"{json.dumps(payload)}"
            )

    except KeyboardInterrupt:
        print("Stopping BUTTON emulator...")

    finally:
        agent.disconnect()


def run_relay():
    """
    Run relay actuator emulator.
    """

    state = {
        "value": 0,
    }

    agent_holder = {
        "agent": None,
    }

    def on_message(topic: str, payload: str):
        try:
            data = json.loads(payload)
            value = int(data.get("value", state["value"]))

        except Exception:
            lower_payload = payload.lower()

            if "on" in lower_payload or "1" in lower_payload:
                value = 1
            else:
                value = 0

        state["value"] = 1 if value else 0

        status_payload = {
            "device": "RELAY_ACTUATOR",
            "type": "status",
            "value": state["value"],
            "state": "ON" if state["value"] else "OFF",
            "timestamp": int(time.time()),
        }

        print(
            "Relay command received:",
            payload,
            "new state:",
            status_payload["state"],
        )

        agent_holder["agent"].publish(
            topic=TOPICS["relay_status"],
            payload=status_payload,
            qos=1,
            retain=True,
        )

    agent = MqttAgent(
        name="relay",
        on_message=on_message,
    )

    agent_holder["agent"] = agent

    agent.connect()
    agent.subscribe(
        topic=TOPICS["relay_cmd"],
        qos=1,
    )

    initial_status = {
        "device": "RELAY_ACTUATOR",
        "type": "status",
        "value": 0,
        "state": "OFF",
        "timestamp": int(time.time()),
    }

    agent.publish(
        topic=TOPICS["relay_status"],
        payload=initial_status,
        qos=1,
        retain=True,
    )

    print("RELAY emulator started.")
    print("Listening on:", TOPICS["relay_cmd"])
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping RELAY emulator...")

    finally:
        agent.disconnect()


def main():
    """
    CLI entry point for device emulators.
    """

    parser = argparse.ArgumentParser(
        description="IOT_SMART_HOME device emulators"
    )

    parser.add_argument(
        "--device",
        required=True,
        choices=[
            "dht",
            "light",
            "meter",
            "reed",
            "button",
            "relay",
        ],
        help="Device emulator to run",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Publish interval in seconds for sensor devices",
    )

    args = parser.parse_args()

    if args.device == "dht":
        run_dht(args.interval)

    elif args.device == "light":
        run_light(args.interval)

    elif args.device == "meter":
        run_meter(args.interval)

    elif args.device == "reed":
        run_reed(args.interval)

    elif args.device == "button":
        run_button()

    elif args.device == "relay":
        run_relay()


if __name__ == "__main__":
    main()