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


def yf_get_market_ohlc(symbol, period, end_dt, tz_str=None):
    """Return YFinance's market OHLC for the symbol.

    :param str symbol: The symbol to request
    :param timedelta period: The candle period
    :param datetime end_dt: The most recent date to receive candles for
    :param str tz_str: pytz string specifying timezone to return the data in.  If None, the computer's local timezone will be used

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

    # YFinance doesn't seem to use timezone on daily or larger candles.
    # The workaround is to remove any timezone it returns, then use US/Eastern, which is what yahoo
    # finance website is reporting its intraday data with. Then, the code below will convert from US/Eastern
    # to the requested timezone
    data = data.tz_localize(None)
    if period < timedelta(days=1):
        data = data.tz_localize("US/Eastern")
        if tz_str is None:
            data = data.tz_convert(datetime.astimezone(datetime.now()).tzinfo)
        else:
            data = data.tz_convert(pytz.timezone(tz_str))

    # For daily or longer, we don't want to convert, just apply the requested timezone
    else:
        if tz_str is None:
            data = data.tz_localize(datetime.astimezone(datetime.now()).tzinfo)
        else:
            data = data.tz_localize(pytz.timezone(tz_str))

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
