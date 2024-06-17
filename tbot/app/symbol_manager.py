from collections.abc import MutableMapping

# For now, we'll use threads, but we want this to be multi-process and/or ZMQ
from threading import Lock


class SymbolManager(MutableMapping):
    """Class to hold data for symbols that will be updated during the lifetime of an application."""

    def __init__(self):
        """Initialize the symbol manager."""
        super().__init__()
        self._store = {}
        self._lock = Lock()

    def __delitem__(self, key):
        """Delete an item from the symbol manager."""
        with self._lock:
            del self._store[key]

    def __getitem__(self, key):
        """Get an item from the symbol manager."""
        with self._lock:
            return self._store[key]

    def __setitem__(self, key, value):
        """Update an item from the symbol manager."""
        with self._lock:
            self._store[key] = value

    def __iter__(self):
        """Return an iterator for the symbol manager."""
        with self._lock:
            return iter(self._store)

    def __len__(self):
        """Return the total number of keys in the symbol manager."""
        with self._lock:
            return len(self._store)
