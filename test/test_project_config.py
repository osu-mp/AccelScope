import unittest
import json
from pathlib import Path
import sys

# Add the parent directory of src to sys.path to resolve the src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.project_config import ProjectConfig, Directory, FileEntry


class TestProjectConfig(unittest.TestCase):
	def setUp(self):
		# Setup a path for test config file
		self.test_config_path = Path("test_project_config.json")
		self.project_config = ProjectConfig(self.test_config_path)

	def tearDown(self):
		# Cleanup the config file after tests
		if self.test_config_path.exists():
			self.test_config_path.unlink()

	def test_initialization(self):
		self.assertEqual(self.project_config.config_path, self.test_config_path)
		self.assertIsNone(self.project_config.data_root_directory)
		self.assertIsNotNone(self.project_config.root_directory)

	def test_save_config(self):
		# Setting up test data
		self.project_config.data_root_directory = "/test/path"
		# Save the config
		self.project_config.save_config()
		# Check if the file is created and contents are correct
		self.assertTrue(self.test_config_path.exists())
		with open(self.test_config_path, 'r') as file:
			data = json.load(file)
			self.assertEqual(data['data_root_directory'], "/test/path")

	def test_load_config(self):
		# Create a config file to load
		with open(self.test_config_path, 'w') as file:
			json.dump({
				"data_root_directory": "/loaded/path",
				"root_directory": {"name": "Root", "entries": []}
			}, file)

		# Load the config
		self.project_config.load_config()
		self.assertEqual(self.project_config.data_root_directory, "/loaded/path")

	def test_nonexistent_file_load(self):
		# Ensure no config file exists
		if self.test_config_path.exists():
			self.test_config_path.unlink()

		self.project_config.load_config()
		self.assertIsNone(self.project_config.data_root_directory)  # Assuming default is None

	def test_nested_directory_structure(self):
		# Set up the nested directory structure
		root = Directory("Root")
		m202 = Directory("M202")
		walking = Directory("Walking")
		m202.entries.append(FileEntry("event1.csv"))
		m202.entries.append(FileEntry("event2.csv"))
		walking.entries.append(FileEntry("event3.csv"))
		m202.entries.append(walking)
		f201 = Directory("F201")
		f201.entries.append(FileEntry("event4.csv"))
		root.entries.append(m202)
		root.entries.append(f201)

		self.project_config.root_directory = root
		self.project_config.data_root_directory = "/path/to/data/root"

		# Save the config
		self.project_config.save_config()

		# Load the config
		loaded_config = ProjectConfig(self.test_config_path)
		loaded_config.load_config()

		# Verify that the loaded config matches the original
		self.assertEqual(loaded_config.data_root_directory, self.project_config.data_root_directory)
		self.assertEqual(len(loaded_config.root_directory.entries), 2)  # M202 and F201
		m202_loaded = loaded_config.root_directory.entries[0]
		self.assertEqual(m202_loaded.name, "M202")
		self.assertIsInstance(m202_loaded.entries[-1], Directory)  # The Walking directory
		self.assertEqual(m202_loaded.entries[-1].entries[0].path, "event3.csv")  # The file in Walking directory


if __name__ == '__main__':
	unittest.main()
