import json
import logging
import os
from models.project_config import ProjectConfig
from models.user_app_config import UserAppConfig

class UserAppConfigService:
    USER_CONFIG_FILE = "user_app_config.json"

    def __init__(self):
        self.config = self.load_from_file(self)
        self.current_project_config = None
        self.get_project_config()

    def save_to_file(self):
        """Saves the user app config to a file."""
        with open(self.USER_CONFIG_FILE, 'w') as file:
            json.dump(self.config.__dict__, file, indent=4)
            logging.debug(f"Saved app config to {self.USER_CONFIG_FILE}")


    @staticmethod
    def load_from_file(self) -> UserAppConfig:
        """Loads user app config from a file or returns a new instance if not available."""
        if os.path.exists(self.USER_CONFIG_FILE):
            with open(self.USER_CONFIG_FILE, 'r') as file:
                data = json.load(file)
                logging.debug(f"Loaded app config from {self.USER_CONFIG_FILE}")
                return UserAppConfig(**data)
        return UserAppConfig()  # Return a new instance with default values if the file does not exist

    # Update methods to keep main_gui read-only with respect to the user configuration
    def update_window_geometry(self, geometry: str):
        self.config.window_geometry = geometry
        self.save_to_file()

    def update_window_state(self, state: str):
        self.config.window_state = state
        self.save_to_file()

    def update_pane_widths(self, project_browser_width: int, viewer_width: int, info_width: int):
        self.config.project_browser_width = project_browser_width
        self.config.viewer_width = viewer_width
        self.config.info_width = info_width
        self.save_to_file()

    def get_project_config(self):
        """Returns the active ProjectConfig instance, loading it if necessary."""
        if self.current_project_config:
            return self.current_project_config

        if self.config.last_opened_project and os.path.exists(self.config.last_opened_project):
            try:
                self.current_project_config = ProjectConfig.from_file(self.config.last_opened_project)
                return self.current_project_config
            except Exception as e:
                logging.error(f"Failed to load project config from {self.config.last_opened_project}: {e}")
                return None

        logging.warning("No active project config found.")
        return None

    def set_last_opened_project(self, last_opened_project_path):
        """
        User has opened a new project, clear last opened file and reload the project config
        :param last_opened_project_path:
        :return:
        """
        self.config.last_opened_project = last_opened_project_path
        self.config.last_opened_file = None
        self.save_to_file()
        self.current_project_config = None
        self.get_project_config()

    def set_last_opened_file(self, last_opened_file):
        """
        Reload the last opened CSV
        :param last_opened_file:
        :return:
        """
        self.config.last_opened_file = last_opened_file
        self.save_to_file()
        self.current_project_config = last_opened_file
        self.get_project_config()