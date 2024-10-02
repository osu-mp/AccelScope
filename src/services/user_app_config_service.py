import json
import logging
import os
from models.user_app_config import UserAppConfig

class UserAppConfigService:
    USER_CONFIG_FILE = "user_app_config.json"

    @staticmethod
    def save_to_file(config: UserAppConfig):
        with open(UserAppConfigService.USER_CONFIG_FILE, 'w') as file:
            json.dump(config.__dict__, file, indent=4)
            logging.debug(f"Saved app config to {UserAppConfigService.USER_CONFIG_FILE}")

    @staticmethod
    def load_from_file() -> UserAppConfig:
        if os.path.exists(UserAppConfigService.USER_CONFIG_FILE):
            with open(UserAppConfigService.USER_CONFIG_FILE, 'r') as file:
                data = json.load(file)
                logging.debug(f"Loaded app config from {UserAppConfigService.USER_CONFIG_FILE}")
                return UserAppConfig(**data)
        return UserAppConfig()  # Return a new instance with default values if the file does not exist
