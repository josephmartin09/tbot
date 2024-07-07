from datetime import timedelta


class CandlePeriod:
    """Class to represent the duration of time of a candle."""

    dt_lookup = {
        "1m": timedelta(minutes=1),
        "2m": timedelta(minutes=2),
        "3m": timedelta(minutes=3),
        "5m": timedelta(minutes=5),
        "10m": timedelta(minutes=10),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
    }
    str_lookup = {}
    for key, value in dt_lookup.items():
        str_lookup[value] = key

    @classmethod
    def from_timedelta(cls, dt):
        """Create a CandlePeriod from a timedelta.

        :param timedelta dt: The timedelta representing the candle period
        :return: A candle period representing the requested elapsed time
        :rtype: CandlePeriod
        """
        return CandlePeriod(cls.str_lookup[dt])

    def __init__(self, str):
        """Initialize the CandlePeriod.

        :param str str: The duration of the CandlePeriod, represented as a string.
        """
        self._str = str
        self._dt = self.dt_lookup[str]

    def as_str(self):
        """Return the string representation of the CandlePeriod.

        :return: The string representing the CandlePeriod
        :rtype: str
        """
        return str(self)

    def __str__(self):
        """Return the string representation of the CandlePeriod.

        :return: The string representing the CandlePeriod
        :rtype: str
        """
        return self._str

    def as_timedelta(self):
        """Return the timedelta equivalent of the CandlePeriod.

        :return: The timedelta equivalent of the CandlePeriod.
        :rtype: timedelta
        """
        return self._dt

    def __repr__(self) -> str:
        """Return the object representation of the CandlePeriod.

        :return: A string representing the CandlePeriod object
        :rtype: str
        """
        return f"<CandlePeriod {self._str}>"
