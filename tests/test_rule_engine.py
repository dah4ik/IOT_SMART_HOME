"""
Tests for Rule Engine.
"""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from manager.rule_engine import RuleEngine


def test_high_temperature_rule():
    """
    Test high temperature rule.
    """

    engine = RuleEngine()

    result = engine.evaluate(
        {
            "device": "DHT_SENSOR",
            "temperature": 31,
        }
    )

    assert any(
        rule["id"] == "high_temperature_warning"
        for rule in result
    )


def test_button_toggle_rule():
    """
    Test button toggle relay rule.
    """

    engine = RuleEngine()

    result = engine.evaluate(
        {
            "device": "BUTTON_SENSOR",
            "value": 1,
        }
    )

    assert any(
        rule["id"] == "button_toggle_relay"
        for rule in result
    )