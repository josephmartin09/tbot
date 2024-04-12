from datetime import datetime, timedelta

from tbot.indicators.qte import GannAnalysis, GannDir
from tbot.platforms.yf import yf_get_market_ohlc

UP = GannDir.UP
DOWN = GannDir.DOWN

ENABLE_ABCS = False
ENABLE_UTURNS = True


def run():
    """Run the example."""
    params = {"symbol": "/NQ=F", "timeframe": timedelta(minutes=5)}

    # Download candles from YFinance
    candles = yf_get_market_ohlc(params["symbol"], params["timeframe"], datetime.now())

    # Run an Indicator
    candles.register_indicator("gann", GannAnalysis())
    gann_analysis = candles.indicators["gann"].last

    # ABCs
    if ENABLE_ABCS:
        abcs = gann_analysis["abcs"]
        print("ABC LONG")
        for i in range(len(candles)):
            if abcs[i] == DOWN:
                print(candles[i].time)
        print("ABC SHORT")
        for i in range(len(candles)):
            if abcs[i] == UP:
                print(candles[i].time)

    # UTURNs
    if ENABLE_UTURNS:
        uturns = gann_analysis["uturns"]
        for i in range(len(candles)):
            if uturns[i] == UP:
                print(candles[i].time, "UP")
            if uturns[i] == DOWN:
                print(candles[i].time, "DOWN")
