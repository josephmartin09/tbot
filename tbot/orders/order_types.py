class Order:
    """Order Base Class."""

    pass


class MarketOrder(Order):
    """Class representation of a market order."""


class LimitOrder(Order):
    """Class representation of a limit order."""


class StopOrder(Order):
    """Class representation of a stop (market) order."""


class StopLimitOrder(Order):
    """Class representation of a stop limit order."""
