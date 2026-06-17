"""
MQTT message schema helpers
"""

import json
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ParsedMessage:
    """
    Parsed MQTT message result.
    """

    ok: bool
    data: Dict[str, Any]
    error: str = ""


def parse_payload(payload: str) -> ParsedMessage:
    """
    Parse MQTT payload as JSON.
    """

    try:
        data = json.loads(payload)

        if not isinstance(data, dict):
            return ParsedMessage(
                ok=False,
                data={},
                error="Payload is not a JSON object",
            )

        if "device" not in data:
            return ParsedMessage(
                ok=False,
                data=data,
                error="Missing required field: device",
            )

        return ParsedMessage(
            ok=True,
            data=data,
            error="",
        )

    except Exception as error:
        return ParsedMessage(
            ok=False,
            data={"raw": payload},
            error=f"Invalid JSON payload: {error}",
        )


def numeric_fields(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract numeric telemetry fields from message.
    """

    ignored_keys = {
        "device",
        "type",
        "state",
        "reason",
        "source",
        "timestamp",
        "ts",
    }

    values = {}

    for key, value in data.items():
        if key in ignored_keys:
            continue

        if isinstance(value, bool):
            values[key] = 1.0 if value else 0.0

        elif isinstance(value, (int, float)):
            values[key] = float(value)

    return values