import traceback
from datetime import datetime

import pytz

from .candle_period import CandlePeriod


class CandleParseError(Exception):
    """Exception denotating that a candle could not be parsed from JSON format."""

    def __init__(self, *args):
        """Initialize the exception object."""
        super().__init__(*args)


class Candle:
    """Class to represent an OHLC candle."""

    def __init__(self, period, time, c_open, c_high, c_low, c_close, c_volume):
        """Initialize the candle.

        :param CandlePeriod period: The time-period of the candle
        :param datetime.datetime time: Time of candle open
        :param float c_open: Open price of the candle
        :param float c_high: High price of the candle
        :param float c_low: Low price of the candle
        :param float c_close: Close price of the candle
        :param float c_volume: Trading volume during candle
        """
        self.period = period
        self._period_dt = period.as_timedelta()
        self.time = time
        self.open = c_open
        self.high = c_high
        self.low = c_low
        self.close = c_close
        self.volume = c_volume

    def __str__(self):
        """Return a string representation of the candle."""
        ret_str = ""
        ret_str += f"Time: {self.time}, "
        ret_str += f"Period: {self.period}, "
        ret_str += f"O: {self.open}, "
        ret_str += f"H: {self.high}, "
        ret_str += f"L: {self.low}, "
        ret_str += f"C: {self.close}, "
        ret_str += f"Vol: {self.volume}"
        return ret_str

    def to_json_dict(self):
        """Return a JSON-serializable dictionary representation of a candle.

        :rtype: dictionary
        """
        return {
            "period": str(self.period),
            "time": int(self.time.timestamp() * 1000),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    @classmethod
    def from_json_dict(cls, json_dict):
        """Create a candle from a JSON dictionary representation of the candle.

        :param dictioinary json_dict: A JSON dictionary representation of the candle.

        .. note::
            It is expected that the json_dict param is a python dict, not a JSON string
        """
        err = None
        c = None
        try:
            c = Candle(
                CandlePeriod(json_dict["period"]),
                datetime.fromtimestamp(
                    float(json_dict["time"]) / 1000, tzinfo=pytz.utc
                ),
                json_dict["open"],
                json_dict["high"],
                json_dict["low"],
                json_dict["close"],
                json_dict["volume"],
            )

        except Exception:
            err = traceback.format_exc()

        finally:
            if err:
                raise CandleParseError(err)

            return c
