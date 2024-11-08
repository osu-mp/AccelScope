import json
import logging
from models.directory_entry import DirectoryEntry
from models.input_settings import InputSettings
from models.label_display import LabelDisplay
from models.output_settings import OutputSettings


class ProjectConfig:
    """
    High level structure of the project config. Contains a user defined directory structure
    of dirs to organize the input CSVs. Each FileEntry contains a unique ID so that the same
    file can be listed multiple times in the same project, with different labels attached to each file.
    For example, the same day of activity could contain kill behavior and walking behavior (via trail-cam)
    and have annotations for each.
    Additionally, it supports user-specific `data_root_directory` paths.
    """
    def __init__(self, proj_name, data_root_directory=None, entries=None, label_display=None,
                 output_settings=None, input_settings=None):
        """
        :param proj_name: The project name.
        :param data_root_directory: Dictionary of {user -> path} mappings, or a single path for legacy support.
        :param entries: List of directory entries for the project.
        :param label_display: List of label display settings.
        :param output_settings: Config for generating output data.
        :param input_settings: Config for reading input data.
        """
        self.proj_name = proj_name
        self.data_root_directory = data_root_directory or {"default": None}
        self.entries = entries or []
        self.label_display = label_display or []
        self.output_settings = output_settings or OutputSettings()
        self.input_settings = input_settings or InputSettings()  # Initialize with a default InputSettings instance

    def to_dict(self):
        """Convert the project config into a dictionary format."""
        return {
            "proj_name": self.proj_name,
            "data_root_directory": self.data_root_directory,
            "entries": [entry.to_dict() for entry in self.entries],
            "label_display": [display.to_dict() for display in self.label_display],
            "output_settings": self.output_settings.to_dict(),
            "input_settings": self.input_settings.to_dict()  # Add input settings to output dict
        }

    @staticmethod
    def from_dict(data):
        """Load the project config from a dictionary."""
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        label_display = [LabelDisplay.from_dict(display) for display in data.get("label_display", [])]
        output_settings = OutputSettings.from_dict(data.get("output_settings", {}))

        data_root_directory = data.get("data_root_directory", {"default": None})

        input_settings_data = data.get("input_settings", {})
        input_settings = InputSettings.from_dict(input_settings_data)

        return ProjectConfig(
            proj_name=data['proj_name'],
            data_root_directory=data_root_directory,
            entries=entries,
            label_display=label_display,
            output_settings=output_settings,
            input_settings=input_settings
        )

    @staticmethod
    def from_file(file_path):
        """Load ProjectConfig from a given JSON file path."""
        with open(file_path, 'r') as file:
            data = json.load(file)
            return ProjectConfig.from_dict(data)

    def add_user_path(self, username, path):
        """Add or update the data path for a specific user."""
        self.data_root_directory[username] = path
        logging.info(f"Added/Updated path for user '{username}' with path '{path}'")

    def remove_user_path(self, username):
        """Remove the path associated with a specific user."""
        if username in self.data_root_directory:
            del self.data_root_directory[username]
            logging.info(f"Removed path for user '{username}'")

    def get_user_path(self, username):
        """Get the data path for a given user, fallback to default if available."""
        return self.data_root_directory.get(username, self.data_root_directory.get("default", None))
