from datetime import datetime, timedelta

from tbot.indicators.qte import GannAnalysis, GannDir
from tbot.platforms.ibkr.ibkr_working import get_market_ohlc

UP = GannDir.UP
DOWN = GannDir.DOWN


def run():
    """Run the example."""
    params = {"symbol": "HG", "timeframe": timedelta(minutes=5)}

    # Download daily candles
    daily_candles = get_market_ohlc(params["symbol"], timedelta(days=1), datetime.now())
    previous_day = daily_candles[-2]
    PDL = previous_day.low
    PDH = previous_day.high

    # Download lower TF candles
    lower_tf_candles = {
        "1m": get_market_ohlc(params["symbol"], timedelta(minutes=1), datetime.now()),
        "2m": get_market_ohlc(params["symbol"], timedelta(minutes=2), datetime.now()),
        "3m": get_market_ohlc(params["symbol"], timedelta(minutes=3), datetime.now()),
        "5m": get_market_ohlc(params["symbol"], timedelta(minutes=5), datetime.now()),
        "10m": get_market_ohlc(params["symbol"], timedelta(minutes=10), datetime.now()),
        "15m": get_market_ohlc(params["symbol"], timedelta(minutes=15), datetime.now()),
    }

    # Run an Indicator
    for tf, candles in lower_tf_candles.items():
        candles.register_indicator("gann", GannAnalysis())

    # Search for break of key level
    for tf, candles in lower_tf_candles.items():
        pdl_break = False
        pdh_break = False
        short_abc = False
        long_abc = False

        for i in range(len(candles)):
            c = candles[i]
            # Search for break of daily level
            if c.time >= (
                previous_day.time + timedelta(hours=19)
            ):  # Need custom lookback
                if (not pdh_break) and (c.high > PDH):
                    pdh_break = True
                    if tf == "1m":
                        print("PDH Break", c.time)

                if (not pdl_break) and (c.low < PDL):
                    pdl_break = True
                    if tf == "1m":
                        print("PDL Break", c.time)

                if (pdl_break) and (not short_abc):
                    if candles.indicators["gann"].last["abcs"][i] == UP:
                        short_abc = True
                        print(tf, "ABC SHORT", c.time)

                if (pdh_break) and (not long_abc):
                    if candles.indicators["gann"].last["abcs"][i] == DOWN:
                        long_abc = True
                        print(tf, "ABC LONG", c.time)
