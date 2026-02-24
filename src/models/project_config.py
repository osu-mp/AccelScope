import json
import logging
from models.directory_entry import DirectoryEntry
from models.input_settings import InputSettings
from models.label_display import LabelDisplay
from models.output_settings import OutputSettings
from models.user_config import UserConfig


# Defaults for new config fields
DEFAULT_Y_RANGE = [-5, 5]
DEFAULT_INDIVIDUAL_ID_REGEX = r"(?P<individual>[^_]+)_"
DEFAULT_PLOT_TITLE_FORMAT = "{individual}    {filename_stem}"


class ProjectConfig:
    """
    High level structure of the project config. Contains a user defined directory structure
    of dirs to organize the input CSVs. Each FileEntry contains a unique ID so that the same
    file can be listed multiple times in the same project, with different labels attached to each file.
    Additionally, it supports per-user configuration via an explicit `users` list.
    """
    def __init__(self, proj_name, users=None, entries=None, label_display=None,
                 output_settings=None, input_settings=None,
                 y_range=None, individual_id_regex=None, plot_title_format=None,
                 verification_threshold=None):
        self.proj_name = proj_name
        self.users = users or []
        self.entries = entries or []
        self.label_display = label_display or []
        self.output_settings = output_settings or OutputSettings()
        self.input_settings = input_settings or InputSettings()
        self.y_range = y_range if y_range is not None else list(DEFAULT_Y_RANGE)
        self.individual_id_regex = individual_id_regex if individual_id_regex is not None else DEFAULT_INDIVIDUAL_ID_REGEX
        self.plot_title_format = plot_title_format if plot_title_format is not None else DEFAULT_PLOT_TITLE_FORMAT
        self.verification_threshold = verification_threshold if verification_threshold is not None else 1.0

    def to_dict(self):
        """Convert the project config into a dictionary format."""
        return {
            "proj_name": self.proj_name,
            "users": [u.to_dict() for u in self.users],
            "entries": [entry.to_dict() for entry in self.entries],
            "label_display": [display.to_dict() for display in self.label_display],
            "output_settings": self.output_settings.to_dict(),
            "input_settings": self.input_settings.to_dict(),
            "y_range": self.y_range,
            "individual_id_regex": self.individual_id_regex,
            "plot_title_format": self.plot_title_format,
            "verification_threshold": self.verification_threshold,
        }

    @staticmethod
    def from_dict(data):
        """Load the project config from a dictionary."""
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        label_display = [LabelDisplay.from_dict(display) for display in data.get("label_display", [])]
        output_settings = OutputSettings.from_dict(data.get("output_settings", {}))

        users = [UserConfig.from_dict(u) for u in data.get("users", [])]

        input_settings_data = data.get("input_settings", {})
        input_settings = InputSettings.from_dict(input_settings_data)

        config = ProjectConfig(
            proj_name=data['proj_name'],
            users=users,
            entries=entries,
            label_display=label_display,
            output_settings=output_settings,
            input_settings=input_settings,
            y_range=data.get("y_range"),
            individual_id_regex=data.get("individual_id_regex"),
            plot_title_format=data.get("plot_title_format"),
            verification_threshold=data.get("verification_threshold"),
        )
        return config

    @staticmethod
    def from_file(file_path):
        """Load ProjectConfig from a given JSON file path."""
        with open(file_path, 'r') as file:
            data = json.load(file)
            return ProjectConfig.from_dict(data)

    def get_user_by_username(self, username):
        """Find a UserConfig by username, or None if not found."""
        for u in self.users:
            if u.username == username:
                return u
        return None
