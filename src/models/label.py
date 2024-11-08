from datetime import datetime, time


class Label:
    def __init__(self, start_time, end_time, behavior):
        """
        Initialize the label with start/end times and calculate the duration.
        The times are stored as `datetime.time`.
        :param start_time: Time string in 'HH:MM:SS.ffffff' format
        :param end_time: Time string in 'HH:MM:SS.ffffff' format
        :param behavior: The behavior name
        """
        if isinstance(start_time, str):
            self.start_time = datetime.strptime(start_time, "%H:%M:%S.%f").time()
        else:
            self.start_time = start_time

        if isinstance(end_time, str):
            self.end_time = datetime.strptime(end_time, "%H:%M:%S.%f").time()
        else:
            self.end_time = end_time

        self.behavior = behavior
        self.duration = self.calculate_duration()

        # Validate the label upon creation
        self.validate()

    def __str__(self):
        start_time_str = self.start_time.strftime('%H:%M:%S.%f')[:-3]
        end_time_str = self.end_time.strftime('%H:%M:%S.%f')[:-3]
        return f"{self.behavior} : {start_time_str} - {end_time_str} ({self.duration})"

    def calculate_duration(self):
        # Calculate the duration between start and end times
        start_dt = datetime.combine(datetime.min, self.start_time)
        end_dt = datetime.combine(datetime.min, self.end_time)
        return end_dt - start_dt

    def validate(self):
        """
        Validate that the label has valid start and end times.
        - Ensures that the start time is before the end time.
        - Raises a ValueError if validation fails.
        """
        if self.start_time >= self.end_time:
            raise ValueError(
                f"Invalid label times: Start time {self.start_time} is not before end time {self.end_time}.")

    @staticmethod
    def from_dict(data):
        # Parse start_time and end_time as time strings in the format 'HH:MM:SS.ffffff'
        start_time = data['start_time']
        end_time = data['end_time']
        return Label(start_time, end_time, data['behavior'])

    def to_dict(self):
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "behavior": self.behavior
        }
