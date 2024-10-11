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


class TestProjectConfig(unittest.TestCase):
	def setUp(self):
		"""Set up some initial data for testing."""
		self.label1 = Label("1900-01-01T05:07:10.825020+00:00", "1900-01-01T06:18:21.373460+00:00", "Stalk")
		self.label2 = Label("1900-01-01T07:08:55.710520+00:00", "1900-01-01T08:35:05.321800+00:00", "Kill Phase 1")

		self.file_entry1 = FileEntry("data/F202_2018-05-20.csv", "TODO_123", [self.label1, self.label2])
		self.file_entry2 = FileEntry("data/F202_2018-06-18.csv", "TODO_456", [self.label1])

		self.directory = DirectoryEntry("F202", [self.file_entry1, self.file_entry2])
		self.project = ProjectConfig("Cougars", "D:/OSU/AccelScopeDemo/", [self.directory])

	def test_find_file_by_id(self):
		"""Test finding files by id."""
		found_file = self.project.find_file_by_id("TODO_123")
		self.assertIsNotNone(found_file)
		self.assertEqual(found_file.file_id, "TODO_123")
		self.assertEqual(found_file.path, "data/F202_2018-05-20.csv")

		not_found_file = self.project.find_file_by_id("NON_EXISTENT")
		self.assertIsNone(not_found_file)

	def test_add_directory(self):
		"""Test adding a new directory."""
		self.project.add_directory("F202", "M201")
		parent_dir = self.project.find_directory_by_path("F202")
		self.assertEqual(len(parent_dir.entries), 3)  # Added new directory
		new_dir = self.project.find_directory_by_path("F202/M201")
		self.assertIsNotNone(new_dir)
		self.assertEqual(new_dir.name, "M201")

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


if __name__ == '__main__':
	unittest.main()
