"""
GUI dashboard
"""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QGridLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
)

from config import TOPICS, BROKER_HOST, BROKER_PORT, PROJECT_NAME
from core.logging_setup import setup_logging, get_logger
from core.mqtt_agent import MqttAgent
from database import SmartHomeDB


setup_logging()

logger = get_logger("iot_smart_home.gui")


class Dashboard(QMainWindow):
    """
    Main GUI dashboard window.
    """

    def __init__(self):
        super().__init__()

        self.db = SmartHomeDB()
        self.agent = MqttAgent("gui")

        self.agent.connect()

        self.setWindowTitle(f"{PROJECT_NAME} - Smart Home Dashboard")
        self.resize(1150, 780)

        self.build_ui()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

        self.refresh()

    def build_ui(self):
        """
        Build main GUI layout.
        """

        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)

        connection_label = QLabel(
            f"Broker: {BROKER_HOST}:{BROKER_PORT} | "
            f"Base topic: {TOPICS['all']}"
        )

        connection_label.setStyleSheet(
            "font-size: 14px; "
            "padding: 8px; "
            "background-color: #e8f5e9; "
            "border: 1px solid #a5d6a7;"
        )

        root_layout.addWidget(connection_label)

        cards_box = QGroupBox("Live Smart Home Status")
        cards_grid = QGridLayout(cards_box)

        self.temperature_label = self.create_value_label()
        self.humidity_label = self.create_value_label()
        self.light_label = self.create_value_label()
        self.electricity_label = self.create_value_label()
        self.water_label = self.create_value_label()
        self.door_label = self.create_value_label()
        self.relay_label = self.create_value_label()

        status_cards = [
            ("Temperature", self.temperature_label),
            ("Humidity", self.humidity_label),
            ("Light", self.light_label),
            ("Electricity", self.electricity_label),
            ("Water", self.water_label),
            ("Door", self.door_label),
            ("Relay", self.relay_label),
        ]

        for index, item in enumerate(status_cards):
            title, widget = item

            group = QGroupBox(title)
            layout = QVBoxLayout(group)
            layout.addWidget(widget)

            row = index // 4
            col = index % 4

            cards_grid.addWidget(group, row, col)

        root_layout.addWidget(cards_box)

        relay_controls = QGroupBox("Relay Control")
        relay_layout = QHBoxLayout(relay_controls)

        self.relay_on_button = QPushButton("Relay ON")
        self.relay_off_button = QPushButton("Relay OFF")
        self.refresh_button = QPushButton("Refresh")

        self.relay_on_button.clicked.connect(
            lambda: self.send_relay_command(1, "manual_gui_on")
        )

        self.relay_off_button.clicked.connect(
            lambda: self.send_relay_command(0, "manual_gui_off")
        )

        self.refresh_button.clicked.connect(self.refresh)

        relay_layout.addWidget(self.relay_on_button)
        relay_layout.addWidget(self.relay_off_button)
        relay_layout.addWidget(self.refresh_button)

        root_layout.addWidget(relay_controls)

        self.events_table = QTableWidget(0, 4)
        self.events_table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "Device",
                "Event Type",
                "Description",
            ]
        )

        self.events_table.horizontalHeader().setStretchLastSection(True)

        events_box = QGroupBox("Recent Events")
        events_layout = QVBoxLayout(events_box)
        events_layout.addWidget(self.events_table)

        root_layout.addWidget(events_box)

        alarms_box = QGroupBox("Recent Alarms")
        alarms_layout = QVBoxLayout(alarms_box)

        self.alarms_text = QTextEdit()
        self.alarms_text.setReadOnly(True)
        self.alarms_text.setStyleSheet(
            "background-color: #fff3e0; "
            "font-family: Consolas; "
            "font-size: 12px;"
        )

        alarms_layout.addWidget(self.alarms_text)

        root_layout.addWidget(alarms_box)

        self.setCentralWidget(root_widget)

    def create_value_label(self) -> QLabel:
        """
        Create styled value label.
        """

        label = QLabel("NA")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold; "
            "padding: 10px; "
            "border: 1px solid #bdbdbd; "
            "background-color: #ffffff;"
        )

        return label

    def set_card(
            self,
            label: QLabel,
            text: str,
            background: str = "#ffffff",
    ):
        """
        Update card label text and background color.
        """

        label.setText(text)
        label.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold; "
            "padding: 10px; "
            "border: 1px solid #bdbdbd; "
            f"background-color: {background};"
        )

    def send_relay_command(
            self,
            value: int,
            reason: str,
    ):
        """
        Publish manual relay command.
        """

        payload = {
            "device": "GUI",
            "type": "command",
            "value": value,
            "reason": reason,
        }

        self.agent.publish(
            topic=TOPICS["relay_cmd"],
            payload=payload,
            qos=1,
            retain=False,
        )

        logger.info(
            "Manual relay command sent: value=%s reason=%s",
            value,
            reason,
        )

    def refresh(self):
        """
        Refresh dashboard values from database.
        """

        values = self.db.latest_values()

        temperature = values.get("temperature")
        humidity = values.get("humidity")
        light = values.get("light")
        electricity = values.get("electricity")
        water = values.get("water")
        door_open = values.get("door_open")

        # Relay can appear as "relay" or as latest generic "value".
        relay = values.get("relay")

        if relay is None:
            relay = values.get("value")

        if temperature is None:
            self.set_card(self.temperature_label, "NA")
        else:
            color = "#ffcdd2" if temperature >= 30 else "#ffffff"
            self.set_card(
                self.temperature_label,
                f"{temperature:.1f} C",
                color,
            )

        if humidity is None:
            self.set_card(self.humidity_label, "NA")
        else:
            color = "#fff9c4" if humidity >= 80 else "#ffffff"
            self.set_card(
                self.humidity_label,
                f"{humidity:.1f} %",
                color,
            )

        if light is None:
            self.set_card(self.light_label, "NA")
        else:
            color = "#fff9c4" if light < 100 else "#ffffff"
            self.set_card(
                self.light_label,
                f"{light:.0f} lux",
                color,
            )

        if electricity is None:
            self.set_card(self.electricity_label, "NA")
        else:
            self.set_card(
                self.electricity_label,
                f"{electricity:.2f} kWh",
            )

        if water is None:
            self.set_card(self.water_label, "NA")
        else:
            self.set_card(
                self.water_label,
                f"{water:.3f} m3",
            )

        if door_open is None:
            self.set_card(self.door_label, "NA")
        else:
            if door_open:
                self.set_card(self.door_label, "OPEN", "#ffcdd2")
            else:
                self.set_card(self.door_label, "Closed", "#c8e6c9")

        if relay is None:
            self.set_card(self.relay_label, "NA")
        else:
            if relay:
                self.set_card(self.relay_label, "ON", "#a5d6a7")
            else:
                self.set_card(self.relay_label, "OFF", "#eeeeee")

        self.refresh_events()
        self.refresh_alarms()

    def refresh_events(self):
        """
        Refresh recent events table.
        """

        events = self.db.recent_events(limit=15)

        self.events_table.setRowCount(len(events))

        for row_index, event in enumerate(events):
            row_values = [
                event["timestamp"],
                event["device"],
                event["event_type"],
                event["description"],
            ]

            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                self.events_table.setItem(
                    row_index,
                    col_index,
                    item,
                )

    def refresh_alarms(self):
        """
        Refresh recent alarms view.
        """

        alarms = self.db.recent_alarms(limit=20)

        self.alarms_text.clear()

        for alarm in alarms:
            line = (
                f"[{alarm['severity']}] "
                f"{alarm['timestamp']} | "
                f"{alarm['device']} | "
                f"{alarm['message']}"
            )

            self.alarms_text.append(line)

    def closeEvent(self, event):
        """
        Disconnect MQTT client when GUI is closed.
        """

        self.agent.disconnect()
        event.accept()


def main():

    app = QApplication(sys.argv)

    dashboard = Dashboard()
    dashboard.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()