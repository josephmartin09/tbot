import math

import numpy as np

from .candle_indicator import CandleIndicator
from .gann_waves import GannWaves
from .gann_with_hoagie import GannDirection


class HorizontalSR(CandleIndicator):
    """Indicator of horizontal support and resistance lines."""

    NUM_HISTOGRAM_BINS = 100
    MIN_TOUCHES = 1

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._gann_waves = GannWaves()

    def update(self, series):
        """Update the indicator."""
        # Step 1: Classify all inflection points using gann waves
        self._gann_waves.update(series)
        gann_waves = self._gann_waves.data
        inflections = []
        trend_dir = gann_waves[0]
        curr_dir = trend_dir
        for i in range(1, len(gann_waves)):
            curr_dir = gann_waves[i]

            # Local Minimum
            if curr_dir == GannDirection.UP and trend_dir == GannDirection.DOWN:
                inflections.append(series[i - 1].low)
                trend_dir = curr_dir

            # Local Maximum
            elif curr_dir == GannDirection.DOWN and trend_dir == GannDirection.UP:
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
