from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Feed(ABC):
    """Base class representation of a time-series financial market data feed."""

    @classmethod
    def datetime_from_millis(cls, ts):
        """Create a UTC datetime from a millisecond POSIX timestamp.

        :param int ts: UNIX Timestamp, in MILLISECONDS, to convert
        :returns: UTC datetime representing the timestamp
        """
        return datetime.fromtimestamp(int(ts / 1000), tz=timezone.utc)

    @classmethod
    def millis_from_datetime(cls, dt):
        """Create a POSIX millisecond timestamp from a datetime.

        :param datetime.datetime: Datetime to convert
        :returns: Integer millisecond timestamp
        """
        return int(dt.timestamp()) * 1000

    def __init__(self):
        """Initialize the feed."""
        pass

    @abstractmethod
    def connect(self):
        """Connect to the feed's underlying data source."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the feed's underlying data source."""
        pass

    @abstractmethod
    def next(self):
        """Retrieve the next available data point from the feed."""
        pass
