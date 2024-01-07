import math

import numpy as np

from tbot.indicators.candle_indicator import CandleIndicator
from tbot.indicators.qte import GannDir, GannWaves


class HorizontalSR(CandleIndicator):
    """Indicator of horizontal support and resistance lines."""

    NUM_HISTOGRAM_BINS = 100
    MIN_TOUCHES = 2

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()
        self._gann_waves = GannWaves()

    def update(self, series):
        """Update the indicator."""
        # Step 1: Classify all inflection points using gann wave
        # Note: We are going to want to use trend changes instead of gann wave changes,
        # but this is the right idea
        sr_potentials = []
        self._gann_waves.update(series)
        gann_waves = self._gann_waves.last
        for i in range(1, len(gann_waves)):
            wave = gann_waves[i]
            if wave.dir == GannDir.UP:
                sr_potentials.append(wave.low)
            else:
                sr_potentials.append(wave.high)

        # Step 2: Create a histogram of the inflections
        range_min = math.floor(min([c.low for c in series]))
        range_max = math.ceil(max([c.high for c in series]))
        touch_cnt, bins = np.histogram(
            sr_potentials,
            bins=self.NUM_HISTOGRAM_BINS,
            range=(range_min, range_max),
        )

        # Step 3: Filter based on minimum touches to be considered a support or resistance
        s_r = []
        for i in range(len(bins) - 1):
            if touch_cnt[i] >= self.MIN_TOUCHES:
                s_r.append(bins[i])

        self._result.append(s_r)
