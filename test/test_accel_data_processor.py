import unittest
import pandas as pd
from datetime import datetime
from models.label import Label
from data_processing.accel_data_processor import AccelDataProcessor


class TestAccelDataProcessor(unittest.TestCase):
    def setUp(self):
        # Sample accelerometer data
        self.data = pd.DataFrame({
            'Timestamp': pd.date_range(start='2023-09-01 08:00:00', periods=10, freq='min'),
            'Acc X [g]': range(10),
            'Acc Y [g]': range(10, 20),
            'Acc Z [g]': range(20, 30)
        })

        # Sample labels
        self.labels = [
            Label(start_time=datetime(2023, 9, 1, 8, 2, 0), end_time=datetime(2023, 9, 1, 8, 4, 0), behavior='Stalk'),
            Label(start_time=datetime(2023, 9, 1, 8, 5, 0), end_time=datetime(2023, 9, 1, 8, 7, 0), behavior='Feed')
        ]

    def test_find_nearest_behaviors_middle(self):
        input_time = datetime(2023, 9, 1, 8, 3, 0)
        prev_label, next_label = AccelDataProcessor.find_nearest_behaviors(self.data, self.labels, input_time)

        print(f"Test Middle: prev_label={prev_label}, next_label={next_label}")

        # Ensure all timestamps are in datetime format for comparison
        prev_label = pd.Timestamp(prev_label).to_pydatetime()
        next_label = pd.Timestamp(next_label).to_pydatetime()

        self.assertEqual(prev_label, self.labels[0].start_time)
        self.assertEqual(next_label, self.labels[0].end_time)

    def test_find_nearest_behaviors_before_first_label(self):
        input_time = datetime(2023, 9, 1, 8, 0, 0)
        prev_label, next_label = AccelDataProcessor.find_nearest_behaviors(self.data, self.labels, input_time)

        print(f"Test Before First Label: prev_label={prev_label}, next_label={next_label}")

        # Ensure all timestamps are in datetime format for comparison
        prev_label = pd.Timestamp(prev_label).to_pydatetime()
        next_label = pd.Timestamp(next_label).to_pydatetime()

        self.assertEqual(prev_label, self.data['Timestamp'].min().to_pydatetime())
        self.assertEqual(next_label, self.labels[0].start_time)

    def test_find_nearest_behaviors_after_last_label(self):
        input_time = datetime(2023, 9, 1, 8, 8, 0)
        prev_label, next_label = AccelDataProcessor.find_nearest_behaviors(self.data, self.labels, input_time)

        print(f"Test After Last Label: prev_label={prev_label}, next_label={next_label}")

        # Ensure all timestamps are in datetime format for comparison
        prev_label = pd.Timestamp(prev_label).to_pydatetime()
        next_label = pd.Timestamp(next_label).to_pydatetime()

        self.assertEqual(prev_label, self.labels[-1].end_time)
        self.assertEqual(next_label, self.data['Timestamp'].max().to_pydatetime())

    def test_find_nearest_behaviors_within_label(self):
        input_time = datetime(2023, 9, 1, 8, 6, 0)
        prev_label, next_label = AccelDataProcessor.find_nearest_behaviors(self.data, self.labels, input_time)

        print(f"Test Within Label: prev_label={prev_label}, next_label={next_label}")

        # Ensure all timestamps are in datetime format for comparison
        prev_label = pd.Timestamp(prev_label).to_pydatetime()
        next_label = pd.Timestamp(next_label).to_pydatetime()

        self.assertEqual(prev_label, self.labels[1].start_time)
        self.assertEqual(next_label, self.labels[1].end_time)


if __name__ == '__main__':
    unittest.main()
