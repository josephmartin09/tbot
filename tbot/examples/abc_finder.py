from datetime import datetime, timedelta

from tbot.indicators.qte import GannABC
from tbot.platforms.yf import yf_get_market_ohlc


def run():
    """Run the example."""
    params = {"symbol": "/ES=F", "timeframe": timedelta(days=1)}

    # Download candles from YFinance
    candles = yf_get_market_ohlc(params["symbol"], params["timeframe"], datetime.now())

    # Run an Indicator
    candles.register_indicator("abc", GannABC())
    for inf in candles.indicators["abc"].last[0:30]:
        print(inf)
