from datetime import datetime, timedelta

from tbot.indicators.qte import GannABC
from tbot.platforms.yf import yf_get_market_ohlc


def run():
    """Run the example."""
    params = {"symbol": "/BTC=F", "timeframe": timedelta(days=1)}

    # Download daily candles to use for support/resistance
    sr_pd = timedelta(days=1)
    candles = yf_get_market_ohlc(params["symbol"], datetime.now(), sr_pd)

    # Download candles for requested timeframe
    candles = yf_get_market_ohlc(params["symbol"], datetime.now(), params["timeframe"])

    # Run an Indicator
    candles.register_indicator("sr", GannABC())
    print(candles.indicators["abc"].last)
