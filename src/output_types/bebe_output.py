from output_interface import OutputGeneratorInterface
from models.output_settings import OutputSettings
from models.project_config import ProjectConfig
import os
import logging


class BEBEOutput(OutputGeneratorInterface):
	"""
	Output targeting the BEBE (Bio-logger Ethogram Benchmark) tool
	The general format is to convert each input CSV into a separate output CSV.
	The project directories will be used as individual animal IDs as far as BEBE is concerned
	"""

	def __init__(self):
		"""Initialize any required parameters or state."""
		pass

	def generate_output(self, project_config: ProjectConfig, output_dir: str, settings: dict):
		"""
        Generate output files based on the provided project configuration.

        :param project_config: The project configuration object containing file paths and labels.
        :param output_dir: The directory where the output files should be saved.
        :param settings: A dictionary containing specific output settings (e.g., frequency, downsampling method, etc.).
        :return: A tuple of (list of generated file paths, list of errors encountered).
        """
		output_files = []

		# TODO Loop through the files in project data and process them

		return output_files

	def _generate_bebe_from_csv(self, file_entry, settings: OutputSettings):
		"""
		A placeholder method for generating BEBE output from a single input CSV file.

		Args:
			file_entry: Information about the CSV file (path, labels, etc.).
			settings: Output settings that apply to this file generation.

		Returns:
			The path to the generated output file.
		"""
		if True:
			raise Exception("not implemented yet")
		# Placeholder for actual CSV processing and output generation
		output_dir = settings.output_directory
		input_file_path = os.path.join(settings.project_root_directory, file_entry.path)

		# Create an output file path (could be BEBE-specific naming convention)
		output_file_name = f"{os.path.splitext(os.path.basename(input_file_path))[0]}_bebe_output.csv"
		output_file_path = os.path.join(output_dir, output_file_name)

		# Ensure the output directory exists
		if not os.path.exists(output_dir):
			os.makedirs(output_dir)

		logging.info(f"Generating BEBE output for {input_file_path}...")

		# Placeholder: simulate writing output data
		with open(output_file_path, 'w') as f:
			f.write("BEBE output content\n")
		# Here is where the BEBE-specific format would be written

		logging.info(f"BEBE output generated: {output_file_path}")

		return output_file_path

	def validate_settings(self, settings: OutputSettings):
		"""
		Validate the provided settings before generating output.

		Args:
			settings: The output settings to validate.

		Returns:
			True if the settings are valid, False otherwise.
		"""
		if not settings.output_directory:
			logging.error("Output directory is not specified.")
			return False

		if settings.output_frequency > settings.input_frequency:
			logging.error("Output frequency cannot be higher than input frequency.")
			return False

		# Additional validation logic for BEBE output-specific settings can go here

		return True
