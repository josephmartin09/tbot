from tbot.util import log

from .candle import Candle

LOGGER = log.get_logger()


class CandleSeries:
    """Class to represent a time-continous series of candles."""

    def __init__(self, period, candles, max_candles):
        """Initialize the candle series.

        :param CandlePeriod period: The elapsed time of a candle in this series.
        :param list candles: A list of candles. The candles must all have the same period and be in ascending chronological order
        :param int max_candles: The maximum number of candles to store. This parameter is required because it is impractical
            to keep an infinite number of candles in memory over a long-duration run. It also ensure that indicator calculations
            won't be re-run on the entire historical dataset.
        """
        if max_candles < 2:
            raise ValueError(f"max_candles must be at least 2. Got {max_candles}")

        self._indicators = {}
        self.period = period
        self._period_dt = period.as_timedelta()
        self._max_candles = max_candles
        self._series = candles[-max_candles:]

        self._validate()

    @property
    def last(self):
        """Return the most recent candle in the series."""
        return self._series[-1]

    def __len__(self):
        """Return the length of the candle series."""
        return len(self._series)

    def __iter__(self):
        """Return an iterator to the candle series."""
        return iter(self._series)

    def __getitem__(self, ind):
        """Return the Candle at the requested index.

        :param int ind: The index to request
        :return: The candle at the requested index
        :rtype: Candle
        """
        return self._series[ind]

    def _validate(self):
        # Check that everything is a candle
        for c in self._series:
            if not isinstance(c, Candle):
                raise TypeError("Not all objects in the series of type Candle")

        # Check that every candle has the same timedelta as the series
        for c in self._series:
            if c._period_dt != self._period_dt:
                raise ValueError(
                    f"Not all candles in the series have a period of {str(self.period)}"
                )

    def append(self, candle):
        """Append a candle to the series."""
        # Check that we got a Candle
        if not isinstance(candle, Candle):
            raise TypeError(
                f"Attempted to append an object that is not a Candle. Got {type(candle)}"
            )

        self._series.append(candle)
        while len(self._series) > self._max_candles:
            self._series.pop(0)
