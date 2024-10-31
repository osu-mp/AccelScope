from enum import Enum


class InputType(Enum):
    """
    Supported file formats for input data.
    Each input type represents a specific data format, potentially with unique
    handling requirements, frequency constraints, and column structure.
    """
    VECTRONIC_MOTION = "VectronicMotion"


class InputSettings:
    """
    Defines settings for reading and processing input files.
    Configurable settings include input type and frequency.
    """
    def __init__(self, input_type: InputType, input_frequency: int):
        """
        Initialize input settings with specific type and frequency.

        :param input_type: Type of input (e.g., Vectronic Motion)
        :param input_frequency: Expected frequency of the input data in Hz.
        """
        self.input_type = input_type
        self.input_frequency = input_frequency

    def validate(self):
        """Validate input settings to ensure proper configuration."""
        if not isinstance(self.input_type, InputType):
            raise ValueError("Invalid input type specified.")
        if self.input_frequency <= 0:
            raise ValueError("Input frequency must be a positive integer.")

    def to_dict(self):
        """Convert input settings to a dictionary for serialization."""
        return {
            "input_type": self.input_type.value,
            "input_frequency": self.input_frequency
        }

    @staticmethod
    def from_dict(data):
        """
        Creates an InputSettings instance from a dictionary, providing default values for missing keys.
        :param data: Dictionary containing input settings data.
        :return: An instance of InputSettings.
        """
        # Safely access the keys with default values if they are missing
        input_type = data.get("input_type", "UnknownInputType")  # Or provide a fallback/default
        input_frequency = data.get("input_frequency", 0)  # Default frequency if missing

        # Convert to Enum or required data types if applicable
        return InputSettings(
            input_type=InputType(input_type),
            input_frequency=input_frequency
        )
