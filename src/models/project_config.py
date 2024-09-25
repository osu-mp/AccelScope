import logging
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.data_display import DataDisplay
from models.label_display import LabelDisplay


class ProjectConfig:
    """
    High level structure of the project config. Contains a user defined directory structure
    of dirs to organize the input CSVs. Each FileEntry contains a unique ID so that the same
    file can be listed multiple times in the same project, with different labels attached to each file.
    For example, the same day of activity could contain kill behavior and walking behavior (via trail-cam)
    and have annotations for each.
    """
    def __init__(self, proj_name, data_root_directory, entries=None, data_display=None, label_display=None):
        self.proj_name = proj_name
        self.data_root_directory = data_root_directory
        self.entries = entries or []
        self.data_display = data_display or []
        self.label_display = label_display or []

    def to_dict(self):
        """Convert ProjectConfig instance back to a dictionary."""
        return {
            'proj_name': self.proj_name,
            'data_root_directory': self.data_root_directory,
            'entries': [entry.to_dict() for entry in self.entries],
            'data_display': [dd.to_dict() for dd in self.data_display],
            'label_display': [ld.to_dict() for ld in self.label_display]
        }

    @staticmethod
    def from_dict(data):
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        data_display = [DataDisplay.from_dict(dd) for dd in data.get("data_display", [])]
        label_display = [LabelDisplay.from_dict(ld) for ld in data.get("label_display", [])]
        return ProjectConfig(
            proj_name=data["proj_name"],
            data_root_directory=data["data_root_directory"],
            entries=entries,
            data_display=data_display,
            label_display=label_display
        )

    def add_directory(self, parent_full_path, new_dir_name):
        # Find the parent directory using the full path
        logging.debug(f"Adding directory {new_dir_name} under path {parent_full_path}")
        parent_dir = self.find_directory_by_path(parent_full_path)
        if parent_dir:
            new_dir = DirectoryEntry(new_dir_name)
            parent_dir.entries.append(new_dir)  # Append to the entries of the DirectoryEntry
            logging.debug(f"Added directory {new_dir_name} under {parent_dir.name}")
        else:
            logging.error(f"Parent directory not found for path: {parent_full_path}")

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

    def add_file(self, parent_full_path, file_entry):
        logging.debug(f"Adding file {file_entry.path} under path {parent_full_path}")
        parent_dir = self.find_directory_by_path(parent_full_path)

        # TODO: ensure file_id of file_entry is a unique ID

        if parent_dir:
            parent_dir.append(file_entry)
            logging.debug(f"Added file {file_entry.path} under {parent_dir}")
        else:
            logging.error(f"Parent directory not found for path: {parent_full_path}")

    def find_file_by_id(self, file_id):
        """Recursively searches the directory structure to find a file by its id."""
        logging.debug(f"Finding file by id: {file_id}")
        return self._search_file_by_id(self.entries, file_id)

    def _search_file_by_id(self, entries, file_id):
        for entry in entries:
            if isinstance(entry, FileEntry) and entry.file_id == file_id:
                logging.debug(f"Found file: {entry.path}")
                return entry
            elif isinstance(entry, DirectoryEntry):
                found = self._search_file_by_id(entry.entries, file_id)
                if found:
                    return found
        logging.debug(f"File with id {file_id} not found.")
        return None

    def get_label_display(self, behavior):
        """Retrieve the LabelDisplay settings for the given behavior."""
        for display in self.label_display:
            if display.display_name == behavior:
                return display
        return None  # Return None if no matching behavior is found