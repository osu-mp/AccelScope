from typing import List


class AxisDisplay:
    """Defines how each axis is displayed on the graph, including its color, transparency, and input name."""
    def __init__(self, display_name: str, color: str, alpha: float, input_name: str):
        """
        :param display_name: Name to be displayed on the graph
        :param color: Color of the axis on the display
        :param alpha: Transparency level for the axis display
        :param input_name: Name of the axis in the input data
        """
        self.display_name: str = display_name
        self.color: str = color
        self.alpha: float = alpha
        self.input_name: str = input_name


class AxisInfo:
    """Stores metadata for each axis, including name, data type, unit, and column index in the input data."""
    def __init__(self, name: str, data_type: str, unit: str, index: int):
        """
        :param name: Name of the axis (e.g., "Acc X [g]")
        :param data_type: Type of data in the axis (e.g., "float")
        :param unit: Unit of measurement (e.g., "[g]")
        :param index: Column index in the input data
        """
        self.name: str = name
        self.data_type: str = data_type
        self.unit: str = unit
        self.index: int = index


class AxesConfig:
    """Manages the configuration of multiple axes, storing display settings and
    providing access to axis names and units."""
    def __init__(self, axis_displays: List[AxisDisplay]):
        """
        Initialize with a list of AxisDisplay instances defining each axis's display settings.

        :param axis_displays: List of AxisDisplay configurations.
        """
        self.axis_displays = axis_displays

    def get_axis_names(self) -> List[str]:
        return [axis.display_name for axis in self.axis_displays]

    def get_axis_units(self) -> List[str]:
        return [axis.unit for axis in self.axis_displays if hasattr(axis, 'unit')]
