from datetime import datetime, time


# Sentinel date used for legacy time-only labels
_SENTINEL_DATE = datetime.min.date()


class Label:
    def __init__(self, start_time, end_time, behavior):
        """
        Initialize the label with start/end times and calculate the duration.
        Times are stored as `datetime.datetime`. Accepts datetime, time, or string inputs.
        For backward compatibility, time-only values are combined with datetime.min date.
        """
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.behavior = behavior
        self.duration = self.calculate_duration()
        self.validate()

    @staticmethod
    def _parse_time(value):
        """Parse a time value into a datetime object."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, time):
            return datetime.combine(_SENTINEL_DATE, value)
        if isinstance(value, str):
            # Try full ISO datetime first (e.g. "2018-06-08T05:58:42.428860")
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
            # Fall back to time-only (e.g. "05:58:42.428860")
            try:
                return datetime.combine(_SENTINEL_DATE, datetime.strptime(value, "%H:%M:%S.%f").time())
            except ValueError:
                pass
            # Try without microseconds (e.g. "05:58:42")
            return datetime.combine(_SENTINEL_DATE, datetime.strptime(value, "%H:%M:%S").time())
        raise TypeError(f"Cannot parse time value of type {type(value)}: {value}")

    @staticmethod
    def is_legacy_time_only(dt):
        """Check if a datetime uses the sentinel date (legacy time-only label)."""
        return dt.date() == _SENTINEL_DATE

    def __str__(self):
        start_time_str = self.start_time.strftime('%H:%M:%S.%f')[:-3]
        end_time_str = self.end_time.strftime('%H:%M:%S.%f')[:-3]
        return f"{self.behavior} : {start_time_str} - {end_time_str} ({self.duration})"

    def calculate_duration(self):
        return self.end_time - self.start_time

    def validate(self):
        if self.start_time >= self.end_time:
            raise ValueError(
                f"Invalid label times: Start time {self.start_time} is not before end time {self.end_time}.")

    @staticmethod
    def from_dict(data):
        return Label(data['start_time'], data['end_time'], data['behavior'])

    def to_dict(self):
        return {
            "start_time": self._serialize_time(self.start_time),
            "end_time": self._serialize_time(self.end_time),
            "behavior": self.behavior
        }

    @staticmethod
    def _serialize_time(dt):
        """Serialize: legacy time-only as HH:MM:SS.ffffff, full datetime as ISO format."""
        if Label.is_legacy_time_only(dt):
            return dt.time().isoformat()
        return dt.isoformat()
