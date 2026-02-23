import unittest
import json
from pathlib import Path
import sys

# Add the parent directory of src to sys.path to resolve the src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.label import Label
from models.project_config import ProjectConfig
from models.user_config import UserConfig
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType


class TestProjectConfig(unittest.TestCase):
	def setUp(self):
		"""Set up some initial data for testing."""
		self.label1 = Label("05:07:10.825020", "06:18:21.373460", "Stalk")
		self.label2 = Label("07:08:55.710520", "08:35:05.321800", "Kill Phase 1")

		self.file_entry1 = FileEntry("data/F202_2018-05-20.csv", "TODO_123", [self.label1, self.label2])
		self.file_entry2 = FileEntry("data/F202_2018-06-18.csv", "TODO_456", [self.label1])

		self.directory = DirectoryEntry("F202", [self.file_entry1, self.file_entry2])
		self.project = ProjectConfig(
			"Cougars",
			users=[UserConfig(username="testuser", data_root="D:/OSU/AccelScopeDemo/")],
			entries=[self.directory],
		)

	def test_to_dict(self):
		"""Test converting ProjectConfig to a dictionary."""
		project_dict = self.project.to_dict()
		self.assertEqual(project_dict['proj_name'], "Cougars")
		self.assertEqual(len(project_dict['entries'][0]['entries']), 2)  # 2 FileEntries
		self.assertEqual(len(project_dict['users']), 1)
		self.assertEqual(project_dict['users'][0]['username'], "testuser")

	def test_from_dict(self):
		"""Test creating ProjectConfig from a dictionary."""
		project_dict = self.project.to_dict()
		loaded_project = ProjectConfig.from_dict(project_dict)
		self.assertEqual(loaded_project.proj_name, "Cougars")
		self.assertEqual(len(loaded_project.entries), 1)
		self.assertEqual(len(loaded_project.entries[0].entries), 2)
		self.assertEqual(len(loaded_project.users), 1)
		self.assertEqual(loaded_project.users[0].username, "testuser")
		self.assertEqual(loaded_project.users[0].data_root, "D:/OSU/AccelScopeDemo/")

	def test_get_user_by_username(self):
		"""Test looking up a user by username."""
		user = self.project.get_user_by_username("testuser")
		self.assertIsNotNone(user)
		self.assertEqual(user.data_root, "D:/OSU/AccelScopeDemo/")

		missing = self.project.get_user_by_username("nobody")
		self.assertIsNone(missing)

	def test_project_config_serialization(self):
		output_settings = OutputSettings(
			output_type=OutputType.BEBE,
			downsample_methods=[DownsampleMethod.AVERAGE],
			output_period=OutputPeriod.ENTIRE_INPUT,
			output_frequency=16,
			buffer_minutes=5,
			round_to_minutes=1
		)
		project = ProjectConfig(
			proj_name="Test Project",
			users=[UserConfig(username="alice", data_root="/path/to/data")],
			entries=[],
			label_display=[]
		)
		project.output_settings = output_settings

		# Convert project config to dict
		project_dict = project.to_dict()
		expected_output_settings_dict = {
			"output_type": "bebe",
			"downsample_methods": ["average"],
			"output_period": "entire_input",
			"output_frequency": 16,
			"buffer_minutes": 5,
			"round_to_minutes": 1
		}

		self.assertEqual(project_dict['output_settings'], expected_output_settings_dict)

		# Deserialize back to project config
		project_from_dict = ProjectConfig.from_dict(project_dict)

		self.assertEqual(project_from_dict.output_settings.output_type, OutputType.BEBE)
		self.assertEqual(project_from_dict.output_settings.downsample_methods, [DownsampleMethod.AVERAGE])
		self.assertEqual(project_from_dict.output_settings.output_period, OutputPeriod.ENTIRE_INPUT)
		self.assertEqual(project_from_dict.output_settings.output_frequency, 16)
		self.assertEqual(project_from_dict.output_settings.buffer_minutes, 5)
		self.assertEqual(project_from_dict.output_settings.round_to_minutes, 1)

	def test_empty_users_list(self):
		"""Test ProjectConfig with no users."""
		project = ProjectConfig(proj_name="Empty")
		self.assertEqual(project.users, [])
		d = project.to_dict()
		self.assertEqual(d["users"], [])
		loaded = ProjectConfig.from_dict(d)
		self.assertEqual(loaded.users, [])



if __name__ == '__main__':
	unittest.main()
