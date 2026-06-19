"""
Reusable MQTT client wrapper.
"""

import json
import threading
import uuid
from typing import Callable, Optional, Union

import paho.mqtt.client as mqtt

from config import (
    BROKER_HOST,
    BROKER_PORT,
    KEEP_ALIVE,
    USERNAME,
    PASSWORD,
    CLEAN_SESSION,
)
from core.logging_setup import get_logger


logger = get_logger("iot_smart_home.mqtt")


class MqttAgent:
    """
    Reusable MQTT client for project components.
    """

    def __init__(
        self,
        name: str,
        on_message: Optional[Callable[[str, str], None]] = None,
    ):
        unique_suffix = uuid.uuid4().hex[:8]
        self.client_id = f"iot_smart_home_{name}_{unique_suffix}"

        self.message_handler = on_message
        self.connected_event = threading.Event()

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=self.client_id,
            clean_session=CLEAN_SESSION,
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if USERNAME:
            self.client.username_pw_set(
                username=USERNAME,
                password=PASSWORD,
            )

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        rc,
    ):
        """
        Called after connection to MQTT broker.
        """

        if rc == 0:
            logger.info(
                "Connected to MQTT broker: %s:%s client_id=%s",
                BROKER_HOST,
                BROKER_PORT,
                self.client_id,
            )

            self.connected_event.set()

        else:
            logger.error(
                "MQTT connection failed. Return code: %s",
                rc,
            )

    def _on_disconnect(
        self,
        client,
        userdata,
        rc,
    ):
        """
        Called when MQTT client disconnects.
        """

        self.connected_event.clear()

        logger.info(
            "Disconnected from MQTT broker. Return code: %s",
            rc,
        )

    def _on_message(
        self,
        client,
        userdata,
        message,
    ):
        """
        Process received MQTT message.
        """

        payload = message.payload.decode(
            "utf-8",
            errors="ignore",
        )

        logger.info(
            "MQTT message received: topic=%s payload=%s",
            message.topic,
            payload,
        )

        if self.message_handler is not None:
            self.message_handler(
                message.topic,
                payload,
            )

    def connect(self):
        """
        Connect to MQTT broker and start network loop.
        """

        logger.info(
            "Connecting to MQTT broker: %s:%s",
            BROKER_HOST,
            BROKER_PORT,
        )

        self.client.connect(
            host=BROKER_HOST,
            port=BROKER_PORT,
            keepalive=KEEP_ALIVE,
        )

        self.client.loop_start()

        connected = self.connected_event.wait(timeout=10)

        if not connected:
            raise ConnectionError(
                f"Could not connect to MQTT broker "
                f"{BROKER_HOST}:{BROKER_PORT}"
            )

    def subscribe(
        self,
        topic: str,
        qos: int = 0,
    ):
        """
        Subscribe to MQTT topic.
        """

        result, message_id = self.client.subscribe(
            topic=topic,
            qos=qos,
        )

        if result != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"Could not subscribe to topic: {topic}"
            )

        logger.info(
            "Subscribed to MQTT topic: %s QoS=%s",
            topic,
            qos,
        )

        return message_id

    def publish(
        self,
        topic: str,
        payload: Union[dict, list, str, int, float],
        qos: int = 0,
        retain: bool = False,
    ):
        """
        Publish message to MQTT topic.
        """

        if isinstance(payload, (dict, list)):
            message = json.dumps(payload)
        else:
            message = str(payload)

        result = self.client.publish(
            topic=topic,
            payload=message,
            qos=qos,
            retain=retain,
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"Could not publish message to topic: {topic}"
            )

        logger.info(
            "MQTT message published: topic=%s qos=%s retain=%s payload=%s",
            topic,
            qos,
            retain,
            message,
        )

        return result

    def disconnect(self):
        """
        Disconnect from MQTT broker.
        """

        try:
            self.client.disconnect()
        finally:
            self.client.loop_stop()
            self.connected_event.clear()