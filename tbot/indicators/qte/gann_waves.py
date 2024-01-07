from collections import namedtuple

from tbot.indicators.candle_indicator import CandleIndicator

from .gann_dir import GannDir
from .gann_with_hoagie import GannWithHoagie

Inflection = namedtuple("Inflection", ["dir", "start_ind", "end_ind", "low", "high"])


class GannWaves(CandleIndicator):
    """Class to calculate abc structure of the market."""

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()

        self._gann_h = GannWithHoagie()

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        self._gann_h.update(series)
        gann_bars = self._gann_h.data

        # Calculate direction, start, and end indicies of inflections
        inf_params = []
        curr_inflection = [gann_bars[0], 0]
        for i in range(1, len(gann_bars)):
            if gann_bars[i] != curr_inflection[0]:
                curr_inflection.append(i - 1)
                inf_params.append(curr_inflection)
                curr_inflection = [gann_bars[i], i - 1]
        curr_inflection.append(len(gann_bars) - 1)
        inf_params.append(curr_inflection)

        # Create inflection tuples from params determined above:
        # 1) The first inflection doesn't know about previous inflections.
        # We have to do it separatley using the start of the inflection as
        # the low or high
        inflections = []
        inf = inf_params[0]
        if inf[0] == GannDir.DOWN:
            inf_lows = [c.low for c in series[inf[1] : inf[2] + 1]]
            inflections.append(
                Inflection(inf[0], inf[1], inf[2], min(inf_lows), series[inf[1]].high)
            )
        else:
            inf_highs = [c.high for c in series[inf[1] : inf[2] + 1]]
            inflections.append(
                Inflection(inf[0], inf[1], inf[2], series[inf[1]].low, max(inf_highs))
            )

        # 2) The rest of the inflections use the previous inflection as a starting point
        for i in range(1, len(inf_params)):
            inf = inf_params[i]
            prev_inf = inflections[i - 1]
            if inf[0] == GannDir.DOWN:
                inf_lows = [c.low for c in series[inf[1] : inf[2] + 1]]
                inflections.append(
                    Inflection(inf[0], inf[1], inf[2], min(inf_lows), prev_inf.high)
                )
            else:
                inf_highs = [c.high for c in series[inf[1] : inf[2] + 1]]
                inflections.append(
                    Inflection(inf[0], inf[1], inf[2], prev_inf.low, max(inf_highs))
                )

        print(series[0].time)
        self._result.append(inflections)
