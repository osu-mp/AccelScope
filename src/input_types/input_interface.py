from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from models.axes_config import AxisInfo, AxesConfig, AxisDisplay


class InputInterface(ABC):
    """
    Interface for input data types, ensuring standard methods for loading, interpreting,
    and configuring data properties.
    """

    def __init__(self):
        """
        Initializes the input interface with a column_info list.
        Each inheriting class must define its `column_info` as a list of `AxisInfo` objects.
        """
        self.column_info: List[AxisInfo] = []

    @abstractmethod
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from the specified file into a DataFrame, applying column mapping and adjustments.

        :param file_path: Path to the data file.
        :return: A DataFrame containing the input data.
        """
        pass

    @abstractmethod
    def get_frequency(self) -> int:
        """
        Get the data frequency defined in the input settings.

        :return: Frequency in Hz.
        """
        pass

    @abstractmethod
    def validate_format(self, df: pd.DataFrame) -> bool:
        """
        Validate that the data format meets the expected structure.

        :param df: DataFrame to validate.
        :return: True if the format is valid; otherwise, raises an error or returns False.
        """
        pass

    def get_axes_config(self) -> AxesConfig:
        """
        Create and return an AxesConfig based on the column_info provided by the inheritor.

        :return: An AxesConfig instance with axis information.
        """
        return AxesConfig(axes_info=self.column_info)

    def get_default_display_config(self) -> List[AxisDisplay]:
        """
        Optionally provides a default display configuration for visual representation.
        If not overridden, returns an empty list.

        :return: List of AxisDisplay configurations for each axis.
        """
        return []
