import unittest
import tempfile
import os
import shutil
from services.project_service import ProjectService
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.project_config import ProjectConfig
from unittest.mock import patch


class TestProjectService(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to act as the root data directory
        self.test_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.test_dir, "project_config.json")

        # Create an instance of ProjectService and mock project configuration
        self.project_service = ProjectService()

        # Initialize ProjectConfig with temp directory as root
        self.project_config = ProjectConfig(
            proj_name="TestProject",
            data_root_directory=self.test_dir,
            entries=[DirectoryEntry("F202_27905_010518_072219")],
            data_display=[],
            label_display=[]
        )
        self.project_service.current_project_config = self.project_config
        self.project_service.current_project_path = self.project_path

    def tearDown(self):
        # Remove the temporary directory after each test
        shutil.rmtree(self.test_dir)

    def test_load_project(self):
        # Write project configuration to temporary project path
        with open(self.project_path, 'w') as f:
            f.write(r'{"proj_name": "TestProject", "data_root_directory": "' + self.test_dir.replace('\\', '/') + r'", "entries": []}')

        # Load the project and check that the name matches
        with patch("os.path.exists", return_value=True):
            self.project_service.load_project(self.project_path)
            self.assertEqual(self.project_service.current_project_config.proj_name, "TestProject")

    def test_save_project(self):
        # Save the current project config and ensure the file is created
        self.project_service.save_project()
        self.assertTrue(os.path.exists(self.project_path))

    def test_add_directory(self):
        # Add a new subdirectory under the existing directory
        self.project_service.add_directory("F202_27905_010518_072219", "NewSubDir")
        self.assertEqual(len(self.project_service.current_project_config.entries[0].entries), 1)
        self.assertEqual(self.project_service.current_project_config.entries[0].entries[0].name, "NewSubDir")

    def test_add_file(self):
        # Add a file to the existing directory
        file_entry = FileEntry(path="F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv")
        self.project_service.add_file("F202_27905_010518_072219", file_entry)
        self.assertEqual(len(self.project_service.current_project_config.entries[0].entries), 1)
        self.assertIsInstance(self.project_service.current_project_config.entries[0].entries[0], FileEntry)

    def test_get_file_entry(self):
        # Add a file and retrieve it by ID
        key = "hardcoded_uuid"
        file_entry = FileEntry(path="F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv")
        self.project_service.add_file("F202_27905_010518_072219", file_entry)
        file_entry.file_id = key
        retrieved_entry = self.project_service.get_file_entry(key)
        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.file_id, key)

    def test_get_file_path(self):
        # Add a file and get its full path
        file_entry = FileEntry(path="F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv")
        self.project_service.add_file("F202_27905_010518_072219", file_entry)
        full_path = self.project_service.get_file_path(file_entry)
        expected_path = os.path.join(self.test_dir, "F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv")
        self.assertEqual(full_path.replace("\\", "/"), expected_path.replace("\\", "/"))

    def test_get_plot_title(self):
        # Test generating plot title
        file_entry = FileEntry(path="F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv")
        self.project_service.add_file("F202_27905_010518_072219", file_entry)
        title = self.project_service.get_plot_title(file_entry)
        expected_title = "F202    2018-06-09"
        self.assertEqual(title, expected_title)

    def test_get_step_time_ms(self):
        # Test for 16 Hz input frequency
        project_service = ProjectService()
        project_service.input_freq = 16
        self.assertEqual(project_service.get_step_time_ms(), 63)

        # Test for 10 Hz input frequency (should return 100)
        project_service.input_freq = 10
        self.assertEqual(project_service.get_step_time_ms(), 100)

        # Test for 1 Hz input frequency (should return 1000)
        project_service.input_freq = 1
        self.assertEqual(project_service.get_step_time_ms(), 1000)

        # Test for 25 Hz input frequency (should return 40)
        project_service.input_freq = 25
        self.assertEqual(project_service.get_step_time_ms(), 40)

if __name__ == '__main__':
    unittest.main()
