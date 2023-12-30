from sortedcollections import SortedDict


class BookLevel:
    """Class to represent a price, volume level within a level 2 order-depth book."""

    def __init__(self, price, volume):
        """Initialize the BookLevel with a price and volume."""
        self.price = price
        self.volume = volume


class BidLevel(BookLevel):
    """Class to represent a Bid BookLevel."""

    def __init__(self, price, volume):
        """Initialize the BookLevel with a price and volume."""
        super().__init__(price, volume)


class AskLevel(BookLevel):
    """Class to represent an Ask BookLevel."""

    def __init__(self, price, volume):
        """Initialize the BookLevel with a price and volume."""
        super().__init__(price, volume)


class OrderBook:
    """Class to maintain a Level2 Order-Depth Book."""

    def __init__(self):
        """Initialize the OrderBook as empty."""
        self._reset()

    def _reset(self):
        self._bids = SortedDict()
        self._asks = SortedDict()

        self._stats = {"last_stat_price": 0.0, "bid_rem": 0.0, "ask_rem": 0.0}

    def sync(self, new_book_state):
        """Replace the current state of the book with a new order book state.

        :param list new_book_state: A list of BookOrder objects that represents the new order book snapshot

        .. note::
            This will remove all previously existing level data. This is useful if there was a connection loss
            and the book needs to be recovered
        """
        self._reset()
        for o in new_book_state:
            self.update(o)

    def _set_level(self, level_d, level):
        self._update_stats(level)

        if level.volume == 0:
            try:
                del level_d[level.price]
            except KeyError:
                pass

        else:
            level_d[level.price] = level.volume

    def update(self, level):
        """Update a book level.

        :param BookLevel level: A price->volume BookLevel to replace in the order book.

        .. note::
            If the volume of the level param is 0, this means the existing price level will be deleted from the order book.
            If the volume of the level param is not 0, the existing volume for the price level will be replaced by the volume in the level param.
        """
        if isinstance(level, BidLevel):
            self._set_level(self._bids, level)

        elif isinstance(level, AskLevel):
            self._set_level(self._asks, level)

        else:
            raise ValueError(
                f"Param 'level' must be either BidLevel or AskLevel. Got {type(level)}"
            )

    @property
    def price(self):
        """Return the mid-market price from the best bid and ask."""
        if (len(self._asks) == 0) or (len(self._bids) == 0):
            return 0.0
        return (self._asks.peekitem(0)[0] + self._bids.peekitem()[0]) / 2

    @property
    def spread(self):
        """Return the spread between the best bid and ask."""
        return self._asks.peekitem(0)[0] - self._bids.peekitem()[0]

    # Stuff that might need to be subclassed, but I suspect is important
    def _update_stats(self, level):
        last_stat_price = self._stats["last_stat_price"]
        if last_stat_price == 0.0:
            self._stats["last_stat_price"] = self.price

        if level.volume == 0:
            if abs((last_stat_price - level.price)) < (0.005 * last_stat_price):
                if isinstance(level, BidLevel):
                    self._stats["bid_rem"] += self._bids.get(level.price, 0)
                else:
                    self._stats["ask_rem"] += self._asks.get(level.price, 0)

    def get_stats(self):
        """Calculate statistics on volume change in the order book."""
        s = self._stats
        try:
            s["price_chg_pct"] = (
                100 * (self.price - s["last_stat_price"]) / s["last_stat_price"]
            )
        except ZeroDivisionError:
            s["price_chg_pct"] = 0

        self._stats = {"last_stat_price": 0.0, "bid_rem": 0.0, "ask_rem": 0.0}
        return s
