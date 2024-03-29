from tbot.indicators import Indicator

from .candle import Candle


class CandleSeries:
    """Class to represent a time-continous series of candles."""

    def __init__(self, candle_period, candles, max_candles):
        """Initialize the candle series.

        :param timedelta candle_period: The elapsed time of a candle in this series.
        :param list candles: A list of candles. The candles must all have the same period and be in ascending chronological order
        :param int max_candles: The maximum number of candles to store. This parameter is required because it is impractical
            to keep an infinite number of candles in memory over a long-duration run. It also ensure that indicator calculations
            won't be re-run on the entire historical dataset.
        """
        if max_candles < 2:
            raise ValueError(f"max_candles must be at least 2. Got {max_candles}")

        self._indicators = {}
        self._candle_period = candle_period
        self._max_candles = max_candles
        self._series = candles[-max_candles:]

        self._validate()

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
            if c.period != self._candle_period:
                raise ValueError(
                    f"Not all candles in the series have a period of {str(self._candle_period)}"
                )

    def _update_indicators(self):
        for ind in self._indicators.values():
            ind._update(self)

    def append(self, candle):
        """Append a candle to the series."""
        # Check that we got a Candle
        if not isinstance(candle, Candle):
            raise TypeError(
                f"Attempted to append an object that is not a Candle. Got {type(candle)}"
            )

        # Add it
        self._series.append(candle)
        while len(self._series) > self._max_candles:
            self._series.pop(0)

        # Update indicators
        self._update_indicators()

    def last(self):
        """Return the most recent candle in the series."""
        return self._series[-1]

    @property
    def indicators(self):
        """Return the indicator instance registered to a particular name.

        :returns: The underlying indicator data store, which is a dict of (name -> Indicator instance)
        :rtype: dict
        """
        return self._indicators

    def register_indicator(self, name, indicator):
        """Register an indicator to apply to this feed.

        :param str name: A unique name to indentify this indicator. For example, "sma_14"
        :param Indicator indicator: A indicator instance to register for this feed.
        """
        if not isinstance(indicator, Indicator):
            raise TypeError(
                f"Param 'indicator' must be of type Indicator. Got {type(indicator)}"
            )
        if name in self._indicators:
            raise ValueError(
                f"There is already an indicator named '{name}' registered."
            )

        self._indicators[name] = indicator
        indicator._update(self)

    def unregister_indicator(self, name):
        """Unregister an indicator from the feed.

        :param str name: The registered name of the indicator
        """
        try:
            del self._indicators[name]
        except KeyError:
            pass
