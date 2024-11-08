import unittest
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType


class TestOutputSettings(unittest.TestCase):

    def test_to_dict(self):
        settings = OutputSettings(
            output_type=OutputType.BEBE,
            downsample_method=DownsampleMethod.AVERAGE,
            output_period=OutputPeriod.LABELED_WITH_BUFFER,
            output_frequency=8,
            buffer_minutes=10,
            round_to_minutes=2
        )
        expected = {
            "output_type": "bebe",
            "downsample_method": "average",
            "output_period": "labeled_with_buffer",
            "output_frequency": 8,
            "buffer_minutes": 10,
            "round_to_minutes": 2
        }
        self.assertEqual(settings.to_dict(), expected)

    def test_from_dict(self):
        data = {
            "output_type": "bebe",
            "downsample_method": "average",
            "output_period": "labeled_with_buffer",
            "output_frequency": 8,
            "buffer_minutes": 10,
            "round_to_minutes": 2
        }
        settings = OutputSettings.from_dict(data)
        self.assertEqual(settings.output_type, OutputType.BEBE)
        self.assertEqual(settings.downsample_method, DownsampleMethod.AVERAGE)
        self.assertEqual(settings.output_period, OutputPeriod.LABELED_WITH_BUFFER)
        self.assertEqual(settings.output_frequency, 8)
        self.assertEqual(settings.buffer_minutes, 10)
        self.assertEqual(settings.round_to_minutes, 2)

    def test_default_values(self):
        settings = OutputSettings()
        self.assertEqual(settings.output_type, OutputType.BEBE)
        self.assertEqual(settings.downsample_method, DownsampleMethod.AVERAGE)
        self.assertEqual(settings.output_period, OutputPeriod.ENTIRE_INPUT)
        self.assertEqual(settings.output_frequency, 16)
        self.assertEqual(settings.buffer_minutes, 5)
        self.assertEqual(settings.round_to_minutes, 1)


if __name__ == '__main__':
    unittest.main()
