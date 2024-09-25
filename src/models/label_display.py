class LabelDisplay:
	"""
	This controls how labels are displayed in the GUI and in the output files.
	"""
	def __init__(self, display_name, color, alpha, output_value):
		self.display_name = display_name
		self.color = color
		self.alpha = alpha
		self.output_value = output_value

	def to_dict(self):
		"""Convert LabelDisplay instance to a dictionary."""
		return {
			'display_name': self.display_name,
			'color': self.color,
			'alpha': self.alpha,
			'output_value': self.output_value
		}

	@staticmethod
	def from_dict(data):
		"""Create a LabelDisplay instance from a dictionary."""
		return LabelDisplay(
			display_name=data['display_name'],
			color=data['color'],
			alpha=data['alpha'],
			output_value=data['output_value']
		)
