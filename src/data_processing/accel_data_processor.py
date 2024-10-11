import pandas as pd
import datetime


class AccelDataProcessor:
    @staticmethod
    def find_nearest_behaviors(data: pd.DataFrame, labels: list, input_time: datetime):
        # Sort the labels by their start time to ensure correct ordering
        labels = sorted(labels, key=lambda x: x.start_time)

        prev_label = None
        next_label = None

        # Iterate over the sorted labels to determine the nearest behaviors
        for label in labels:
            # if input time falls within a label, return that label start/end
            if label.start_time <= input_time <= label.end_time:
                prev_label = label.start_time
                next_label = label.end_time
                break
            elif label.end_time <= input_time:
                # This label is before the input time
                prev_label = label.end_time
            elif label.start_time > input_time and next_label is None:
                # This label is the first one after the input time
                next_label = label.start_time
                break

        # If there's no previous label, set it to the start of the data
        if prev_label is None:
            prev_label = data['Timestamp'].min()

        # If there's no next label, set it to the end of the data
        if next_label is None:
            next_label = data['Timestamp'].max()

        return prev_label, next_label
