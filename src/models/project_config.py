import json
import logging
from models.directory_entry import DirectoryEntry
from models.input_settings import InputSettings
from models.label_display import LabelDisplay
from models.output_settings import OutputSettings


# Defaults for new config fields
DEFAULT_Y_RANGE = [-5, 5]
DEFAULT_INDIVIDUAL_ID_REGEX = r"(?P<individual>[^_]+)_"
DEFAULT_PLOT_TITLE_FORMAT = "{individual}    {filename_stem}"


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
                 output_settings=None, input_settings=None,
                 y_range=None, individual_id_regex=None, plot_title_format=None,
                 reviewers=None):
        """
        :param proj_name: The project name.
        :param data_root_directory: Dictionary of {user -> path} mappings, or a single path for legacy support.
        :param entries: List of directory entries for the project.
        :param label_display: List of label display settings.
        :param output_settings: Config for generating output data.
        :param input_settings: Config for reading input data.
        :param y_range: Fixed Y-axis range for the viewer, e.g. [-5, 5].
        :param individual_id_regex: Regex with named group 'individual' applied to relative file path.
        :param plot_title_format: Template string using {individual} and {filename_stem}.
        :param reviewers: Dict of {username: {"alias": "XX"}} for multi-reviewer verification.
        """
        self.proj_name = proj_name
        self.data_root_directory = data_root_directory or {"default": None}
        self.entries = entries or []
        self.label_display = label_display or []
        self.output_settings = output_settings or OutputSettings()
        self.input_settings = input_settings or InputSettings()
        self.y_range = y_range if y_range is not None else list(DEFAULT_Y_RANGE)
        self.individual_id_regex = individual_id_regex if individual_id_regex is not None else DEFAULT_INDIVIDUAL_ID_REGEX
        self.plot_title_format = plot_title_format if plot_title_format is not None else DEFAULT_PLOT_TITLE_FORMAT
        self.reviewers = reviewers if reviewers is not None else {}

    def to_dict(self):
        """Convert the project config into a dictionary format."""
        result = {
            "proj_name": self.proj_name,
            "data_root_directory": self.data_root_directory,
            "entries": [entry.to_dict() for entry in self.entries],
            "label_display": [display.to_dict() for display in self.label_display],
            "output_settings": self.output_settings.to_dict(),
            "input_settings": self.input_settings.to_dict(),
            "y_range": self.y_range,
            "individual_id_regex": self.individual_id_regex,
            "plot_title_format": self.plot_title_format,
        }
        if self.reviewers:
            result["reviewers"] = self.reviewers
        return result

    @staticmethod
    def from_dict(data):
        """Load the project config from a dictionary."""
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        label_display = [LabelDisplay.from_dict(display) for display in data.get("label_display", [])]
        output_settings = OutputSettings.from_dict(data.get("output_settings", {}))

        data_root_directory = data.get("data_root_directory", {"default": None})

        input_settings_data = data.get("input_settings", {})
        input_settings = InputSettings.from_dict(input_settings_data)

        config = ProjectConfig(
            proj_name=data['proj_name'],
            data_root_directory=data_root_directory,
            entries=entries,
            label_display=label_display,
            output_settings=output_settings,
            input_settings=input_settings,
            y_range=data.get("y_range"),
            individual_id_regex=data.get("individual_id_regex"),
            plot_title_format=data.get("plot_title_format"),
            reviewers=data.get("reviewers"),
        )
        # Auto-populate reviewers from data_root_directory keys for old configs
        config.populate_reviewers_from_data_root()
        return config

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

    def populate_reviewers_from_data_root(self):
        """Auto-add reviewer entries from data_root_directory keys (excluding 'default' and 'active')."""
        excluded = {"default", "active"}
        for key in self.data_root_directory:
            if key not in excluded and key not in self.reviewers:
                self.reviewers[key] = {"alias": self._generate_alias(key)}

    @staticmethod
    def _generate_alias(username):
        """Generate a 2-character uppercase alias from a username."""
        return username[:2].upper()
