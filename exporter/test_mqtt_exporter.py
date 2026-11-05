import unittest

from mqtt_exporter import HUMIDITY, LAST_UPDATE, TEMPERATURE, StationMetrics


def sample_value(gauge, **labels):
    for metric in gauge.collect():
        for sample in metric.samples:
            if sample.labels == labels:
                return sample.value
    return None


class StationMetricsTest(unittest.TestCase):
    def test_five_channel_sample(self):
        station = StationMetrics()
        readings = {
            "units": "Celsius",
            "temperature_CH1": 23.3,
            "humidity_CH1": 42,
            "temperature_CH2": 22.4,
            "humidity_CH2": 45,
            "temperature_CH3": 23.0,
            "humidity_CH3": 44,
            "temperature_CH4": 23.5,
            "humidity_CH4": 41,
            "temperature_CH5": 8.6,
            "humidity_CH5": 81,
        }
        for key, value in readings.items():
            station.handle(f"home/ws-3000/{key}", str(value).encode())

        for channel, temperature, humidity in (
            ("1", 23.3, 42),
            ("2", 22.4, 45),
            ("3", 23.0, 44),
            ("4", 23.5, 41),
            ("5", 8.6, 81),
        ):
            self.assertEqual(sample_value(TEMPERATURE, channel=channel), temperature)
            self.assertEqual(sample_value(HUMIDITY, channel=channel), humidity)
        self.assertIsNotNone(
            sample_value(LAST_UPDATE, channel="3", measurement="temperature")
        )

    def test_fahrenheit_is_converted_to_celsius(self):
        station = StationMetrics()
        station.handle("home/ws-3000/temperature_CH8", b"68")
        self.assertIsNone(sample_value(TEMPERATURE, channel="8"))
        station.handle("home/ws-3000/units", b"Fahrenheit")
        station.handle("home/ws-3000/temperature_CH8", b"68")
        self.assertAlmostEqual(sample_value(TEMPERATURE, channel="8"), 20)


if __name__ == "__main__":
    unittest.main()
