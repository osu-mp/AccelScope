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
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType


class TestProjectConfig(unittest.TestCase):
	def setUp(self):
		"""Set up some initial data for testing."""
		self.label1 = Label("05:07:10.825020", "06:18:21.373460", "Stalk")
		self.label2 = Label("07:08:55.710520", "08:35:05.321800", "Kill Phase 1")

		self.file_entry1 = FileEntry("data/F202_2018-05-20.csv", "TODO_123", [self.label1, self.label2])
		self.file_entry2 = FileEntry("data/F202_2018-06-18.csv", "TODO_456", [self.label1])

		self.directory = DirectoryEntry("F202", [self.file_entry1, self.file_entry2])
		self.project = ProjectConfig("Cougars", "D:/OSU/AccelScopeDemo/", [self.directory])

	def test_to_dict(self):
		"""Test converting ProjectConfig to a dictionary."""
		project_dict = self.project.to_dict()
		self.assertEqual(project_dict['proj_name'], "Cougars")
		self.assertEqual(len(project_dict['entries'][0]['entries']), 2)  # 2 FileEntries

	def test_from_dict(self):
		"""Test creating ProjectConfig from a dictionary."""
		project_dict = self.project.to_dict()
		loaded_project = ProjectConfig.from_dict(project_dict)
		self.assertEqual(loaded_project.proj_name, "Cougars")
		self.assertEqual(len(loaded_project.entries), 1)
		self.assertEqual(len(loaded_project.entries[0].entries), 2)

	def test_project_config_serialization(self):
		output_settings = OutputSettings(
			output_type=OutputType.BEBE,
			downsample_method=DownsampleMethod.AVERAGE,
			output_period=OutputPeriod.ENTIRE_INPUT,
			output_frequency=16,
			buffer_minutes=5,
			round_to_minutes=1
		)
		project = ProjectConfig(
			proj_name="Test Project",
			data_root_directory="/path/to/data",
			entries=[],
			label_display=[]
		)
		project.output_settings = output_settings

		# Convert project config to dict
		project_dict = project.to_dict()
		expected_output_settings_dict = {
			"output_type": "bebe",
			"downsample_method": "average",
			"output_period": "entire_input",
			"output_frequency": 16,
			"buffer_minutes": 5,
			"round_to_minutes": 1
		}

		self.assertEqual(project_dict['output_settings'], expected_output_settings_dict)

		# Deserialize back to project config
		project_from_dict = ProjectConfig.from_dict(project_dict)

		self.assertEqual(project_from_dict.output_settings.output_type, OutputType.BEBE)
		self.assertEqual(project_from_dict.output_settings.downsample_method, DownsampleMethod.AVERAGE)
		self.assertEqual(project_from_dict.output_settings.output_period, OutputPeriod.ENTIRE_INPUT)
		self.assertEqual(project_from_dict.output_settings.output_frequency, 16)
		self.assertEqual(project_from_dict.output_settings.buffer_minutes, 5)
		self.assertEqual(project_from_dict.output_settings.round_to_minutes, 1)



if __name__ == '__main__':
	unittest.main()
