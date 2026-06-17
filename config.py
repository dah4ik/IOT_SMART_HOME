from pathlib import Path

# Project details


PROJECT_NAME = "IOT_SMART_HOME"



# MQTT Broker configuration


BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
KEEP_ALIVE = 90

USERNAME = ""
PASSWORD = ""

CLEAN_SESSION = True



# MQTT Topics


BASE_TOPIC = "iot_smart_home"

TOPICS = {
    "all": f"{BASE_TOPIC}/#",

    "dht": f"{BASE_TOPIC}/dht/telemetry",
    "light": f"{BASE_TOPIC}/light/telemetry",
    "meter": f"{BASE_TOPIC}/meter/telemetry",
    "reed": f"{BASE_TOPIC}/reed/telemetry",

    "button": f"{BASE_TOPIC}/button/event",

    "relay_cmd": f"{BASE_TOPIC}/relay/cmd",
    "relay_status": f"{BASE_TOPIC}/relay/status",

    "alarms": f"{BASE_TOPIC}/alarms",
    "manager_status": f"{BASE_TOPIC}/manager/status",
}



# Project folders


ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = str(DATA_DIR / "iot_smart_home.db")
LOG_PATH = str(DATA_DIR / "iot_smart_home.log")



# Alarm thresholds


THRESHOLDS = {
    "temperature_high": 30.0,
    "temperature_critical": 35.0,
    "humidity_high": 80.0,
    "light_low": 100.0,
    "electricity_high": 2.0,
    "water_high": 0.04,
}



# Devices registry


DEVICES = {
    "DHT_SENSOR": {
        "type": "sensor",
        "room": "Living Room",
        "description": "Temperature and humidity sensor",
    },

    "LIGHT_SENSOR": {
        "type": "sensor",
        "room": "Living Room",
        "description": "Light intensity sensor",
    },

    "METER_SENSOR": {
        "type": "meter",
        "room": "Utility Room",
        "description": "Electricity and water meter",
    },

    "REED_SENSOR": {
        "type": "sensor",
        "room": "Main Door",
        "description": "Door open or close sensor",
    },

    "BUTTON_SENSOR": {
        "type": "event",
        "room": "Entrance",
        "description": "Manual push button",
    },

    "RELAY_ACTUATOR": {
        "type": "actuator",
        "room": "Living Room",
        "description": "Relay actuator for light or alarm control",
    },
}