class PriceLevelAlert:
    """Class to detect when price crosses a specified level."""

    CROSS_ABOVE = 1
    CROSS_BELOW = -1

    def __init__(self, direction, target_price, current_price):
        """Initialize the PriceLevelAlert.

        :param int direction: CROSS_ABOVE or CROSS_BELOW
        :param float target_price: The price this alert should trigger on
        :param float current_price: The current price
        """
        self._target_price = target_price
        self._dir = direction
        self._triggered = False
        self.update(current_price)

    def _fire(self):
        self._triggered = True

    def reset(self):
        """Reset the alert so it can trigger again."""
        self._triggered = False

    def update(self, price):
        """Update the alert with a new price. This will trigger the alert if the new price crosses the target price.

        :param float price: The new price level (the most recent price)
        """
        if self._dir == self.CROSS_ABOVE:
            if price > self._target_price:
                self._fire()

        elif self._dir == self.CROSS_BELOW:
            if price < self._target_price:
                self._fire()

    def triggered(self):
        """Return the status of the alert.

        :return: True if the alert was previously triggered, False otherwise
        :rtype: bool
        """
        return self._triggered
