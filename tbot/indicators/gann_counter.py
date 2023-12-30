from enum import IntEnum, auto

from .candle_indicator import CandleIndicator


class GannDirection(IntEnum):
    """Enumerated type to represent Gann bar directions."""

    UP = 1
    DOWN = auto()


class GannCounter(CandleIndicator):
    """Class to perform trend detection using a Gann Bar Counting."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        trend = []

        # Label the first direction based on close direction
        if series[0].open < series[0].close:
            trend.append(GannDirection.UP)
        else:
            trend.append(GannDirection.DOWN)

        # Determine Gann Bar Directions
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]

            # Up bar
            if (curr.high > prev.high) and (curr.low > prev.low):
                trend.append(GannDirection.UP)

            # Down bar
            elif (curr.low < prev.low) and (curr.high < prev.high):
                trend.append(GannDirection.DOWN)

            # Inside bar
            elif (curr.high < prev.high) and (curr.low > prev.low):
                trend.append(trend[-1])

            # Outside bar
            else:
                trend.append(trend[-1])

        self._result.append(trend)
