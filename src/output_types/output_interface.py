from abc import ABC, abstractmethod
from models.project_config import ProjectConfig


class OutputGeneratorInterface(ABC):
    """
    Interface that defines how a project config is translated into output files.

    This interface outlines the core structure for generating output files
    based on a project configuration, allowing for extensible implementations
    of different output formats (e.g., BEBE, etc.).

    The implementation should:
      - Generate output files from one or more input files as defined in the ProjectConfig.
      - Ensure that each output class dynamically handles its own settings and output logic.
      - Return the paths of generated files and report any failures encountered during processing.
      - Optionally, allow for downsampling, period-specific output, and configurable output frequencies.
    """

    @abstractmethod
    def generate_output(self, project_config: ProjectConfig, output_dir: str, settings: dict):
        """
        Generate output files based on the provided project configuration.

        :param project_config: The project configuration object containing file paths and labels.
        :param output_dir: The directory where the output files should be saved.
        :param settings: A dictionary containing specific output settings (e.g., frequency, downsampling method, etc.).
        :return: A tuple of (list of generated file paths, list of errors encountered).
        """
        pass

    @abstractmethod
    def validate_settings(self, settings):
        """
        Validate the settings before generating output.

        :param settings: Settings for the output, such as frequency, method, etc.
        :return: Boolean indicating whether the settings are valid, along with error messages if not.
        """
        pass