"""
Assistant BOT
"""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from config import TOPICS
from core.logging_setup import setup_logging
from core.mqtt_agent import MqttAgent
from database import SmartHomeDB


setup_logging()


def print_home_status(db: SmartHomeDB):

    """
    Print latest smart home values.
    """

    values = db.latest_values()

    if not values:
        print("No telemetry data available yet.")
        return

    print()
    print("Current home status:")
    print("--------------------")

    for key, value in values.items():
        print(f"{key}: {value}")

    print()


def print_room_temperature(db: SmartHomeDB):

    """
    Print latest room temperature.
    """

    temperature = db.latest_value("temperature")

    if temperature is None:
        print("Room temperature is currently unavailable.")
    else:
        print(f"Room temperature is {temperature:.1f} C")


def print_alarms(db: SmartHomeDB):

    """
    Print recent alarms.
    """

    alarms = db.recent_alarms(limit=10)

    if not alarms:
        print("No alarms found.")
        return

    print()
    print("Recent alarms:")
    print("--------------")

    for alarm in alarms:
        print(
            f"[{alarm['severity']}] "
            f"{alarm['timestamp']} | "
            f"{alarm['device']} | "
            f"{alarm['message']}"
        )

    print()


def send_relay_command(
        mqtt_agent: MqttAgent,
        value: int,
):

    """
    Send relay command.
    """

    payload = {
        "device": "ASSISTANT_BOT",
        "type": "command",
        "value": value,
        "reason": "assistant_command",
    }

    mqtt_agent.publish(
        topic=TOPICS["relay_cmd"],
        payload=payload,
        qos=1,
        retain=False,
    )

    if value:
        print("Relay ON command sent.")
    else:
        print("Relay OFF command sent.")


def main():
    """
    Assistant BOT entry point.
    """

    db = SmartHomeDB()
    mqtt_agent = MqttAgent("assistant_bot")
    mqtt_agent.connect()

    print("IOT_SMART_HOME Assistant BOT")
    print("----------------------------")
    print("Available commands:")
    print("home status")
    print("room temperature")
    print("alarms")
    print("relay on")
    print("relay off")
    print("exit")
    print()

    try:
        while True:
            command = input("assistant> ").strip().lower()

            if command in ["exit", "quit", "stop"]:
                break

            elif command == "home status":
                print_home_status(db)

            elif command == "room temperature":
                print_room_temperature(db)

            elif command == "alarms":
                print_alarms(db)

            elif command == "relay on":
                send_relay_command(
                    mqtt_agent=mqtt_agent,
                    value=1,
                )

            elif command == "relay off":
                send_relay_command(
                    mqtt_agent=mqtt_agent,
                    value=0,
                )

            else:
                print("Unknown command.")

    finally:
        mqtt_agent.disconnect()
        print("Assistant BOT stopped.")


if __name__ == "__main__":
    main()