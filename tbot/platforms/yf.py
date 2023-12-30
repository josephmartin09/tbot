from datetime import datetime, timedelta

import pytz
import yfinance as yf

from tbot.candles import Candle, CandleSeries
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


def yf_get_market_ohlc(symbol, period, end_dt, tz_str="local"):
    """Return YFinance's market OHLC for the symbol.

    :param str symbol: The symbol to request
    :param timedelta period: The candle period
    :param datetime end_dt: The most recent date to receive candles for
    :param str tz_str: String specifying timezone to return data in. Use 'local' for local timezone, or pass a pytz string such as US/Eastern, or UTC

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

    # Strip the timezone, then convert to US/Eastern: YFinance doesn't put a timezone on
    # daily or larger candles
    data = data.tz_localize(None)
    data = data.tz_localize("US/Eastern")
    if tz_str == "local":
        data = data.tz_convert(datetime.astimezone(datetime.now()).tzinfo)
    else:
        data = data.tz_convert(pytz.timezone(tz_str))

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
