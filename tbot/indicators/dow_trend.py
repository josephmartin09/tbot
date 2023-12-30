from .candle_indicator import CandleIndicator
from .gann_with_hoagie import GannWithHoagie


class DowTrend(CandleIndicator):
    """Class to classify candles into DOW trends."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()

        self._gannBar = GannWithHoagie()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        self._gannBar.update(series)
        gann_bars = self._gannBar.data

        inflections = []
        curr_inflection = [gann_bars[0], 0]

        # Calculate all inflections
        for i in range(1, len(gann_bars)):
            if gann_bars[i] != curr_inflection[0]:
                curr_inflection.append(i - 1)
                inflections.append(curr_inflection)
                curr_inflection = [gann_bars[i], i]
        curr_inflection.append(len(gann_bars) - 1)
        inflections.append(curr_inflection)

        # DOW Trends need at least 4 inflections for a trend to exist
        if len(inflections) < 4:
            self._result = [None] * len(series)
            return

        raise NotImplementedError("Haven't figured this one out")
