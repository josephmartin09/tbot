import math

import numpy as np

from tbot.indicators.candle_indicator import CandleIndicator
from tbot.indicators.qte import GannABC, GannDir


class HorizontalSR(CandleIndicator):
    """Indicator of horizontal support and resistance lines."""

    NUM_HISTOGRAM_BINS = 100
    MIN_TOUCHES = 1

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._gann_abc = GannABC()

    def update(self, series):
        """Update the indicator."""
        # Step 1: Classify all inflection points using gann waves
        self._gann_abc.update(series)
        gann_waves = self._gann_abc.data
        inflections = []
        trend_dir = gann_waves[0]
        curr_dir = trend_dir
        for i in range(1, len(gann_waves)):
            curr_dir = gann_waves[i]

            # Local Minimum
            if curr_dir == GannDir.UP and trend_dir == GannDir.DOWN:
                inflections.append(series[i - 1].low)
                trend_dir = curr_dir

            # Local Maximum
            elif curr_dir == GannDir.DOWN and trend_dir == GannDir.UP:
                inflections.append(series[i - 1].high)
                trend_dir = curr_dir

        # Step 2: Create a histogram of the inflections
        range_min = math.floor(min([c.low for c in series]))
        range_max = math.ceil(max([c.high for c in series]))
        touch_cnt, bins = np.histogram(
            inflections,
            bins=self.NUM_HISTOGRAM_BINS,
            range=(range_min, range_max),
        )

        # Step 3: Filter based on minimum touches to be considered a support or resistance
        s_r = []
        for i in range(len(bins) - 1):
            if touch_cnt[i] >= self.MIN_TOUCHES:
                s_r.append(bins[i])

        self._result.append(s_r)
