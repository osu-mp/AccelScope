import unittest
import tempfile
import os
import shutil
from services.project_service import ProjectService
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.project_config import ProjectConfig
from models.user_config import UserConfig
from models.output_settings import OutputSettings, OutputType, DownsampleMethod, OutputPeriod
from unittest.mock import patch

class TestProjectService(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to act as the root data directory
        self.test_dir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.test_dir, "project_config.json")

        # Create an instance of ProjectService and mock project configuration
        self.project_service = ProjectService()

        # Initialize OutputSettings with defaults
        self.output_settings = OutputSettings(
            output_type=OutputType.BEBE,
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=4
        )

        # Initialize ProjectConfig with temp directory as root and mock output settings
        self.project_config = ProjectConfig(
            proj_name="TestProject",
            users=[UserConfig(username="default_user", data_root=self.test_dir)],
            entries=[DirectoryEntry("F202_27905_010518_072219")],
            label_display=[],
            output_settings=self.output_settings
        )

        # Set the project config in the service and resolve the data root directory
        self.project_service.current_project_config = self.project_config
        self.project_service.current_project_path = self.project_path

        # Manually set _active_data_root since getpass.getuser() won't match "default_user"
        self.project_service._active_data_root = self.test_dir

    def tearDown(self):
        # Remove the temporary directory after each test
        shutil.rmtree(self.test_dir)

    def test_resolve_data_root_directory(self):
        """Test that resolve_data_root_directory finds the correct user's data root."""
        with patch("getpass.getuser", return_value="default_user"):
            self.project_service.resolve_data_root_directory()
            self.assertEqual(self.project_service._active_data_root, self.test_dir)

    def test_resolve_data_root_unknown_user(self):
        """Test that unknown user gets None active data root."""
        with patch("getpass.getuser", return_value="unknown_user"):
            self.project_service.resolve_data_root_directory()
            self.assertIsNone(self.project_service._active_data_root)

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
        file_entry.id = key
        retrieved_entry = self.project_service.get_file_entry(key)
        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.id, key)

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
        # Test for 16 Hz input frequency (default from setUp)
        self.assertEqual(self.project_service.get_step_time_ms(), 63)

        # Test for 10 Hz input frequency (should return 100)
        self.project_config.input_settings.input_frequency = 10
        self.assertEqual(self.project_service.get_step_time_ms(), 100)

        # Test for 1 Hz input frequency (should return 1000)
        self.project_config.input_settings.input_frequency = 1
        self.assertEqual(self.project_service.get_step_time_ms(), 1000)

        # Test for 25 Hz input frequency (should return 40)
        self.project_config.input_settings.input_frequency = 25
        self.assertEqual(self.project_service.get_step_time_ms(), 40)

    def test_get_reviewers(self):
        """Test that get_reviewers builds dict from users list."""
        reviewers = self.project_service.get_reviewers()
        self.assertIn("default_user", reviewers)
        self.assertEqual(reviewers["default_user"]["alias"], "DE")

    def test_update_user_data_root_existing_user(self):
        """Test updating data root for an existing user."""
        new_path = tempfile.mkdtemp()
        try:
            with patch("getpass.getuser", return_value="default_user"):
                self.project_service.update_user_data_root(new_path)
                user = self.project_config.get_user_by_username("default_user")
                self.assertEqual(user.data_root, new_path)
                self.assertEqual(self.project_service._active_data_root, new_path)
        finally:
            shutil.rmtree(new_path)

    def test_update_user_data_root_new_user(self):
        """Test updating data root creates a new user entry if not found."""
        new_path = tempfile.mkdtemp()
        try:
            with patch("getpass.getuser", return_value="new_user"):
                self.project_service.update_user_data_root(new_path)
                user = self.project_config.get_user_by_username("new_user")
                self.assertIsNotNone(user)
                self.assertEqual(user.data_root, new_path)
        finally:
            shutil.rmtree(new_path)

if __name__ == '__main__':
    unittest.main()
