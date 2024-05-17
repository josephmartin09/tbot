from datetime import datetime, timedelta

from tbot.indicators.qte import GannAnalysis, GannDir
from tbot.platforms.yf import get_market_ohlc

# from tbot.platforms.ibkr.ibkr_working import get_market_ohlc

UP = GannDir.UP
DOWN = GannDir.DOWN

ENABLE_ABCS = False
ENABLE_UTURNS = True


def run():
    """Run the example."""
    params = {"symbol": "/ES=F", "timeframe": timedelta(minutes=5)}

    # Download candles from YFinance
    candles = get_market_ohlc(params["symbol"], params["timeframe"], datetime.now())

    # Run an Indicator
    candles.register_indicator("gann", GannAnalysis())
    print(candles.indicators["gann"].last)
