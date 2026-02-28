import getpass
import json
import logging
import math
import os
import tempfile
import re
import uuid
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.input_settings import InputSettings
from models.label_display import LabelDisplay
from models.project_config import ProjectConfig
from models.user_config import UserConfig


class ProjectService:
    """Service to manage a project configuration."""

    def __init__(self, project_path=None):
        self.current_project_path = project_path
        self.current_project_config = None
        self._active_data_root = None
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

        username = getpass.getuser()
        user_config = self.current_project_config.get_user_by_username(username)

        if user_config and user_config.data_root and os.path.exists(user_config.data_root):
            logging.info(f"Using data root directory for user '{username}': {user_config.data_root}")
            self._active_data_root = user_config.data_root
        else:
            logging.error(f"No valid data root directory found for user '{username}'. Please update the project config.")
            self._active_data_root = None

    def is_data_root_valid(self):
        """Return True if the active data root exists and is a directory."""
        return self._active_data_root is not None and os.path.isdir(self._active_data_root)

    def update_user_data_root(self, new_path):
        """Update the data root for the current OS user, re-resolve, and save."""
        if not self.current_project_config:
            logging.error("No project config loaded, cannot update data root.")
            return
        username = getpass.getuser()
        user_config = self.current_project_config.get_user_by_username(username)
        if user_config:
            user_config.data_root = new_path
        else:
            self.current_project_config.users.append(
                UserConfig(username=username, data_root=new_path)
            )
        self.resolve_data_root_directory()
        self.save_project()

    def save_project(self):
        """Save the current project configuration to the specified file path.

        Uses atomic write (temp file + rename) to prevent corruption if the
        process crashes mid-write.
        """
        if not self.current_project_path:
            logging.error("Unable to save project config, no current_project_path set")
            return

        if self.current_project_config:
            try:
                dir_name = os.path.dirname(os.path.abspath(self.current_project_path))
                fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_name, text=True)
                try:
                    with os.fdopen(fd, 'w') as f:
                        json.dump(self.current_project_config.to_dict(), f, indent=4)
                    os.replace(temp_path, self.current_project_path)
                    logging.info(f"Saved project configuration to {self.current_project_path}")
                except BaseException:
                    # Clean up temp file on any failure
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
                    raise
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
            if not self._active_data_root:
                logging.error("Active data root directory not set. Please resolve data root directory.")
                return None
            return os.path.join(self._active_data_root, file_entry.path)

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
        matched_dir = None

        # Traverse the path from the top-level entries
        for segment in segments:
            found = False
            for entry in current_entries:
                if isinstance(entry, DirectoryEntry) and entry.name == segment:
                    matched_dir = entry
                    current_entries = entry.entries
                    found = True
                    break
            if not found:
                logging.error(f"Directory '{segment}' not found in path: {path}.")
                return None, False  # If no matching directory is found, return None

        # Return the final DirectoryEntry object
        return matched_dir, False

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
            if is_root:
                self.current_project_config.entries.append(file_entry)
            else:
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

    def create_project(self, proj_name, location, data_root, entries=None):
        """
        Handles project creation including validation and saving the config.
        entries: optional list of DirectoryEntry/FileEntry to pre-populate the project.
        """
        # Validate inputs
        if not proj_name or not location or not data_root:
            raise ValueError("Project name, location, and data root are required.")

        if os.path.exists(location):
            raise FileExistsError(f"The file {location} already exists.")

        username = getpass.getuser()

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

        project_config = ProjectConfig(
            proj_name=proj_name,
            users=[UserConfig(username=username, data_root=data_root)],
            entries=entries or [],
            label_display=default_label_display
        )

        # Assign unique IDs to any FileEntry objects that were pre-populated
        if entries:
            self.current_project_config = project_config
            self.current_project_path = location
            self._assign_ids_recursive(project_config.entries)

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

    def _assign_ids_recursive(self, entries):
        """Recursively assign unique IDs to all FileEntry objects that lack one."""
        for entry in entries:
            if isinstance(entry, FileEntry):
                if not entry.id:
                    entry.id = self._generate_unique_id()
            elif isinstance(entry, DirectoryEntry):
                self._assign_ids_recursive(entry.entries)

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
        """Return the active data root directory path."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        if not self._active_data_root:
            logging.warning("Current project has no active data root directory")
        return self._active_data_root

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
        Return the plot title for the given file_entry using config-driven regex and format.
        Uses individual_id_regex to extract the individual ID from the relative file path,
        and plot_title_format to build the title string.
        """
        config = self.current_project_config
        file_full_path = self.get_file_path(file_entry)
        filename_stem = os.path.splitext(os.path.basename(file_full_path))[0]

        # Extract individual ID using config regex on relative path
        individual = ""
        if config and file_entry.path:
            normalized_path = file_entry.path.replace("\\", "/")
            match = re.search(config.individual_id_regex, normalized_path)
            if match:
                try:
                    individual = match.group("individual")
                except IndexError:
                    individual = normalized_path.split("/")[0] if "/" in normalized_path else ""
            else:
                individual = normalized_path.split("/")[0] if "/" in normalized_path else ""

        # Format the title
        title_format = config.plot_title_format if config else "{individual}    {filename_stem}"
        try:
            return title_format.format(individual=individual, filename_stem=filename_stem)
        except (KeyError, ValueError) as e:
            logging.warning(f"Invalid plot title format '{title_format}': {e}")
            return f"{individual}    {filename_stem}"

    def get_step_time_ms(self):
        """
        For the active project config, return the number of milliseconds one step represents
        E.g. for 16 Hz data, this is 1000 / 16 ~ 63 ms
        :return:
        """
        if self.current_project_config and self.current_project_config.input_settings:
            freq = self.current_project_config.input_settings.input_frequency
        else:
            freq = 16
        return math.ceil(1000 / freq)

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

    def update_file_comment(self, id, username, comment):
        """Update the comment for a specific file entry by file ID and username."""
        if self.current_project_config:
            file_entry = self.find_file_by_id(id)
            if file_entry:
                file_entry.set_comment(username, comment)
                self.save_project()
            else:
                logging.error(f"File with ID {id} not found.")
        else:
            logging.warning(f"No active project configuration loaded.")

    def get_verification_color(self, verified_by):
        """Return 'red', 'yellow', or 'green' based on reviewer verification state and threshold."""
        num_verified = len(verified_by)
        if num_verified == 0:
            return "red"
        reviewers = self.get_reviewers()
        num_reviewers = len(reviewers)
        if num_reviewers == 0:
            # No reviewers configured — any verification counts as green
            return "green"
        threshold = self.current_project_config.verification_threshold if self.current_project_config else 1.0
        required = math.ceil(threshold * num_reviewers)
        if num_verified >= required:
            return "green"
        return "yellow"

    @staticmethod
    def get_os_username():
        """Return the current OS username (used to find data_root per user)."""
        try:
            return os.getlogin()
        except Exception:
            return getpass.getuser()  # Fallback method

    def get_user_data_path(self):
        """Return the resolved active data root path."""
        if self._active_data_root:
            return self._active_data_root
        raise FileNotFoundError(f"No active data root directory resolved. Please update the project config.")

    def get_input_settings(self) -> InputSettings:
        """Return the input settings from the project configuration."""
        return self.current_project_config.input_settings if self.current_project_config else None

    def get_current_reviewer(self):
        """Return the current OS username as the reviewer name."""
        return getpass.getuser()

    def get_reviewers(self):
        """Return a reviewers dict built from the users list."""
        if self.current_project_config:
            return {u.username: {"alias": u.alias} for u in self.current_project_config.users}
        return {}
