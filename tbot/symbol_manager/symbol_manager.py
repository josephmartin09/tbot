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
        self._subscribers = []

    def _invoke_subscribers(self, feed_key):
        for subscriber in self._subscribers:
            sub_key = self._to_key(subscriber.symbol, subscriber.period)
            if feed_key == sub_key:
                subscriber.process_update(self._symbols[feed_key])

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
        self._invoke_subscribers(key)

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

        self._invoke_subscribers(key)

    def add_subscriber(self, symbol_subscriber):
        """Subscribe to updates from a feed."""
        self._subscribers.append(symbol_subscriber)

    def remove_subscriber(self, symbol_subscriber):
        """Unsubscribe from updates to a feed."""
        self._subscribers.remove(symbol_subscriber)
