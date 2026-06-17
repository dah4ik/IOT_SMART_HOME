@echo off

uvicorn api.web_api:app --reload --host 127.0.0.1 --port 8000

pause