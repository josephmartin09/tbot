from .feed import Feed


class TickerFeed(Feed):
    """Ticker Data Feed."""

    def __init__(self):
        """Initialize the ticker feed."""
        super().__init__()

    # Need a tick data structure:
    # tick: direction, volume, price, time
