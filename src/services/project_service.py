import json
import logging
import os
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
            return self.current_project_config.find_file_by_id(file_id)
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
            return self.current_project_config.get_label_display(behavior)
        logging.warning(f"No active project configuration loaded.")
        return None

    def add_directory(self, parent_full_path, new_dir_name):
        """Add a new directory entry to the specified parent directory path in the project configuration."""
        if self.current_project_config:
            self.current_project_config.add_directory(parent_full_path, new_dir_name)
            logging.info(f"Added new directory '{new_dir_name}' under '{parent_full_path}'.")
        else:
            logging.warning("No active project configuration loaded.")

    def add_file(self, parent_full_path, file_entry):
        """Add a new file entry to the specified parent directory path in the project configuration."""
        if self.current_project_config:
            self.current_project_config.add_file(parent_full_path, file_entry)
            logging.info(f"Added new file '{file_entry.path}' under '{parent_full_path}'.")
        else:
            logging.warning("No active project configuration loaded.")

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
