from tbot.indicators.candle_indicator import CandleIndicator

from .gann_dir import GannDir
from .gann_legs import GannLegs


class GannABC(CandleIndicator):
    """Class to calculate wave structure of the market."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._gann_legs = GannLegs()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        self._gann_legs.update(series)
        legs = self._gann_legs.last
        res = [None, None]

        # Discover ABCs
        if len(legs) > 2:
            for i in range(2, len(legs)):
                if (
                    legs[i - 2].low < legs[i - 1].low
                    and legs[i - 1].high < legs[i].high
                ):
                    res.append(GannDir.UP)
                elif (
                    legs[i - 2].high > legs[i - 1].high
                    and legs[i - 1].low > legs[i].low
                ):
                    res.append(GannDir.DOWN)
                else:
                    res.append(None)

        self._result.append(res)
