from datetime import datetime, timedelta

from tbot.indicators.qte import GannABC
from tbot.platforms.yf import yf_get_market_ohlc


def run():
    """Run the example."""
    params = {"symbol": "/ES=F", "timeframe": timedelta(days=1)}

    # Download candles from YFinance
    candles = yf_get_market_ohlc(
        params["symbol"], params["timeframe"], datetime.now(), tz_str="UTC"
    )

    # Run an Indicator
    candles.register_indicator("abc", GannABC())
    print(candles[-1])
