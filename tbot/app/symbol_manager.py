# For now, we'll use threads, but we want this to be multi-process and/or ZMQ
from threading import Lock


class SymbolManager:
    """Class to hold data for symbols that will be updated during the lifetime of an application."""

    def __init__(self):
        """Initialize the symbol manager."""
        super().__init__()
        self._symbols = {}
        self._lock = Lock()

    def add_symbol(self, name):
        """Register a symbol.

        :param str name: The name of the symbol
        """
        pass

    def add_feed(self, symbol, name, initial_feed_data):
        """Register a feed to a symbol.

        :param str symbol: The name of the symbol to add the feed to
        :param str name: The name of the feed
        :param object initial_feed_data: The initial data of the feed
        """
        pass

    def update_feed(self, symbol, feed_name, update):
        """Update a feed.

        :param str symbol: The name of the symbol
        :param str feed: The name of the feed
        :param object update: The update to add to the feed
        """
        if symbol not in self._symbols:
            raise ValueError(f"Symbol {symbol} is not registered")

        feeds = self._symbols[symbol]
        if feed_name not in feeds:
            raise ValueError(f"Feed {feed_name} is not registered")

        feed = feeds[feed_name]
        feed.append(update)

    def remove_feed(self, symbol, feed):
        """Remove a feed from the symbol manager.

        :param str symbol: The name of the symbol that contains the feed.
        :param str feed: The name of the feed to remove.
        """
        pass
