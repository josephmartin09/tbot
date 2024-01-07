from tbot.indicators.candle_indicator import CandleIndicator

# from .gann_dir import GannDir
from .gann_waves import GannWaves


class GannABC(CandleIndicator):
    """Class to calculate wave structure of the market."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._gann_waves = GannWaves()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        self._gann_waves.update(series)

        self._result = self._gann_waves._result
