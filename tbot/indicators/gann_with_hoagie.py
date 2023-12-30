from enum import IntEnum, auto

from .candle_indicator import CandleIndicator


class GannDirection(IntEnum):
    """Enumerated type to represent Gann bar directions."""

    UP = 1
    DOWN = auto()


class GannWithHoagie(CandleIndicator):
    """Class to perform trend detection using a Gann Bar Counting.

    .. note::
        This strategy includes the "hoagie" theory popularized by QuantTradeEdge YouTube channel
    """

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        trend = []
        hoagie_active = False
        hoagie_candle = None

        # Label the first direction based on close direction
        if series[0].open < series[0].close:
            trend.append(GannDirection.UP)
        else:
            trend.append(GannDirection.DOWN)

        # Determine Gann Bar Directions
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]

            if hoagie_active:
                # Up bar
                if (curr.high > hoagie_candle.high) and (curr.low > hoagie_candle.low):
                    trend.append(GannDirection.UP)
                    hoagie_active = False
                    hoagie_candle = None

                # Down bar
                elif (curr.low < hoagie_candle.low) and (
                    curr.high < hoagie_candle.high
                ):
                    trend.append(GannDirection.DOWN)
                    hoagie_active = False
                    hoagie_candle = None

                # Inside bar
                elif (curr.high < hoagie_candle.high) and (
                    curr.low > hoagie_candle.low
                ):
                    trend.append(trend[-1])

                # Outside bar
                else:
                    trend.append(trend[-1])
                    hoagie_active = False
                    hoagie_candle = None

            else:
                # Up bar
                if (curr.high > prev.high) and (curr.low > prev.low):
                    trend.append(GannDirection.UP)

                # Down bar
                elif (curr.low < prev.low) and (curr.high < prev.high):
                    trend.append(GannDirection.DOWN)

                # Inside bar
                elif (curr.high < prev.high) and (curr.low > prev.low):
                    trend.append(trend[-1])
                    hoagie_active = True
                    hoagie_candle = prev

                # Outside bar
                else:
                    trend.append(trend[-1])

        self._result = trend
