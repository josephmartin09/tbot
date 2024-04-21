from datetime import datetime, timedelta

import pytz
import yfinance as yf
from flask import Flask, jsonify, request

from tbot.candles import Candle, CandleSeries
from tbot.indicators.sr import HorizontalSR
from tbot.util import log

log.disable_sublogger("yfinance")
log.disable_sublogger("peewee")

app = Flask(__name__)

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


def get_market_ohlc(symbol, end_dt, period):
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

    # Strip the timezone, then convert back to UTC.
    # This is done because for some reason yfinance returns inconsistent timezone
    # information.
    data = data.tz_localize(None)
    data = data.tz_localize(pytz.timezone("US/Eastern"))

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
    """Start the Flask API web server."""
    app.run(host="localhost", port=8081, debug=True)


@app.route("/")
def root():
    """Root API route."""
    return jsonify({"msg": "Hello API"})


@app.route("/trade", methods=["POST"])
def trade():
    """Trade API route."""
    params = request.json

    # Download daily candles to use for support/resistance
    sr_pd = timedelta(days=1)
    candles_sr = get_market_ohlc(params["symbol"], datetime.now(), sr_pd)

    # Download candles for requested timeframe
    candles_req = get_market_ohlc(
        params["symbol"], datetime.now(), times[params["timeframe"]]
    )
    candles_req_chart = []
    for c in candles_req:
        candles_req_chart.append(
            {
                # Note that lightweight charts needs the utc offset to correctly display time
                "time": c.time.timestamp() + c.time.utcoffset().total_seconds(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
            }
        )

    # Calculate Support/Resistance, keeping lines only visible in the requested timeframe
    candles_sr.register_indicator("s_r", HorizontalSR())
    s_r = []
    filter_min = min([c.low for c in candles_req])
    filter_max = max([c.high for c in candles_req])
    filter_min -= 0.01 * filter_min
    filter_max += 0.01 * filter_max
    for sr_line in candles_sr.indicators["s_r"].last:
        if sr_line >= filter_min and sr_line <= filter_max:
            s_r.append(sr_line)

    # Construct response
    resp = {"candles": candles_req_chart, "s_r": s_r}

    return jsonify(resp)
