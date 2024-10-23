import logging
import numpy as np
import pandas as pd


class AccelDataParser:
	def __init__(self, file_path):
		"""
		Initializes the AccelDataParser class with the path to the CSV file.

		Parameters:
		- file_path: Path to the CSV file.
		"""
		self.file_path = file_path
		self.data = None

	def read_data(self, start_time=None, end_time=None, num_samples=0, method='raw'):
		"""
		Reads and optionally filters and downsamples the accelerometer data from the CSV file.

		Restricts data to only a single day by ignoring any data that after 23:59

		Parameters:
		- start_time: Optional; start time to filter data. Default is the start of the dataset.
		- end_time: Optional; end time to filter data. Default is the end of the dataset.
		- num_samples: Optional; number of samples to return, evenly spaced across the range. Default is 0 (returns all data).
		- method: 'raw' for raw sampling, 'average' for averaging groups of samples.

		Returns:
		- A DataFrame containing the filtered and/or downsampled data.
		"""
		# Read the CSV into a DataFrame
		self.data = pd.read_csv(self.file_path, skiprows=1)

		# Combine 'UTC DateTime' and 'Milliseconds' into a single timestamp
		self.data['Timestamp'] = pd.to_datetime(
			self.data['UTC DateTime'] + '.' + self.data['Milliseconds'].astype(str).str.zfill(3),
			format='%H:%M:%S.%f'
		)

		# Convert 'Timestamp' to time only (without date)
		self.data['TimeOnly'] = self.data['Timestamp'].dt.time

		# Drop the original 'UTC DateTime' and 'Milliseconds' columns
		self.data.drop(columns=['UTC DateTime', 'Milliseconds'], inplace=True)

		# Detect the rollover point where time goes from '23:59:59' to '00:00:00'
		# TODO: clarify how to handle duplicate/rollover data with Wes
		# for i in range(1, len(self.data)):
		# 	if self.data['TimeOnly'].iloc[i] <= self.data['TimeOnly'].iloc[i - 1]:
		# 		# We've found the rollover point, cut off all data after this point
		# 		self.data = self.data.iloc[:i]
		# 		logging.info(f"Day rollover found at {i=}, stopping reading file {self.data.iloc[i-1]=}")
		# 		break

		# Filter by start_time and end_time if provided
		if start_time:
			start_time = pd.to_datetime(start_time).time()
			self.data = self.data[self.data['TimeOnly'] >= start_time]

		if end_time:
			end_time = pd.to_datetime(end_time).time()
			self.data = self.data[self.data['TimeOnly'] <= end_time]

		# If num_samples is specified and greater than 0, downsample the data
		if 0 < num_samples < len(self.data):
			if method == 'raw':
				# Raw sampling (every nth sample)
				indices = np.linspace(0, len(self.data) - 1, num_samples, dtype=int)
				self.data = self.data.iloc[indices]
			elif method == 'average':
				# Averaging groups of samples
				chunk_size = len(self.data) // num_samples
				self.data = self.data.groupby(np.arange(len(self.data)) // chunk_size).mean().head(num_samples)

		return self.data

	def write_data(self, output_path):
		"""
		Writes the current DataFrame to a new CSV file.

		Parameters:
		- output_path: Path where the CSV will be saved.
		"""
		if self.data is not None:
			self.data.to_csv(output_path, index=False)
		else:
			raise ValueError("No data to write. Please read or generate data first.")
