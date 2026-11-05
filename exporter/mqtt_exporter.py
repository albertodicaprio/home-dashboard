"""Translate ws3000-mqtt topics into Prometheus gauges."""

import logging
import math
import os
import re
import time

import paho.mqtt.client as mqtt
from prometheus_client import Gauge, start_http_server


TOPIC_PATTERN = re.compile(r"^home/ws-3000/(temperature|humidity)_CH([1-8])$")
TEMPERATURE = Gauge(
    "ws3000_temperature_celsius", "Station temperature in degrees Celsius", ["channel"]
)
HUMIDITY = Gauge(
    "ws3000_humidity_percent", "Station relative humidity in percent", ["channel"]
)
LAST_UPDATE = Gauge(
    "ws3000_last_update_timestamp_seconds",
    "Unix time of the last valid station reading",
    ["channel", "measurement"],
)


class StationMetrics:
    def __init__(self):
        self.units = None

    def handle(self, topic: str, payload: bytes) -> None:
        try:
            value = payload.decode("utf-8").strip()
        except UnicodeDecodeError:
            logging.warning("Ignoring non-UTF-8 MQTT payload on %s", topic)
            return

        if topic == "home/ws-3000/units":
            if value in ("Celsius", "Fahrenheit"):
                self.units = value
            else:
                logging.warning("Ignoring unknown station unit: %s", value)
            return

        match = TOPIC_PATTERN.fullmatch(topic)
        if not match:
            return
        measurement, channel = match.groups()
        try:
            number = float(value)
        except ValueError:
            logging.warning("Ignoring nonnumeric reading on %s: %s", topic, value)
            return
        if not math.isfinite(number):
            return

        if measurement == "temperature":
            if self.units is None:
                logging.warning("Waiting for station units before exporting temperature")
                return
            if self.units == "Fahrenheit":
                number = (number - 32) * 5 / 9
            TEMPERATURE.labels(channel).set(number)
        else:
            if not 0 <= number <= 100:
                return
            HUMIDITY.labels(channel).set(number)
        LAST_UPDATE.labels(channel, measurement).set(time.time())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start_http_server(8000)
    station = StationMetrics()
    client = mqtt.Client(client_id="ws3000-prometheus-exporter")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
            client.subscribe("home/ws-3000/#")
        else:
            logging.error("MQTT connection failed with code %s", rc)

    def on_message(client, userdata, message):
        station.handle(message.topic, message.payload)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(os.getenv("MQTT_HOST", "mosquitto"), 1883, keepalive=60)
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
