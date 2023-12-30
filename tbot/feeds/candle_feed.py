from abc import abstractmethod

from .feed import Feed


class CandleFeed(Feed):
    """Class representation of a time-series market feed that provides OHLCV candles."""

    def __init__(self, symbol, period):
        """Initialze the feed.

        :param str symbol: The symbol whose candles should be returned in this feed.
        :param datetime.timedelta period: The desired timeperiod of the candle series
        """
        super().__init__()
        self._symbol = symbol
        self._period = period
        self._series = None

    def _init_candles(self, series):
        """Initialize or replace the current candle series with a new series.

        :param CandleSeries series: The series to use for this feed.

        .. note::
            This is not meant to be called directly by a user. It should be called by a child class
            to initialize the starting candles for a feed upon connect().
        """
        self._series = series

    @abstractmethod
    def _next_candle(self):
        """Return the next candle from the data feed.

        .. note::
            This function is not meant to be called directly by a user. It is meant to be
            used as an internal implementation for a specific exchange/brokerage. It will be called from
            next()
        """
        pass

    def next(self):
        """Return the next candle from the data feed."""
        # We are making the assumption that _next_candle appends the next candle.
        # This is a bad design pattern. Appending needs to be done here.
        candle = self._next_candle()

        # Update all indicators
        self._update_indicators()

        # Return the candle to the user
        return candle

    @property
    def candles(self):
        """Return a reference to the CandleSeries this feed has created."""
        if not self._series:
            raise RuntimeError(
                "CandleFeed child class did not populate the series variable."
            )
        return self._series
