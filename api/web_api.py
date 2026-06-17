"""
REST API and Web Dashboard
"""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from config import PROJECT_NAME, TOPICS
from core.mqtt_agent import MqttAgent
from database import SmartHomeDB


app = FastAPI(
    title=f"{PROJECT_NAME} API",
    description="REST API for Smart Home IoT system",
    version="1.0.0",
)

db = SmartHomeDB()
mqtt_agent = MqttAgent("web_api")
mqtt_agent.connect()


@app.get("/api/status")
def status():
    """
    Return current system status.
    """

    return {
        "project": PROJECT_NAME,
        "base_topic": TOPICS["all"],
        "latest_values": db.latest_values(),
    }


@app.get("/api/alarms")
def alarms(limit: int = 20):
    """
    Return recent alarms.
    """

    return [
        dict(row)
        for row in db.recent_alarms(limit=limit)
    ]


@app.get("/api/events")
def events(limit: int = 20):
    """
    Return recent events.
    """

    return [
        dict(row)
        for row in db.recent_events(limit=limit)
    ]


@app.get("/api/telemetry/{metric_key}")
def telemetry(metric_key: str, limit: int = 100):
    """
    Return telemetry series for selected metric key.
    """

    return [
        dict(row)
        for row in db.telemetry_series(
            metric_key=metric_key,
            limit=limit,
        )
    ]


@app.post("/api/relay/{value}")
def relay(value: int):
    """
    Send relay command.

    value:
    - 1 means ON
    - 0 means OFF
    """

    relay_value = 1 if value else 0

    payload = {
        "device": "WEB_API",
        "type": "command",
        "value": relay_value,
        "reason": "api_request",
    }

    mqtt_agent.publish(
        topic=TOPICS["relay_cmd"],
        payload=payload,
        qos=1,
        retain=False,
    )

    return {
        "relay_command_sent": relay_value,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """
    Simple browser dashboard.
    """

    return """
<!doctype html>
<html>
<head>
    <title>IOT_SMART_HOME Dashboard</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 30px;
            background: #f6f8fa;
        }

        h1 {
            color: #1565c0;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 2px 8px #ddd;
        }

        .card-title {
            font-size: 15px;
            color: #666;
        }

        .value {
            font-size: 28px;
            font-weight: bold;
            color: #1565c0;
            margin-top: 10px;
        }

        button {
            padding: 10px 18px;
            margin: 5px;
            font-size: 16px;
            cursor: pointer;
        }

        pre {
            background: #222;
            color: #eee;
            padding: 12px;
            border-radius: 6px;
            max-height: 260px;
            overflow: auto;
        }
    </style>
</head>

<body>
    <h1>IOT_SMART_HOME - Web Dashboard</h1>

    <button onclick="relay(1)">Relay ON</button>
    <button onclick="relay(0)">Relay OFF</button>

    <div class="cards" id="cards"></div>

    <h2>Recent Alarms</h2>
    <pre id="alarms"></pre>

    <h2>Recent Events</h2>
    <pre id="events"></pre>

<script>
async function loadDashboard() {
    const statusResponse = await fetch('/api/status');
    const status = await statusResponse.json();

    const latest = status.latest_values || {};

    const keys = [
        'temperature',
        'humidity',
        'light',
        'electricity',
        'water',
        'door_open',
        'value'
    ];

    document.getElementById('cards').innerHTML = keys.map(key => {
        const value = latest[key] ?? 'NA';

        return `
            <div class="card">
                <div class="card-title">${key}</div>
                <div class="value">${value}</div>
            </div>
        `;
    }).join('');

    const alarmsResponse = await fetch('/api/alarms');
    const alarms = await alarmsResponse.json();

    document.getElementById('alarms').innerText =
        JSON.stringify(alarms, null, 2);

    const eventsResponse = await fetch('/api/events');
    const events = await eventsResponse.json();

    document.getElementById('events').innerText =
        JSON.stringify(events, null, 2);
}

async function relay(value) {
    await fetch('/api/relay/' + value, {
        method: 'POST'
    });

    loadDashboard();
}

setInterval(loadDashboard, 2000);
loadDashboard();
</script>

</body>
</html>
"""