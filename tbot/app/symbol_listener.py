from tbot.indicators import Indicator


class SymbolListener:
    """Class to receive updates for a symbol feed from the symbol manager."""

    def __init__(self, symbol, period):
        """Initialize the SymbolListener.

        :param str symbol: The symbol of interest
        :param CandlePeriod period: The time period the feed will be delimited by
        """
        self._indicators = {}
        self._feed = None
        self._has_update = False

        self._symbol = symbol
        self._period = period

    def process_update(self, new_feed):
        """Ingest an update from the symbol manager.

        :param CandleSeries new_feed: The most recent data for this listener's feed

        ..note::
            This is meant to be called only by the symbol manager object.
        """
        self._feed = new_feed
        self._has_update = True

    def has_update(self):
        """Report the availability of a new feed update.

        :return: True if there's been a feed update since the last call of this function, False otherwise
        :rtype: bool
        """
        has_update = self._has_update
        self._has_update = False
        return has_update

    @property
    def symbol(self):
        """Get the symbol name of this listnener.

        :return: The symbol name
        :rtype: str
        """
        return self._symbol

    @property
    def period(self):
        """Get the period of this listener.

        :return: The period of the feed registered to this listener
        :rtype: CandlePeriod
        """
        return self._period

    @property
    def feed(self):
        """Get the feed requested by this listener.

        :return: The feed requested by this listener
        :rtype: CandleSeries
        """
        return self._feed

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
