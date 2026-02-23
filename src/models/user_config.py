class UserConfig:
    """Represents a single user's configuration within a project."""

    def __init__(self, username, display_name=None, alias=None, data_root=None):
        self.username = username
        self.display_name = display_name or username.capitalize()
        self.alias = alias or username[:2].upper()
        self.data_root = data_root

    def to_dict(self):
        return {
            "username": self.username,
            "display_name": self.display_name,
            "alias": self.alias,
            "data_root": self.data_root,
        }

    @staticmethod
    def from_dict(data):
        return UserConfig(
            username=data["username"],
            display_name=data.get("display_name"),
            alias=data.get("alias"),
            data_root=data.get("data_root"),
        )
