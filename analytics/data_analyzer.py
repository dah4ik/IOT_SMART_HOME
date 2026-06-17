"""
Analytics module
"""

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


import matplotlib.pyplot as plt
import pandas as pd

from config import DB_PATH
from database import SmartHomeDB


def load_table(table_name: str) -> pd.DataFrame:

    """
    Load database table into pandas DataFrame.
    """

    db = SmartHomeDB(DB_PATH)

    with db.connect() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn,
        )


def print_summary():

    """
    Print database summary.
    """

    telemetry = load_table("telemetry")
    events = load_table("events")
    alarms = load_table("alarms")
    relay_commands = load_table("relay_commands")

    print("IOT_SMART_HOME database summary")
    print("--------------------------------")
    print("Telemetry rows:", len(telemetry))
    print("Events rows:", len(events))
    print("Alarms rows:", len(alarms))
    print("Relay commands rows:", len(relay_commands))

    if not telemetry.empty:
        print()
        print("Telemetry statistics:")
        print(
            telemetry.groupby("metric_key")["metric_value"].agg(
                [
                    "count",
                    "min",
                    "max",
                    "mean",
                ]
            )
        )


def plot_metric(
        metric_key: str,
        output_path: str,
):
    """
    Generate chart for selected telemetry metric.
    """

    telemetry = load_table("telemetry")

    data = telemetry[
        telemetry["metric_key"] == metric_key
        ].copy()

    if data.empty:
        print(f"No telemetry data found for metric: {metric_key}")
        return

    data["timestamp"] = pd.to_datetime(data["timestamp"])

    plt.figure(figsize=(10, 5))
    plt.plot(
        data["timestamp"],
        data["metric_value"],
        marker="o",
    )

    plt.title(f"IOT_SMART_HOME - {metric_key} trend")
    plt.xlabel("Time")
    plt.ylabel(metric_key)
    plt.xticks(rotation=30)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(output_path)

    print("Chart saved to:", output_path)


def main():
    """
    Analytics CLI entry point.
    """

    parser = argparse.ArgumentParser(
        description="IOT_SMART_HOME analytics module"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print database summary",
    )

    parser.add_argument(
        "--plot",
        choices=[
            "temperature",
            "humidity",
            "light",
            "electricity",
            "water",
            "door_open",
            "value",
        ],
        help="Telemetry metric to plot",
    )

    parser.add_argument(
        "--out",
        default="data/chart.png",
        help="Output chart path",
    )

    args = parser.parse_args()

    if args.summary:
        print_summary()

    if args.plot:
        plot_metric(
            metric_key=args.plot,
            output_path=args.out,
        )


if __name__ == "__main__":
    main()