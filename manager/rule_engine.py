"""
Rule Engine
"""

import json
from pathlib import Path
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT_DIR / "rules" / "rules.json"


class RuleEngine:
    """
    Configurable rule engine.
    """

    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules_path = Path(rules_path)
        self.rules = self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        """
        Load rules from JSON file.
        """

        with open(self.rules_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("rules", [])

    def compare(
            self,
            value: float,
            operator: str,
            threshold: float,
    ) -> bool:
        """
        Compare value with threshold according to operator.
        """

        if operator == ">":
            return value > threshold

        if operator == ">=":
            return value >= threshold

        if operator == "<":
            return value < threshold

        if operator == "<=":
            return value <= threshold

        if operator == "==":
            return value == threshold

        if operator == "!=":
            return value != threshold

        return False

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against incoming message data.
        """

        device = data.get("device", "")
        triggered_rules = []

        for rule in self.rules:
            if rule.get("source") != device:
                continue

            key = rule.get("key")

            if key not in data:
                continue

            value = data[key]

            if isinstance(value, bool):
                value = 1.0 if value else 0.0

            try:
                numeric_value = float(value)
                threshold = float(rule.get("threshold", 0))
            except Exception:
                continue

            operator = rule.get("operator", ">")

            if self.compare(numeric_value, operator, threshold):
                triggered_rule = dict(rule)
                triggered_rule["actual_value"] = numeric_value
                triggered_rules.append(triggered_rule)

        return triggered_rules