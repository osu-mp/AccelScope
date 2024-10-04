import json
import logging
import os
import uuid
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.project_config import ProjectConfig


class ProjectService:
    """Service to manage a project configuration."""

    def __init__(self, project_path=None):
        self.current_project_path = project_path
        self.current_project_config = None
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

    # def prompt_for_project(self, parent):
    #     """Prompt the user to load or create a new project (e.g., via a file dialog)."""
    #     response = messagebox.askyesno("Open Project", "Do you want to open an existing project?")
    #     if response:
    #         project_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Open Project File")
    #         if project_path:
    #             self.load_project(project_path)
    #     else:
    #         # Create a new project using NewProjectDialog
    #         new_project_dialog = NewProjectDialog(parent=parent)
    #         new_project_dialog.grab_set()
    #         parent.wait_window(new_project_dialog)
    #
    #         # Load the new project if one was created
    #         project_path = new_project_dialog.location_entry.get()
    #         if project_path:
    #             self.load_project(project_path)

    def get_file_entry(self, file_id):
        """Retrieve a file entry by file ID from the current project configuration."""
        if self.current_project_config:
            return self.find_file_by_id(file_id)
        logging.warning(f"No active project configuration loaded.")
        return None

    def update_labels(self, file_id, labels):
        """Update the labels for a specific file entry by file ID and save the changes."""
        if self.current_project_config:
            file_entry = self.current_project_config.find_file_by_id(file_id)
            if file_entry:
                file_entry.set_labels(labels)
                self.save_project()
                logging.info(f"Updated labels for file with ID {file_id}.")

            else:
                logging.error(f"File with ID {file_id} not found.")
        else:
            logging.warning(f"No active project configuration loaded.")

    def get_file_path(self, file_entry):
        """Get the full file path for the given file entry."""
        if self.current_project_config:
            return os.path.join(self.current_project_config.data_root_directory, file_entry.path)
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
        unique_id = self._generate_unique_file_id()
        file_entry.file_id = unique_id

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

        # Create a new ProjectConfig instance
        project_config = ProjectConfig(
            proj_name=proj_name,
            data_root_directory=data_root,
            entries=[],
            data_display=[],
            label_display=[]
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

    def _generate_unique_file_id(self):
        """Generate a unique file ID that does not already exist in the project configuration."""
        while True:
            # Generate a simple unique ID
            unique_id = str(uuid.uuid4())[:8]  # Use the first 8 characters of UUID for simplicity

            # Check if the generated ID already exists
            if not self._is_file_id_exists(unique_id):
                return unique_id

    def _is_file_id_exists(self, file_id):
        """Check if the given file ID already exists in the current project configuration."""
        if not self.current_project_config:
            return False

        return self.find_file_by_id(file_id) is not None

    def find_file_by_id(self, file_id):
        """Retrieve a file entry by file ID from the current project configuration."""
        if not self.current_project_config:
            logging.warning("No active project configuration loaded.")
            return None

        return self._search_file_by_id(self.current_project_config.entries, file_id)

    def _search_file_by_id(self, entries, file_id):
        """Recursively searches the directory structure to find a file by its id."""
        for entry in entries:
            if isinstance(entry, FileEntry) and entry.file_id == file_id:
                return entry
            elif isinstance(entry, DirectoryEntry):
                found = self._search_file_by_id(entry.entries, file_id)
                if found:
                    return found
        return None
