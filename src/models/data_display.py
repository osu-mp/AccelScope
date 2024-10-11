class DataDisplay:
	"""
	This class focuses on how the input data (x/y/z accel values) is displayed
	in the GUI and output to smaller CSVs.
	"""
	def __init__(self, input_name, display_name, color, alpha, output_name):
		self.input_name = input_name
		self.display_name = display_name
		self.color = color
		self.alpha = alpha
		self.output_name = output_name

	def to_dict(self):
		"""Convert DataDisplay instance to a dictionary."""
		return {
			'input_name': self.input_name,
			'display_name': self.display_name,
			'color': self.color,
			'alpha': self.alpha,
			'output_name': self.output_name
		}

	@staticmethod
	def from_dict(data):
		"""Create a DataDisplay instance from a dictionary."""
		return DataDisplay(
			input_name=data['input_name'],
			display_name=data['display_name'],
			color=data['color'],
			alpha=data['alpha'],
			output_name=data['output_name']
		)
