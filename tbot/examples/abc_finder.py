from datetime import datetime, timedelta

from tbot.indicators.qte import GannAnalysis
from tbot.platforms.yf import yf_get_market_ohlc


def run():
    """Run the example."""
    params = {"symbol": "/NQ=F", "timeframe": timedelta(minutes=15)}

    # Download candles from YFinance
    candles = yf_get_market_ohlc(params["symbol"], params["timeframe"], datetime.now())

    # Run an Indicator
    candles.register_indicator("abc", GannAnalysis())

    # Print
    abcs = candles.indicators["abc"].last["abcs"]

    for i in range(len(candles)):
        print(candles[i].time, abcs[i])
