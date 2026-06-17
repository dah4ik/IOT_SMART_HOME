# IOT_SMART_HOME — Setup and Run Guide

This README contains only the required steps to install, configure and run the project.

---

## 1. Requirements

Before running the project, install:

- Python 3.10 or newer
- Git
- Internet connection for MQTT broker access

The project uses the public HiveMQ MQTT broker:

```text
broker.hivemq.com:1883
```

---

## 2. Open the Project

Open the project folder:

```text
IOT_SMART_HOME
```

In PyCharm, open the folder as an existing project.

---

## 3. Create Virtual Environment

From the project root folder, run:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 4. Install Dependencies

Run:

```bash
pip install -r requirements.txt
```

If PyQt5 installation fails, install it separately:

```bash
pip install PyQt5
```

---

## 5. Configuration

All project configuration is located in:

```text
config.py
```

Default MQTT configuration:

```python
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
KEEP_ALIVE = 90
BASE_TOPIC = "iot_smart_home"
```

No username or password is required for the default public broker.

Database and logs are created automatically in:

```text
data/
```

Database file:

```text
data/iot_smart_home.db
```

Log file:

```text
data/iot_smart_home.log
```

---

## 6. Run Order

The correct run order is:

```text
1. Data Manager
2. Relay Emulator
3. Sensor Emulators
4. GUI Dashboard
5. Web API / Web Dashboard
```

---

## 7. Start the Project Manually

Open a separate terminal for each command.

### Terminal 1 — Start Data Manager

```bash
python manager/data_manager.py
```

Keep this terminal open.

---

### Terminal 2 — Start Relay Emulator

```bash
python devices/emulators.py --device relay
```

Keep this terminal open.

---

### Terminal 3 — Start DHT Sensor

```bash
python devices/emulators.py --device dht --interval 5
```

---

### Terminal 4 — Start Light Sensor

```bash
python devices/emulators.py --device light --interval 5
```

---

### Terminal 5 — Start Meter Sensor

```bash
python devices/emulators.py --device meter --interval 7
```

---

### Terminal 6 — Start Reed Sensor

```bash
python devices/emulators.py --device reed --interval 10
```

---

### Terminal 7 — Start Button Emulator

```bash
python devices/emulators.py --device button
```

Press `ENTER` in this terminal to send a button event.

---

### Terminal 8 — Start GUI Dashboard

```bash
python gui/main_gui.py
```

---

### Terminal 9 — Start Web API and Web Dashboard

```bash
uvicorn api.web_api:app --reload --host 127.0.0.1 --port 8000
```

Open in browser:

```text
http://127.0.0.1:8000
```

---

## 8. Start the Project with Scripts

On Windows, you can start everything with:

```bash
scripts/start_all.bat
```

Or start only selected components:

```bash
scripts/start_manager.bat
scripts/start_gui.bat
scripts/start_web_api.bat
```

---

## 9. Run Analytics

Print database summary:

```bash
python analytics/data_analyzer.py --summary
```

Generate a chart:

```bash
python analytics/data_analyzer.py --plot temperature --out data/temperature.png
```

---

## 10. Run Assistant BOT

```bash
python assistant/assistant_bot.py
```

Available commands inside the assistant:

```text
home status
room temperature
alarms
relay on
relay off
exit
```

---

## 11. Run Tests

```bash
pytest tests
```

---

## 12. Stop the Project

To stop each component, press:

```text
Ctrl + C
```

in every running terminal.

If GUI is open, close the GUI window normally.

---

## 13. Troubleshooting

### MQTT messages do not arrive

Check that all components use the same broker and base topic in `config.py`:

```python
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
BASE_TOPIC = "iot_smart_home"
```

Also make sure you have an active internet connection.

---

### GUI shows no data

Make sure these components are running first:

```bash
python manager/data_manager.py
python devices/emulators.py --device dht --interval 5
python devices/emulators.py --device relay
```

---

### Web dashboard does not open

Make sure the API server is running:

```bash
uvicorn api.web_api:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

---

### Relay does not respond

Make sure Relay Emulator is running:

```bash
python devices/emulators.py --device relay
```

Then send a command from GUI, Web API, Assistant BOT, or Button Emulator.

---

### Database was not created

Run Data Manager once:

```bash
python manager/data_manager.py
```

The database will be created automatically:

```text
data/iot_smart_home.db
```

---

## 14. Quick Full Run Checklist

```text
[ ] pip install -r requirements.txt
[ ] python manager/data_manager.py
[ ] python devices/emulators.py --device relay
[ ] python devices/emulators.py --device dht --interval 5
[ ] python devices/emulators.py --device light --interval 5
[ ] python devices/emulators.py --device meter --interval 7
[ ] python devices/emulators.py --device reed --interval 10
[ ] python devices/emulators.py --device button
[ ] python gui/main_gui.py
[ ] uvicorn api.web_api:app --reload --host 127.0.0.1 --port 8000
[ ] open http://127.0.0.1:8000
```
