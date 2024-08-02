class SymbolManager:
    """Class to hold data for symbols that will be updated during the lifetime of an application."""

    @classmethod
    def _to_key(cls, symbol, period):
        """Convert a symbol and period to a hashable key.

        .. note::
            This is for internal use within this class.
        """
        return f"{str(symbol)}_{str(period)}"

    def __init__(self):
        """Initialize the symbol manager."""
        super().__init__()
        self._symbols = {}
        self._listeners = []

    def _invoke_listeners(self, feed_key):
        for listener in self._listeners:
            listner_key = self._to_key(listener.symbol, listener.period)
            if feed_key == listner_key:
                listener.process_update(self._symbols[feed_key])

    def add_feed(self, symbol, period, initial_feed_data):
        """Register a feed to a symbol.

        :param str symbol: The name of the symbol to add the feed to
        :param str period: The name of the feed
        :param list[Candle] initial_feed_data: The initial data of the feed, as a list of candles.
        """
        key = self._to_key(symbol, period)
        if key in self._symbols:
            raise ValueError(f"Feed for {key} is already registered")

        self._symbols[key] = initial_feed_data
        if len(initial_feed_data) > 0:
            self._invoke_listeners(key)

    def remove_feed(self, symbol, period):
        """Remove a feed from the symbol manager.

        :param str symbol: The name of the symbol that contains the feed.
        :param str period: The name of the feed to remove.
        """
        key = self._to_key(symbol, period)
        try:
            del self._symbols[key]

        except KeyError:
            pass

    def update_feed(self, symbol, period, update):
        """Update a feed.

        :param str symbol: The name of the symbol
        :param str period: The name of the feed
        :param object update: The update to add to the feed
        """
        key = self._to_key(symbol, period)
        feed = self._symbols[key]
        feed.append(update)

        self._invoke_listeners(key)

    def add_listener(self, symbol_listener):
        """Subscribe to updates from a feed."""
        self._listeners.append(symbol_listener)

    def remove_listener(self, symbol_listener):
        """Unsubscribe from updates to a feed."""
        self._listeners.remove(symbol_listener)
