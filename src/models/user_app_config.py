class UserAppConfig:
	"""
	Data related to an individual user's app setup, to keep the look and feel the same at startup.
	Separate from project config.
	"""
	def __init__(self, last_opened_project=None, last_opened_file=None, window_geometry="1200x800",
	             project_browser_width=200, viewer_width=800, info_width=200, zoom_level=None,
	             axes_display=None, window_state=None, splitter_positions=None):
		self.last_opened_project = last_opened_project  # Path to last opened project JSON
		self.last_opened_file = last_opened_file  # File ID of last opened file
		self.window_geometry = window_geometry  # e.g., "1200x800" (width x height)
		self.project_browser_width = project_browser_width  # Width of the project browser pane
		self.viewer_width = viewer_width
		self.info_width = info_width
		self.zoom_level = zoom_level  # Zoom/scale level for the viewer
		self.axes_display = axes_display or {'x': True, 'y': True, 'z': True}  # Whether axes (X/Y/Z) are displayed
		self.window_state = window_state  # Whether the window was maximized or minimized
		self.splitter_positions = splitter_positions  # Splitter positions (like the divider between viewer & project browser)

	def to_dict(self):
		"""Convert UserAppConfig instance to a dictionary."""
		return {
			'last_opened_project': self.last_opened_project,
			'last_opened_file': self.last_opened_file,
			'window_geometry': self.window_geometry,
			'project_browser_width': self.project_browser_width,
			'viewer_width': self.viewer_width,
			'info_width': self.info_width,
			'zoom_level': self.zoom_level,
			'axes_display': self.axes_display,
			'window_state': self.window_state,
			'splitter_positions': self.splitter_positions
		}

	@classmethod
	def from_dict(cls, data):
		"""Create a UserAppConfig instance from a dictionary."""
		return cls(
			last_opened_project=data.get('last_opened_project'),
			last_opened_file=data.get('last_opened_file'),
			window_geometry=data.get('window_geometry'),
			project_browser_width=data.get('project_browser_width'),
			viewer_width=data.get('viewer_width'),
			info_width=data.get('info_width'),
			zoom_level=data.get('zoom_level'),
			axes_display=data.get('axes_display', {'x': True, 'y': True, 'z': True}),
			window_state=data.get('window_state'),
			splitter_positions=data.get('splitter_positions')
		)
