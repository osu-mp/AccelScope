import getpass
import json
import logging
import math
import os
import uuid
from models.data_display import DataDisplay
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.input_settings import InputSettings
from models.label_display import LabelDisplay
from models.project_config import ProjectConfig


class ProjectService:
    """Service to manage a project configuration."""

    def __init__(self, project_path=None):
        self.current_project_path = project_path
        self.current_project_config = None
        self.input_freq = 16        # TODO move to project config
        if project_path:
            self.load_project(project_path)

    def load_project(self, project_path):
        """Load the project configuration from the specified file path."""
        try:
            if os.path.exists(project_path):
                with open(project_path, 'r') as file:
                    project_data = json.load(file)
                    self.current_project_config = ProjectConfig.from_dict(project_data)
                    self.current_project_path = project_path
                    logging.info(f"Loaded project from {project_path}")
            else:
                logging.error(f"Project file '{project_path}' does not exist.")
        except json.JSONDecodeError as e:
            logging.error(f"Error loading project configuration from {project_path}: {e}")
            self.current_project_config = None

        # Validate and resolve the user-specific data root directory
        if self.current_project_config:
            self.resolve_data_root_directory()

    def resolve_data_root_directory(self):
        """Resolve the correct data root directory based on the current user."""
        if not self.current_project_config:
            logging.error("No project config loaded")
            return

        # Get the current OS username
        username = getpass.getuser()

        # Check if a path is specified for this user, else use the default path
        data_root = self.current_project_config.data_root_directory.get(username)

        if not data_root:
            # If user-specific path is not found, fallback to the default
            data_root = self.current_project_config.data_root_directory.get("default")

        if data_root and os.path.exists(data_root):
            logging.info(f"Using data root directory for user '{username}': {data_root}")
            self.current_project_config.data_root_directory["active"] = data_root
        else:
            logging.error(f"No valid data root directory found for user '{username}' and no default. Please update the project config.")

    def save_project(self):
        """Save the current project configuration to the specified file path."""
        if not self.current_project_path:
            logging.error("Unable to save project config, no current_project_path set")
            return

        if self.current_project_config:
            try:
                with open(self.current_project_path, 'w') as file:
                    json.dump(self.current_project_config.to_dict(), file, indent=4)
                    logging.info(f"Saved project configuration to {self.current_project_path}")
            except Exception as e:
                logging.error(f"Failed to save project configuration: {e}")
        else:
            logging.error("No active project configuration to save.")

    def get_output_settings(self):
        """Return the current output settings from the project configuration."""
        if self.current_project_config:
            return self.current_project_config.output_settings
        logging.warning("No active project configuration loaded.")
        return None

    def update_output_settings(self, new_output_settings):
        """Update and save the output settings."""
        if self.current_project_config:
            self.current_project_config.output_settings = new_output_settings
            self.save_project()
        else:
            logging.warning("No active project configuration loaded.")

    def get_file_entry(self, id):
        """Retrieve a file entry by file ID from the current project configuration."""
        if self.current_project_config:
            return self.find_file_by_id(id)
        logging.warning(f"No active project configuration loaded.")
        return None

    def update_labels(self, id, labels):
        """Update the labels for a specific file entry by file ID and save the changes."""
        if self.current_project_config:
            file_entry = self.find_file_by_id(id)
            if file_entry:
                file_entry.set_labels(labels)
                self.save_project()
            else:
                logging.error(f"File with ID {id} not found.")
        else:
            logging.warning(f"No active project configuration loaded.")

    def get_file_path(self, file_entry):
        """Get the full file path for the given file entry."""
        if self.current_project_config:
            # Get the active data root directory
            active_root = self.current_project_config.data_root_directory.get("active")

            if not active_root:
                logging.error("Active data root directory not set. Please resolve data root directory.")
                return None

            return os.path.join(active_root, file_entry.path)

        logging.warning(f"No active project configuration loaded.")
        return None

    def get_label_display(self, behavior):
        """Retrieve the label display settings for a given behavior from the project configuration."""
        if self.current_project_config:
            for display in self.current_project_config.label_display:
                if display.display_name == behavior:
                    return display
            return None  # Return None if no matching behavior is found
        logging.warning(f"No active project configuration loaded.")
        return None

    def find_directory_by_path(self, path):
        """Find a directory by its path within the current project configuration."""
        if not self.current_project_config:
            logging.error("No active project configuration loaded.")
            return None, False

        logging.debug(f"Finding directory by path: {path}")

        # If the path is empty or matches the project name, return the root entries
        if not path or path == self.current_project_config.proj_name:
            return self.current_project_config.entries, True

        # Split the path and traverse the directory structure
        segments = path.strip('/').split('/')  # Remove leading/trailing slashes and split into segments
        current_entries = self.current_project_config.entries

        # Traverse the path from the top-level entries
        for segment in segments:
            found = False
            for entry in current_entries:
                if isinstance(entry, DirectoryEntry) and entry.name == segment:
                    current_entries = entry.entries
                    found = True
                    break
            if not found:
                logging.error(f"Directory '{segment}' not found in path: {path}.")
                return None, False  # If no matching directory is found, return None

        # Return the final DirectoryEntry object
        return entry if isinstance(entry, DirectoryEntry) else None, False

    def add_directory(self, parent_full_path, new_dir_name):
        """Add a new directory entry to the specified parent directory path in the project configuration."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return

        # Use the new find_directory_by_path to get the parent directory
        parent_dir, is_root = self.find_directory_by_path(parent_full_path)

        if parent_dir is not None:
            new_dir = DirectoryEntry(new_dir_name)

            if is_root:
                # If it's the root, add to the root entries list directly
                self.current_project_config.entries.append(new_dir)
            else:
                # Otherwise, add to the found DirectoryEntry's entries list
                parent_dir.entries.append(new_dir)

            logging.info(f"Added new directory '{new_dir_name}' under '{parent_full_path}'.")

            # Save the project configuration to persist changes
            self.save_project()
        else:
            raise ValueError(f"Parent directory '{parent_full_path}' not found.")

    def add_file(self, parent_full_path, file_entry):
        """Add a new file entry to the specified parent directory path in the project configuration."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return

        # Generate a unique ID for the file entry
        unique_id = self._generate_unique_id()
        file_entry.id = unique_id

        # Add the file to the specified parent directory path
        parent_dir, is_root = self.find_directory_by_path(parent_full_path)

        if parent_dir is not None:
            # Add the file entry to the directory
            parent_dir.entries.append(file_entry)
            logging.info(f"Added new file '{file_entry.path}' under '{parent_full_path}' with ID '{unique_id}'.")

            # Save the project configuration to persist changes
            self.save_project()
        else:
            raise ValueError(f"Parent directory '{parent_full_path}' not found.")

    def get_project_config(self):
        """Return the current project configuration."""
        if self.current_project_config:
            return self.current_project_config
        else:
            logging.warning("No active project configuration loaded.")
            return None

    def create_project(self, proj_name, location, data_root):
        """
        Handles project creation including validation and saving the config.
        """
        # Validate inputs
        if not proj_name or not location or not data_root:
            raise ValueError("Project name, location, and data root are required.")

        if os.path.exists(location):
            raise FileExistsError(f"The file {location} already exists.")

        # Create default data_display and label_display configurations as instances of their respective classes
        # TODO: move this elsewhere
        default_data_display = [
            DataDisplay(
                input_name="Acc X [g]",
                display_name="X-axis",
                color="red",
                alpha=0.6,
                output_name="Acc X [g]"
            ),
            DataDisplay(
                input_name="Acc Y [g]",
                display_name="Y-axis",
                color="black",
                alpha=0.5,
                output_name="Acc Y [g]"
            ),
            DataDisplay(
                input_name="Acc Z [g]",
                display_name="Z-axis",
                color="blue",
                alpha=0.7,
                output_name="Acc Z [g]"
            )
        ]

        default_label_display = [
            LabelDisplay(
                display_name="Stalk",
                color="green",
                alpha=0.2,
                output_value="STALK"
            ),
            LabelDisplay(
                display_name="Kill Phase 1",
                color="purple",
                alpha=0.2,
                output_value="KILL"
            ),
            LabelDisplay(
                display_name="Kill Phase 2",
                color="orange",
                alpha=0.2,
                output_value="KILL_PHASE_2"
            ),
            LabelDisplay(
                display_name="Feed",
                color="blue",
                alpha=0.2,
                output_value="FEED"
            ),
            LabelDisplay(
                display_name="Walk",
                color="red",
                alpha=0.2,
                output_value="WALK"
            )
        ]

        # Create a new ProjectConfig instance with default data_display and label_display
        project_config = ProjectConfig(
            proj_name=proj_name,
            data_root_directory=data_root,
            entries=[],
            data_display=default_data_display,
            label_display=default_label_display
        )

        # Save the project configuration as a JSON file
        self._save_project_config(location, project_config)

    @staticmethod
    def _save_project_config(location, project_config: ProjectConfig):
        """
        Internal method to save the project configuration to the specified location.
        """
        try:
            with open(location, 'w') as json_file:
                json.dump(project_config.to_dict(), json_file, indent=4)
            logging.info(f"Project created and saved to {location}")
        except Exception as e:
            logging.error(f"Failed to save project config to {location}: {e}")
            raise

    def _generate_unique_id(self):
        """Generate a unique file ID that does not already exist in the project configuration."""
        while True:
            # Generate a simple unique ID
            unique_id = str(uuid.uuid4())[:8]  # Use the first 8 characters of UUID for simplicity

            # Check if the generated ID already exists
            if not self._does_id_exist(unique_id):
                return unique_id

    def _does_id_exist(self, id):
        """Check if the given file ID already exists in the current project configuration."""
        if not self.current_project_config:
            return False

        return self.find_file_by_id(id) is not None

    def find_file_by_id(self, id):
        """Retrieve a file entry by file ID from the current project configuration."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        return self._search_file_by_id(self.current_project_config.entries, id)

    def _search_file_by_id(self, entries, id):
        """Recursively searches the directory structure to find a file by its id."""
        for entry in entries:
            if isinstance(entry, FileEntry) and entry.id == id:
                return entry
            elif isinstance(entry, DirectoryEntry):
                found = self._search_file_by_id(entry.entries, id)
                if found:
                    return found
        return None

    def get_project_name(self):
        """Return current project name (alert if not found/empty)"""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        proj_name = self.current_project_config.proj_name
        if not proj_name:
            logging.warning("Current project has no name or name is empty")
        return proj_name

    def get_project_root_dir(self):
        """Return current project root directory (alert if not found/empty)"""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        root_dir = self.current_project_config.data_root_directory
        if not root_dir:
            logging.warning("Current project has no root directory")
        return root_dir

    def get_entries(self):
        """Return current project entries (alert if not found/empty)"""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        entries = self.current_project_config.entries
        if not entries:
            logging.warning("Current project has no entries")
        return entries

    def get_plot_title(self, file_entry):
        """
        Return the plot title for the given file_entry
        This currently uses the file path to determine, but could be customized later (possibly added to project config)
        E.g. file_full_path = "C:/data_root/F202_27905_010518_072219/MotionData_27905/2018/06 Jun/09/2018-06-09.csv"
        title = F202 -- 2018-06-09
        :param file_entry:
        :return:
        """
        file_full_path = self.get_file_path(file_entry)
        # Extract the fifth parent directory as the coug_id
        coug_collar = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_full_path))))))
        coug_id = coug_collar.split("_")[0]
        # Extract the filename without extension as the date
        date = os.path.splitext(os.path.basename(file_full_path))[0]

        return f"{coug_id}    {date}"

    def get_step_time_ms(self):
        """
        For the active project config, return the number of milliseconds one step represents
        E.g. for 16 Hz data, this is 1000 / 16 ~ 63 ms
        :return:
        """
        return math.ceil(1000 / self.input_freq)

    def delete_file_by_id(self, id):
        """Delete a file entry from the project configuration by file ID."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return

        # Find the file entry by its ID
        file_entry = self.find_file_by_id(id)

        if file_entry:
            # Find the parent directory of the file entry
            parent_entry = self.find_parent_directory_of_file(id, self.current_project_config.entries)

            if parent_entry and isinstance(parent_entry, DirectoryEntry):
                # Remove the file entry from the parent directory
                parent_entry.entries.remove(file_entry)
                self.save_project()  # Persist the changes
                logging.info(f"Deleted file with ID '{id}' from project configuration.")
            else:
                logging.warning(f"Parent directory for file with ID '{id}' not found.")
        else:
            logging.warning(f"File with ID '{id}' not found.")

    def find_parent_directory_of_file(self, id, entries):
        """Recursively find the parent directory of a file entry by file ID."""
        for entry in entries:
            if isinstance(entry, FileEntry) and entry.id == id:
                return None  # If this is the file entry, return None (it has no parent)
            elif isinstance(entry, DirectoryEntry):
                if any(isinstance(sub_entry, FileEntry) and sub_entry.id == id for sub_entry in
                       entry.entries):
                    return entry  # Return the parent directory if the file is found here
                # Recursively search in sub-directories
                parent = self.find_parent_directory_of_file(id, entry.entries)
                if parent:
                    return parent
        return None

    def update_file_comment(self, id, comment):
        """Update the comment for a specific file entry by file ID."""
        if self.current_project_config:
            file_entry = self.find_file_by_id(id)
            if file_entry:
                file_entry.comment = comment
                self.save_project()
            else:
                logging.error(f"File with ID {id} not found.")
        else:
            logging.warning(f"No active project configuration loaded.")

    @staticmethod
    def get_os_username():
        """Return the current OS username (used to find data_root per user)."""
        try:
            return os.getlogin()
        except Exception:
            return getpass.getuser()  # Fallback method

    def get_user_data_path(self):
        """Return the correct data path based on the current user."""
        username = self.get_os_username()
        data_paths = self.current_project_config.data_root_directory

        if username in data_paths:
            return data_paths[username]
        elif 'default' in data_paths:
            return data_paths['default']
        else:
            raise FileNotFoundError(f"No path found for user {username} and no default path available.")

    def get_input_settings(self) -> InputSettings:
        """Return the input settings from the project configuration."""
        return self.project_config.input_settings if self.project_config else None