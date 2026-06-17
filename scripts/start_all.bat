@echo off

echo Starting IOT_SMART_HOME full system...

start cmd /k python manager\data_manager.py
start cmd /k python devices\emulators.py --device relay
start cmd /k python devices\emulators.py --device dht --interval 5
start cmd /k python devices\emulators.py --device light --interval 5
start cmd /k python devices\emulators.py --device meter --interval 7
start cmd /k python devices\emulators.py --device reed --interval 10
start cmd /k python devices\emulators.py --device button
start cmd /k python gui\main_gui.py
start cmd /k uvicorn api.web_api:app --host 127.0.0.1 --port 8000

echo All components started.