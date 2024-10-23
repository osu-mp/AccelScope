from enum import Enum


class DownsampleMethod(Enum):
    """
    Enum to define different methods of downsampling the accelerometer data.
    AVERAGE: Takes the average of N consecutive points and outputs a single point.
    NTH_VALUE: Takes every Nth value from the dataset and discards the rest.
    """
    AVERAGE = "average"         # Downsample by averaging N points into 1
    NTH_VALUE = "nth_value"     # Downsample by selecting every Nth point


class OutputPeriod(Enum):
    """
    Enum to specify the period of data that should be included in the output.
    ENTIRE_INPUT: Outputs the entire dataset, regardless of labels or time ranges.
    LABELED_WITH_BUFFER: Outputs only the labeled periods with an additional buffer of time on either side.
    """
    ENTIRE_INPUT = "entire_input"              # Output the entire dataset
    LABELED_WITH_BUFFER = "labeled_with_buffer"  # Output only labeled periods with a buffer


class OutputType(Enum):
    """
    Enum to represent the types of output formats supported.
    BEBE: A custom format designed for BEBE format (Bio-logger Ethogram Benchmark).
    OTHER: A placeholder for any other future output types that may be added.
    """
    BEBE = "bebe"             # Custom output format for BEBE
    OTHER = "other"           # Placeholder for additional output formats


class OutputSettings:
	def __init__(self, output_type=OutputType.BEBE, downsample_method=DownsampleMethod.AVERAGE,
	             output_period=OutputPeriod.ENTIRE_INPUT, output_frequency=16, buffer_minutes=5, round_to_minutes=1):
		"""
		Initializes the output settings for generating output files.

		:param output_type: Type of output (enum, e.g. BEBE).
		:param downsample_method: Method of downsampling (enum, e.g. AVERAGE or NTH_VALUE).
		:param output_period: Period of the data to output (enum, e.g. ENTIRE_INPUT or LABELED_WITH_BUFFER).
		:param output_frequency: Frequency of the output data in Hz (integer).
		:param buffer_minutes: Buffer to add around labeled periods in minutes (integer).
		:param round_to_minutes: Round the output data to the nearest multiple of X minutes (integer).
		"""
		self.output_type = output_type
		self.downsample_method = downsample_method
		self.output_period = output_period
		self.output_frequency = output_frequency
		self.buffer_minutes = buffer_minutes
		self.round_to_minutes = round_to_minutes

	def to_dict(self):
		"""
		Converts the output settings to a dictionary representation.
		"""
		return {
			"output_type": self.output_type.value,
			"downsample_method": self.downsample_method.value,
			"output_period": self.output_period.value,
			"output_frequency": self.output_frequency,
			"buffer_minutes": self.buffer_minutes,
			"round_to_minutes": self.round_to_minutes
		}

	@staticmethod
	def from_dict(data):
		"""
		Creates an instance of OutputSettings from a dictionary representation.
		"""
		return OutputSettings(
			output_type=OutputType(data.get("output_type", OutputType.BEBE.value)),
			downsample_method=DownsampleMethod(data.get("downsample_method", DownsampleMethod.AVERAGE.value)),
			output_period=OutputPeriod(data.get("output_period", OutputPeriod.ENTIRE_INPUT.value)),
			output_frequency=data.get("output_frequency", 16),
			buffer_minutes=data.get("buffer_minutes", 5),
			round_to_minutes=data.get("round_to_minutes", 1)
		)
