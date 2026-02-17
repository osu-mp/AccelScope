import unittest
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType


class TestOutputSettings(unittest.TestCase):

    def test_to_dict(self):
        settings = OutputSettings(
            output_type=OutputType.BEBE,
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_period=OutputPeriod.LABELED_WITH_BUFFER,
            output_frequency=8,
            buffer_minutes=10,
            round_to_minutes=2
        )
        expected = {
            "output_type": "bebe",
            "downsample_methods": ["average"],
            "output_period": "labeled_with_buffer",
            "output_frequency": 8,
            "buffer_minutes": 10,
            "round_to_minutes": 2
        }
        self.assertEqual(settings.to_dict(), expected)

    def test_to_dict_multiple_methods(self):
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE, DownsampleMethod.MIN, DownsampleMethod.MAX],
        )
        result = settings.to_dict()
        self.assertEqual(result["downsample_methods"], ["average", "min", "max"])

    def test_from_dict(self):
        data = {
            "output_type": "bebe",
            "downsample_methods": ["average"],
            "output_period": "labeled_with_buffer",
            "output_frequency": 8,
            "buffer_minutes": 10,
            "round_to_minutes": 2
        }
        settings = OutputSettings.from_dict(data)
        self.assertEqual(settings.output_type, OutputType.BEBE)
        self.assertEqual(settings.downsample_methods, [DownsampleMethod.AVERAGE])
        self.assertEqual(settings.output_period, OutputPeriod.LABELED_WITH_BUFFER)
        self.assertEqual(settings.output_frequency, 8)
        self.assertEqual(settings.buffer_minutes, 10)
        self.assertEqual(settings.round_to_minutes, 2)

    def test_from_dict_legacy_single_method(self):
        """Legacy configs with singular downsample_method should still load."""
        data = {
            "output_type": "bebe",
            "downsample_method": "nth_value",
            "output_period": "entire_input",
        }
        settings = OutputSettings.from_dict(data)
        self.assertEqual(settings.downsample_methods, [DownsampleMethod.NTH_VALUE])

    def test_default_values(self):
        settings = OutputSettings()
        self.assertEqual(settings.output_type, OutputType.BEBE)
        self.assertEqual(settings.downsample_methods, [DownsampleMethod.AVERAGE])
        self.assertEqual(settings.output_period, OutputPeriod.ENTIRE_INPUT)
        self.assertEqual(settings.output_frequency, 16)
        self.assertEqual(settings.buffer_minutes, 5)
        self.assertEqual(settings.round_to_minutes, 1)

    def test_round_trip(self):
        """Serialize and deserialize should produce equivalent settings."""
        original = OutputSettings(
            downsample_methods=[DownsampleMethod.NTH_VALUE, DownsampleMethod.MAX],
            output_period=OutputPeriod.LABELED_WITH_BUFFER,
            output_frequency=4,
            buffer_minutes=10,
            round_to_minutes=5
        )
        restored = OutputSettings.from_dict(original.to_dict())
        self.assertEqual(original.to_dict(), restored.to_dict())


if __name__ == '__main__':
    unittest.main()
