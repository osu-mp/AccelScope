import datetime


class Label:
    def __init__(self, start_time, end_time, behavior):
        """
        Initialize the label with start/end times and calculate the duration.
        The times can be either datetime or strings (when loading from file, which is converted to datetime).
        :param start_time:
        :param end_time:
        :param behavior:
        """
        if isinstance(start_time, str):
            self.start_time = datetime.datetime.fromisoformat(start_time)
        else:
            self.start_time = start_time
        if isinstance(end_time, str):
            self.end_time = datetime.datetime.fromisoformat(end_time)
        else:
            self.end_time = end_time
        self.behavior = behavior
        self.duration = self.end_time - self.start_time

    def __str__(self):
        start_time_str = self.start_time.strftime('%H:%M:%S.%f')[:-3]
        end_time_str = self.end_time.strftime('%H:%M:%S.%f')[:-3]
        return f"{self.behavior} : {start_time_str} - {end_time_str} ({self.duration})"

    def to_dict(self):
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "behavior": self.behavior
        }

    @staticmethod
    def from_dict(data):
        return Label(data['start_time'], data['end_time'], data['behavior'])
