import logging
import pandas as pd
from input_types.input_interface import InputInterface
from models.axes_config import AxesConfig, AxisDisplay

class VectronicMotionInput(InputInterface):
    """
    Input type class for Vectronic Motion data, handling CSV format specifics.
    """

    def __init__(self, frequency: int):
        """
        Initialize with specific frequency and predefined column info for Vectronic Motion data.

        :param frequency: Expected frequency of the input data in Hz.
        """
        self.frequency = frequency
        self.column_info = {
            "Timestamp": AxisDisplay(input_name="Timestamp", display_name="Timestamp", color="orange", alpha=1.0),
            "Acc X [g]": AxisDisplay(input_name="Acc X [g]", display_name="X-axis", color="red", alpha=0.6),
            "Acc Y [g]": AxisDisplay(input_name="Acc Y [g]", display_name="Y-axis", color="black", alpha=0.5),
            "Acc Z [g]": AxisDisplay(input_name="Acc Z [g]", display_name="Z-axis", color="blue", alpha=0.7)
        }

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from a Vectronic Motion CSV file, creating a timestamp column.

        :param file_path: Path to the data file.
        :return: DataFrame containing the input data.
        """
        try:
            # Load the CSV without skipping rows initially
            df = pd.read_csv(file_path, skiprows=1)

            # Log columns found for debugging
            logging.info(f"Columns found in the file: {df.columns.tolist()}")

            # Combine 'UTC DateTime' and 'Milliseconds' into 'Timestamp' as a full datetime object
            if 'UTC DateTime' in df.columns and 'Milliseconds' in df.columns:
                df['Timestamp'] = pd.to_datetime(
                    df['UTC DateTime'].astype(str) + '.' + df['Milliseconds'].astype(str).str.zfill(3),
                    format='%H:%M:%S.%f'
                )

                # Drop original columns after combining
                df.drop(columns=['UTC DateTime', 'Milliseconds'], inplace=True)
            else:
                missing_cols = [col for col in ['UTC DateTime', 'Milliseconds'] if col not in df.columns]
                raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")

            # Validate format
            self.validate_format(df)
            return df

        except KeyError as e:
            logging.error(f"KeyError encountered: {e}")
            raise ValueError(f"Missing expected columns: {e}")
        except Exception as e:
            logging.error(f"General error encountered: {e}")
            raise ValueError(f"Error loading data from Vectronic file: {e}")

    def validate_format(self, df: pd.DataFrame) -> bool:
        """
        Check that required columns are present in the data.

        :param df: DataFrame to validate.
        :return: True if format is valid, raises an error otherwise.
        """
        # Expected columns based on input names in column_info
        expected_columns = [info.input_name for info in self.column_info.values()]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing expected columns: {missing_columns}")
        return True

    def get_frequency(self) -> int:
        """Return the data frequency."""
        return self.frequency

    def get_axes_config(self) -> AxesConfig:
        """Return axes configuration for Vectronic Motion data, excluding Timestamp."""
        axis_displays = [axis for axis in self.column_info.values() if axis.display_name != "Timestamp"]
        return AxesConfig(axis_displays=axis_displays)
