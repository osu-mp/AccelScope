import json
import logging
from models.directory_entry import DirectoryEntry
from models.data_display import DataDisplay
from models.label_display import LabelDisplay
from models.output_settings import OutputSettings

class ProjectConfig:
    """
    High level structure of the project config. Contains a user defined directory structure
    of dirs to organize the input CSVs. Each FileEntry contains a unique ID so that the same
    file can be listed multiple times in the same project, with different labels attached to each file.
    For example, the same day of activity could contain kill behavior and walking behavior (via trail-cam)
    and have annotations for each.
    """
    def __init__(self, proj_name, data_root_directory=None, entries=None, data_display=None, label_display=None,
                 output_settings=None):
        self.proj_name = proj_name
        self.data_root_directory = data_root_directory
        self.entries = entries or []
        self.data_display = data_display or []
        self.label_display = label_display or []
        self.output_settings = output_settings or OutputSettings()
    def to_dict(self):
        return {
            "proj_name": self.proj_name,
            "data_root_directory": self.data_root_directory,
            "entries": [entry.to_dict() for entry in self.entries],
            "data_display": [display.to_dict() for display in self.data_display],
            "label_display": [display.to_dict() for display in self.label_display],
            "output_settings": self.output_settings.to_dict()
        }

    @staticmethod
    def from_dict(data):
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        data_display = [DataDisplay.from_dict(display) for display in data.get("data_display", [])]
        label_display = [LabelDisplay.from_dict(display) for display in data.get("label_display", [])]
        output_settings = OutputSettings.from_dict(data.get("output_settings", {}))

        return ProjectConfig(
            proj_name=data['proj_name'],
            data_root_directory=data['data_root_directory'],
            entries=entries,
            data_display=data_display,
            label_display=label_display,
            output_settings=output_settings
        )

    @staticmethod
    def from_file(file_path):
        """Load ProjectConfig from a given JSON file path."""
        with open(file_path, 'r') as file:
            data = json.load(file)
            return ProjectConfig.from_dict(data)
#
    def find_directory_by_path(self, path):
        logging.debug(f"Finding directory by path: {path}")

        # If the path is empty or root, return the top-level entries
        if not path or path == "/":
            return self.entries

        # Split the path and traverse the directory structure
        segments = path.strip('/').split('/')  # Remove leading/trailing slashes and split into segments
        current_entries = self.entries

        # Traverse the path from the top-level entries
        for segment in segments:
            found = False
            for entry in current_entries:
                if isinstance(entry, DirectoryEntry) and entry.name == segment:
                    current_entries = entry.entries
                    found = True
                    break
            if not found:
                logging.error(f"Directory '{segment}' not found in path.")
                return None  # If no matching directory is found, return None

        # Return the final DirectoryEntry object instead of the list of entries
        return entry if isinstance(entry, DirectoryEntry) else None
