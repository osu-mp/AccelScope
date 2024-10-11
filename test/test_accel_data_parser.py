from accel_data_parser import AccelDataParser  # Import your class
import os
import pandas as pd
import unittest

# Construct the relative path to the data file
data_path = os.path.join(os.path.dirname(__file__), 'data', 'F202_2018-06-18.csv')

class TestAccelDataParser(unittest.TestCase):

	def setUp(self):
		# This method will run before each test
		self.parser = AccelDataParser(data_path)  # Example CSV file for testing

	def test_read_all_data(self):
		df = self.parser.read_data()
		self.assertIsInstance(df, pd.DataFrame)
		self.assertFalse(df.empty)

	def test_read_filtered_data(self):
		df = self.parser.read_data(start_time="00:01:00", end_time="00:02:00")
		self.assertIsInstance(df, pd.DataFrame)
		self.assertGreater(len(df), 0)

	def test_read_with_sampling(self):
		df = self.parser.read_data(num_samples=10, method='raw')
		self.assertEqual(len(df), 10)

	def test_average_sampling(self):
		df = self.parser.read_data(num_samples=5, method='average')
		self.assertEqual(len(df), 5)

	def test_write_data(self):
		df = self.parser.read_data()
		self.parser.write_data("output_test.csv")
		written_df = pd.read_csv("output_test.csv")
		self.assertEqual(len(df), len(written_df))


if __name__ == '__main__':
	unittest.main()
