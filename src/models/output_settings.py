from enum import Enum


class DownsampleMethod(Enum):
    """
    Enum to define different methods of downsampling the accelerometer data.
    """
    AVERAGE = "average"         # Downsample by averaging N points into 1
    NTH_VALUE = "nth_value"     # Downsample by selecting every Nth point
    MIN = "min"                 # Downsample by taking the minimum of N points
    MAX = "max"                 # Downsample by taking the maximum of N points


class OutputPeriod(Enum):
    """
    Enum to specify the period of data that should be included in the output.
    """
    ENTIRE_INPUT = "entire_input"
    LABELED_WITH_BUFFER = "labeled_with_buffer"


class OutputType(Enum):
    """
    Enum to represent the types of output formats supported.
    """
    BEBE = "bebe"


class OutputSettings:
	def __init__(self, output_type=OutputType.BEBE, downsample_methods=None,
	             output_period=OutputPeriod.ENTIRE_INPUT, output_frequency=16, buffer_minutes=5, round_to_minutes=1):
		"""
		Initializes the output settings for generating output files.

		:param output_type: Type of output (enum, e.g. BEBE).
		:param downsample_methods: List of downsampling methods to apply.
		:param output_period: Period of the data to output (enum).
		:param output_frequency: Frequency of the output data in Hz (integer).
		:param buffer_minutes: Buffer to add around labeled periods in minutes (integer).
		:param round_to_minutes: Round the output data to the nearest multiple of X minutes (integer).
		"""
		self.output_type = output_type
		self.downsample_methods = downsample_methods or [DownsampleMethod.AVERAGE]
		self.output_period = output_period
		self.output_frequency = output_frequency
		self.buffer_minutes = buffer_minutes
		self.round_to_minutes = round_to_minutes

	def to_dict(self):
		"""Converts the output settings to a dictionary representation."""
		return {
			"output_type": self.output_type.value,
			"downsample_methods": [m.value for m in self.downsample_methods],
			"output_period": self.output_period.value,
			"output_frequency": self.output_frequency,
			"buffer_minutes": self.buffer_minutes,
			"round_to_minutes": self.round_to_minutes
		}

	@staticmethod
	def from_dict(data):
		"""Creates an instance of OutputSettings from a dictionary representation."""
		# Support legacy single downsample_method field
		if "downsample_methods" in data:
			methods = [DownsampleMethod(m) for m in data["downsample_methods"]]
		elif "downsample_method" in data:
			methods = [DownsampleMethod(data["downsample_method"])]
		else:
			methods = [DownsampleMethod.AVERAGE]

		return OutputSettings(
			output_type=OutputType(data.get("output_type", OutputType.BEBE.value)),
			downsample_methods=methods,
			output_period=OutputPeriod(data.get("output_period", OutputPeriod.ENTIRE_INPUT.value)),
			output_frequency=data.get("output_frequency", 16),
			buffer_minutes=data.get("buffer_minutes", 5),
			round_to_minutes=data.get("round_to_minutes", 1)
		)
