import datetime


class Label:
    def __init__(self, start_time, end_time, behavior):
        self.start_time = datetime.datetime.fromisoformat(start_time)
        self.end_time = datetime.datetime.fromisoformat(end_time)
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
