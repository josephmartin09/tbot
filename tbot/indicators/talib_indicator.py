import numpy as np

from .candle_indicator import CandleIndicator


class TalibIndicator(CandleIndicator):
    """Class to wrap calls to TA-Lib in a CandleFeed-compatible object."""

    def __init__(self, talib_fcn, *ta_args, **ta_kwargs):
        """Initialize the indicator.

        :param callable talib_fcn: The TA-lib function to use for the underlying indicator arithmetic
        :param ta_args: Positional arguments to be supplied to the underlying TA-lib call
        :param ta_kwargs: Keyword arguments to be supplied to the underlying TA-lib call
        """
        super().__init__()
        self._fcn = talib_fcn
        self._ta_args = ta_args
        self._ta_kwargs = ta_kwargs

    def update(self, series):
        """Calculate the result of the indicator on the series, then save th result.

        :param CandleSeries series: The series to perform the calculation on
        """
        # Convert the CandleSeries into the TA Lib abstract format
        ta_candles = {"open": [], "high": [], "low": [], "close": []}
        for c in series:
            ta_candles["open"].append(c.open)
            ta_candles["high"].append(c.high)
            ta_candles["low"].append(c.low)
            ta_candles["close"].append(c.close)

        # Convert to numpy float array
        ta_candles["open"] = np.asarray(ta_candles["open"], dtype=np.float64)
        ta_candles["high"] = np.asarray(ta_candles["high"], dtype=np.float64)
        ta_candles["low"] = np.asarray(ta_candles["low"], dtype=np.float64)
        ta_candles["close"] = np.asarray(ta_candles["close"], dtype=np.float64)

        # Run TA-Lib
        result = self._fcn(ta_candles, *self._ta_args, **self._ta_kwargs)

        # It isn't documented anywhere, but it appears some of TA-lib's indicators
        # return more than one value. In this cases, a list is returned.  We have to
        # transpose that list to make the last data point reflect the same time value
        if isinstance(result, list):
            return np.transpose(result)

        # The result is likely in the correct format already
        else:
            return result
