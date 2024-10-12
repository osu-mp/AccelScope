import unittest
import os
import json
from services.user_app_config_service import UserAppConfigService
from models.user_app_config import UserAppConfig


class TestUserAppConfigService(unittest.TestCase):

	def setUp(self):
		"""Setup before each test."""
		# Ensure the test config file doesn't exist before running tests
		self.test_config_file = UserAppConfigService.USER_CONFIG_FILE
		if os.path.exists(self.test_config_file):
			os.remove(self.test_config_file)

	def tearDown(self):
		"""Clean up after each test."""
		# Remove the test config file after each test
		if os.path.exists(self.test_config_file):
			os.remove(self.test_config_file)

	def test_save_to_file(self):
		"""Test saving the UserAppConfig to a file."""
		config = UserAppConfig(
			last_opened_project="test_project.json",
			last_opened_file="test_file.csv",
			window_geometry="1200x800",
			project_browser_width=200,
			info_width=150,
			zoom_level=1.5,
			axes_display={"x": True, "y": False, "z": True},
			window_state="zoomed",
		)

		# Save the configuration
		with open(self.test_config_file, 'w') as file:
			json.dump(config.__dict__, file, indent=4)

		# Verify file contents
		with open(self.test_config_file, 'r') as file:
			data = json.load(file)
			self.assertEqual(data['last_opened_project'], "test_project.json")
			self.assertEqual(data['last_opened_file'], "test_file.csv")
			self.assertEqual(data['window_geometry'], "1200x800")
			self.assertEqual(data['project_browser_width'], 200)
			self.assertEqual(data['info_width'], 150)
			self.assertEqual(data['zoom_level'], 1.5)
			self.assertEqual(data['axes_display'], {"x": True, "y": False, "z": True})
			self.assertEqual(data['window_state'], "zoomed")

	def test_load_from_file(self):
		"""Test loading the UserAppConfig from a file."""
		# Create a sample config file
		sample_config = {
			"last_opened_project": "sample_project.json",
			"last_opened_file": "sample_file.csv",
			"window_geometry": "800x600",
			"project_browser_width": 100,
			"info_width": 300,
			"zoom_level": 1.2,
			"axes_display": {"x": False, "y": True, "z": False},
			"window_state": "normal",
		}

		with open(self.test_config_file, 'w') as file:
			json.dump(sample_config, file, indent=4)

		# Load the configuration
		loaded_config = UserAppConfigService.load_from_file()

		# Verify loaded values
		self.assertEqual(loaded_config.last_opened_project, "sample_project.json")
		self.assertEqual(loaded_config.last_opened_file, "sample_file.csv")
		self.assertEqual(loaded_config.window_geometry, "800x600")
		self.assertEqual(loaded_config.project_browser_width, 100)
		self.assertEqual(loaded_config.info_width, 300)
		self.assertEqual(loaded_config.zoom_level, 1.2)
		self.assertEqual(loaded_config.axes_display, {"x": False, "y": True, "z": False})
		self.assertEqual(loaded_config.window_state, "normal")

	def test_load_nonexistent_file(self):
		"""Test loading UserAppConfig when the file does not exist."""
		# Load configuration, should return a new default instance
		loaded_config = UserAppConfigService.load_from_file()

		# Verify loaded config is the default one
		self.assertIsInstance(loaded_config, UserAppConfig)
		self.assertIsNone(loaded_config.last_opened_project)
		self.assertIsNone(loaded_config.last_opened_file)
		self.assertIsNotNone(loaded_config.window_geometry)
		self.assertIsNotNone(loaded_config.project_browser_width)
		self.assertIsNotNone(loaded_config.info_width)
		self.assertIsNone(loaded_config.zoom_level)
		self.assertIsNone(loaded_config.window_state)
		self.assertEqual(loaded_config.axes_display, {"x": True, "y": True, "z": True})


if __name__ == '__main__':
	unittest.main()
