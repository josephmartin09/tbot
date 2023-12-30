from datetime import datetime, timedelta

import pytz
import yfinance as yf

from tbot.candles import Candle, CandleSeries
from tbot.indicators.sr import HorizontalSR
from tbot.util import log

log.disable_sublogger("yfinance")
log.disable_sublogger("peewee")

periods = {
    timedelta(minutes=1): "1m",
    timedelta(minutes=5): "5m",
    timedelta(minutes=15): "15m",
    timedelta(hours=1): "1h",
    timedelta(days=1): "1d",
    timedelta(weeks=1): "1wk",
}

times = {}
for k, v in periods.items():
    times[v] = k


def yf_get_market_ohlc(symbol, end_dt, period):
    """Return YFinance's market OHLC for the symbol.

    :param str symbol: The symbol to request
    :param datetime end_dt: The most recent date to receive candles for
    :param timedelta period: The candle period

    .. note::
        The start of the series is determined by the candle period. The lookback table is defined as follows

    .. code-block::

        lookback = {
            timedelta(minutes=1): timedelta(days=1),
            timedelta(minutes=5): timedelta(days=5),
            timedelta(minutes=15): timedelta(days=5),
            timedelta(hours=1): timedelta(days=20),
            timedelta(days=1): timedelta(days=365),
            timedelta(weeks=1): timedelta(days=3 * 365),
        }

    """
    lookback = {
        timedelta(minutes=1): timedelta(days=1),
        timedelta(minutes=5): timedelta(days=5),
        timedelta(minutes=15): timedelta(days=5),
        timedelta(hours=1): timedelta(days=20),
        timedelta(days=1): timedelta(days=365),
        timedelta(weeks=1): timedelta(days=3 * 365),
    }

    # Download hourly candles from yfinance
    end_dt += timedelta(days=1)
    data = yf.download(
        [symbol],
        interval=periods[period],
        start=(end_dt - lookback[period]).date(),
        end=(end_dt.date()),
    )

    # Strip the timezone, then convert to US/Eastern which is the timezone used by yfinance
    # This is done because for some reason yfinance returns inconsistent timezone
    # information.
    data = data.tz_localize(None)
    data = data.tz_localize(pytz.timezone("US/Eastern"))
    # Use TZ Convert to get the data back in the user's local timezone
    data = data.tz_convert(datetime.astimezone(datetime.now()).tzinfo)

    # Convert to the candles data structure
    candles = []
    for index, row in data.iterrows():
        candles.append(
            Candle(
                period,
                index.to_pydatetime(),
                row["Open"],
                row["High"],
                row["Low"],
                row["Close"],
                row["Volume"],
            )
        )
    return CandleSeries(period, candles, len(candles))


def run():
    """Run the example."""
    params = {"symbol": "/BTC=F", "timeframe": "1d"}

    # Download daily candles to use for support/resistance
    sr_pd = timedelta(days=1)
    candles = yf_get_market_ohlc(params["symbol"], datetime.now(), sr_pd)

    # Download candles for requested timeframe
    candles = yf_get_market_ohlc(
        params["symbol"], datetime.now(), times[params["timeframe"]]
    )

    # Run an Indicator
    candles.register_indicator("horiztonal_sr", HorizontalSR())
    print(candles.indicators["horiztonal_sr"].last)
