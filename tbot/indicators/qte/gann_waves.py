from tbot.indicators.candle_indicator import CandleIndicator

from .gann_dir import GannDir
from .gann_with_hoagie import GannWithHoagie


class GannWaves(CandleIndicator):
    """Class to calculate wave structure of the market."""

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

        # Calculate the first wave using data from the first inflection period
        gann_waves = [-1] * len(series)
        for i in range(0, inflections[0][2] + 1):
            gann_waves[i] = inflections[0][0]
        trend_inflection = inflections[0]

        # Use previous inflections to calculate the larger trend
        for i in range(1, len(inflections)):
            trend_dir = trend_inflection[0]
            curr_dir = inflections[i][0]
            assigned_dir = None

            # We moved from UP to DOWN
            if curr_dir == GannDir.DOWN:
                # Check for lower low to indicate new trend
                if series[inflections[i][2]].low < series[inflections[i - 1][1]].low:
                    assigned_dir = GannDir.DOWN
                    trend_inflection = inflections[i]
                else:
                    assigned_dir = trend_dir

            # We moved from DOWN to UP
            elif curr_dir == GannDir.UP:
                # Check for higher high to indicate new trend
                if series[inflections[i][2]].high > series[inflections[i - 1][1]].high:
                    assigned_dir = GannDir.UP
                    trend_inflection = inflections[i]
                else:
                    assigned_dir = trend_dir

            # Fill in the candles
            for i in range(inflections[i][1], inflections[i][2] + 1):
                gann_waves[i] = assigned_dir

        self._result = gann_waves
