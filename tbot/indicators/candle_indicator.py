from abc import abstractmethod

from .indicator import Indicator


class CandleIndicator(Indicator):
    """Class to represent an indicator called on a CandleSeries."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._result = None

    def _update(self, series):
        self._result = self.update(series)

    @abstractmethod
    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        pass

    @property
    def last(self):
        """Return the last value in the indicator, which corresponds to the most recent point in time."""
        if self._result is not None:
            return self._result[-1]
        return None

    @property
    def data(self):
        """Return the full data set calculated on the underlying candles."""
        return self._result
