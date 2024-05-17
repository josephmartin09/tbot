from collections import namedtuple

from tbot.indicators.candle_indicator import CandleIndicator

from .gann_dir import GannDir

Leg = namedtuple("Leg", ["dir", "start_ind", "end_ind", "low", "high"])


class GannAnalysis(CandleIndicator):
    """Indicator to perform Gann Bar Counting, Leg Analysis, and ABC Detection using the methods on the Quant Trade Edge Channel."""

    HOAGIE_MIN_INSIDE_BARS = 2

    def __init__(self):
        """Initialize the indicator."""
        super().__init__()

    @classmethod
    def _calc_dirs(cls, series):
        """Calculate the bar directions of each candle using the Gann With Hoagie bar counting method.

        :returns: A list of bar directions
        """
        bar_dirs = []
        hoagie_active = False
        hoagie_candle = None

        # Label the first direction based on close direction
        if series[0].open < series[0].close:
            bar_dirs.append(GannDir.UP)
        else:
            bar_dirs.append(GannDir.DOWN)

        # Determine Gann Bar Directions
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]

            if not hoagie_active:
                # Up bar
                if (curr.high > prev.high) and (curr.low > prev.low):
                    bar_dirs.append(GannDir.UP)

                # Down bar
                elif (curr.low < prev.low) and (curr.high < prev.high):
                    bar_dirs.append(GannDir.DOWN)

                # Inside bar: For non-hoagies, an inside bar is strictly smaller than the previous bar
                elif (curr.high < prev.high) and (curr.low > prev.low):
                    bar_dirs.append(bar_dirs[-1])
                    hoagie_active = True
                    hoagie_candle = prev

                # Outside bar
                else:
                    bar_dirs.append(bar_dirs[-1])

            # We're within a potential Hoagie
            else:
                # Up bar
                if (curr.high > hoagie_candle.high) and (curr.low > hoagie_candle.low):
                    bar_dirs.append(GannDir.UP)
                    hoagie_active = False
                    hoagie_candle = None

                # Down bar
                elif (curr.low < hoagie_candle.low) and (
                    curr.high < hoagie_candle.high
                ):
                    bar_dirs.append(GannDir.DOWN)
                    hoagie_active = False
                    hoagie_candle = None

                # Inside bar: For hoagies, a same size bar doesn't break the hoagie. To account for this, count it as an inside bar
                elif (curr.high <= hoagie_candle.high) and (
                    curr.low >= hoagie_candle.low
                ):
                    bar_dirs.append(bar_dirs[-1])

                # Outside bar
                else:
                    bar_dirs.append(bar_dirs[-1])
                    hoagie_active = False
                    hoagie_candle = None

        return bar_dirs

    @classmethod
    def _calc_legs(cls, series, bar_dirs):
        """Calculate the leg directions using bar directions as input.

        :returns: A list of leg directions
        """

        def new_leg():
            return {
                "dir": None,
                "start": None,
                "end": None,
                "high": None,
                "low": None,
            }

        legs = []

        # The first leg gets the direction of the first bar
        curr_leg = new_leg()
        curr_leg["dir"] = bar_dirs[0]
        curr_leg["start"] = 0
        curr_leg["end"] = 0
        curr_leg["high"] = series[0].high
        curr_leg["low"] = series[0].low

        # Calculate the rest of the legs by anaylzing changes in bar direction
        for i in range(1, len(bar_dirs)):
            bar_dir = bar_dirs[i]

            # If we discover a change in bar direction, save the current leg as it's done
            if bar_dir != curr_leg["dir"]:
                legs.append(curr_leg)

                # Start the next leg from the end of the current one
                prev_leg = curr_leg
                curr_leg = new_leg()
                curr_leg["dir"] = bar_dir
                curr_leg["start"] = prev_leg["end"]
                curr_leg["end"] = i
                if curr_leg["dir"] == GannDir.UP:
                    curr_leg["low"] = prev_leg["low"]
                    curr_leg["high"] = series[i].high
                else:
                    curr_leg["low"] = series[i].low
                    curr_leg["high"] = prev_leg["high"]

            # Check the current bar to see if it's a new maximum or minimum of the leg
            if bar_dir == GannDir.UP:
                if series[i].high > curr_leg["high"]:
                    curr_leg["high"] = series[i].high
                    curr_leg["end"] = i
            else:
                if series[i].low < curr_leg["low"]:
                    curr_leg["low"] = series[i].low
                    curr_leg["end"] = i

        return legs

    @classmethod
    def _calc_abcs(cls, series, legs):
        abc_up_inds = []
        abc_down_inds = []
        if len(legs) > 2:
            for i in range(2, len(legs)):
                A = legs[i - 2]
                B = legs[i - 1]
                C = legs[i]

                # ABC Up
                if C["dir"] == GannDir.UP:
                    if (A["low"] < B["low"]) and (B["high"] < C["high"]):
                        abc_up_inds.append(C["end"])

                # ABC Down
                else:
                    if (A["high"] > B["high"]) and (B["low"] > C["low"]):
                        abc_down_inds.append(C["end"])

        # Flatten ABC locations into an array the same size as the data series
        abcs = [None] * len(series)
        for ind in abc_up_inds:
            abcs[ind] = GannDir.UP
        for ind in abc_down_inds:
            abcs[ind] = GannDir.DOWN
        return abcs

    @classmethod
    def _calc_uturns(cls, series, legs):
        uturn_up_inds = []
        uturn_down_inds = []

        crit_high = None
        crit_low = None
        curr_trend = None
        if legs[0]["dir"] == GannDir.UP:
            curr_trend = GannDir.UP
        else:
            curr_trend = GannDir.DOWN
        crit_high = legs[0]["high"]
        crit_low = legs[0]["low"]
        uturn_level = None

        # Search for uturns with the rest of the legs.
        for i in range(1, len(legs)):
            curr_leg = legs[i]
            if uturn_level is None:
                # In an UP trend, look for a lower-low to set the uturn level
                if curr_trend == GannDir.UP:
                    # Current leg is UP, check for trend continuation
                    if curr_leg["dir"] == GannDir.UP:
                        if curr_leg["high"] >= crit_high:
                            # Higher High
                            crit_high = curr_leg["high"]
                        else:
                            # Lower High
                            pass

                    # Current leg is DOWN, check for initial UTURN level
                    else:
                        if curr_leg["low"] >= crit_low:
                            # Higher Low
                            crit_low = curr_leg["low"]
                        else:
                            # Lower Low
                            uturn_level = curr_leg["low"]

                # In a DOWN trend, look for a higher high to set the uturn level
                else:
                    # Current leg is DOWN, check for trend continuation
                    if curr_leg["dir"] == GannDir.DOWN:
                        if curr_leg["low"] <= crit_low:
                            # Lower Low
                            crit_low = curr_leg["low"]
                        else:
                            # Higher Low
                            pass

                    # Current leg is UP, check for initial UTURN level
                    else:
                        if curr_leg["high"] <= crit_high:
                            crit_high = curr_leg["high"]
                        else:
                            uturn_level = curr_leg["high"]

            # We have a pending UTURN
            else:
                if curr_trend == GannDir.UP:
                    # Current leg is UP, check for trend continuation
                    if curr_leg["dir"] == GannDir.UP:
                        if curr_leg["high"] >= crit_high:
                            # Higher High
                            crit_high = curr_leg["high"]
                            uturn_level = None

                    # Current leg is DOWN, check for confirmed UTURN
                    else:
                        if curr_leg["low"] < uturn_level:
                            # UTURN DOWN
                            uturn_down_inds.append(curr_leg["end"])
                            crit_low = curr_leg["low"]
                            crit_high = curr_leg["high"]
                            uturn_level = None
                            curr_trend = GannDir.DOWN
                else:
                    # Current leg is DOWN, check for trend continuation
                    if curr_leg["dir"] == GannDir.DOWN:
                        if curr_leg["low"] <= crit_low:
                            # Lower Low
                            crit_low = curr_leg["low"]
                            uturn_level = None

                    # Current leg is UP, check for confirmed UTURN
                    else:
                        if curr_leg["high"] > uturn_level:
                            # UTURN UP
                            uturn_up_inds.append(curr_leg["end"])
                            crit_low = curr_leg["low"]
                            crit_high = curr_leg["high"]
                            uturn_level = None
                            curr_trend = GannDir.UP

        # Flatten uturn locations into an array the same size as the data series
        uturns = [None] * len(series)
        for ind in uturn_up_inds:
            uturns[ind] = GannDir.UP
        for ind in uturn_down_inds:
            uturns[ind] = GannDir.DOWN
        return uturns

    def update(self, series):
        """Calculate the result of the indicator on the series, then save the result.

        :param CandleSeries series: The series to perform the calculation on
        """
        bar_dirs = self._calc_dirs(series)
        legs = self._calc_legs(series, bar_dirs)
        abcs = self._calc_abcs(series, legs)
        uturns = self._calc_uturns(series, legs)

        result = []
        for i in range(len(bar_dirs)):
            result.append({"bar": bar_dirs[i], "abc": abcs[i], "uturns": uturns[i]})

        return result
