from datetime import datetime, timedelta

from tbot.indicators.qte import GannABC
from tbot.platforms.yf import yf_get_market_ohlc


def run():
    """Run the example."""
    params = {"symbol": "/NG=F", "timeframe": timedelta(minutes=15)}

    # Download candles from YFinance
    candles = yf_get_market_ohlc(params["symbol"], params["timeframe"], datetime.now())

    # Run an Indicator
    candles.register_indicator("abc", GannABC())
    print(candles.indicators["abc"].last)
