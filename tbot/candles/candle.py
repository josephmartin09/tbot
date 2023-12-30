class Candle:
    """Class to represent an OHLC candle."""

    def __init__(self, time, period, c_open, c_high, c_low, c_close, c_volume):
        """Initialize the candle.

        :param datetime.datetime time: Time of candle open
        :param datetime.timedelta period: The time-period of the candle
        :param float c_open: Open price of the candle
        :param float c_high: High price of the candle
        :param float c_low: Low price of the candle
        :param float c_close: Close price of the candle
        :param float c_volume: Trading volume during candle
        """
        self.time = time
        self.period = period
        self.open = c_open
        self.high = c_high
        self.low = c_low
        self.close = c_close
        self.volume = c_volume

    def __str__(self):
        """Return a string representation of the candle."""
        ret_str = ""
        ret_str += f"Time: {self.time}, "
        ret_str += f"Open: {self.open}, "
        ret_str += f"High: {self.high}, "
        ret_str += f"Low: {self.low}, "
        ret_str += f"Close: {self.close}, "
        ret_str += f"Volume: {self.volume}"
        return ret_str
