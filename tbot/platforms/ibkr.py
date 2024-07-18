from datetime import datetime
from functools import partial

from ib_insync import IB, ContFuture

from tbot.candles import Candle

CLIENT_ID = 78258
CLIENT_PORT = 4002


class IBWrapper:
    """A wrapper class around ib_insync."""

    period_lookup = {
        "1m": "1 min",
        "2m": "2 mins",
        "3m": "3 mins",
        "5m": "5 mins",
        "10m": "10 mins",
        "15m": "15 mins",
        "30m": "30 mins",
        "1h": "1 hour",
        "4h": "4 hours",
        "1d": "1 day",
        "1w": "1 week",
    }

    lookback = {
        "1m": "1 D",
        "2m": "2 D",
        "3m": "3 D",
        "5m": "5 D",
        "10m": "10 D",
        "15m": "15 D",
        "1h": "60 D",
        "4h": "180 D",
        "1d": "1 Y",
        "1w": "3 Y",
    }

    def __init__(self, mgr):
        """Initialize the IB API.

        :param SymbolManager mgr: A reference to the symbol manager
        """
        self.ib = IB()
        self.ib.connect("127.0.0.1", CLIENT_PORT, clientId=CLIENT_ID, readonly=True)
        self.mgr = mgr

    def disconnect(self):
        """Disconnect from the IB API."""
        self.ib.disconnect()

    def future_lookup(self, symbol, exchange=""):
        """Attempt to lookup the futures contract from symbol.

        :param str symbol: The symbol name
        :param str exchange: The exchange the symbol is listed on
        :rtype: Contract
        """
        details = self.ib.reqContractDetails(
            ContFuture(symbol=symbol, exchange=exchange)
        )[0]
        contract = details.contract
        contract.secType = "FUT"
        return contract

    def historical_data(self, symbol, period, exchange=""):
        """Return historical data for a symbol.

        :param str symbol: The symbol name
        :param CandlePeriod period: The candle period
        :param str exchange: The exchange the symbol is listed on
        :return: A list of candles, in dictionary format
        """
        contract = self.future_lookup(symbol, exchange=exchange)
        candles = []
        pd_str = period.as_str()

        bars = self.ib.reqHistoricalData(
            contract,
            "",
            self.lookback[pd_str],
            self.period_lookup[pd_str],
            "TRADES",
            False,  # useRTH is False to use ETH
            formatDate=1,  # Local Timezone (Use 2 for UTC)
            keepUpToDate=False,
        )

        for b in bars:
            candles.append(
                {
                    "time": b.date.timestamp(),
                    "period": pd_str,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
            )

        return candles

    def on_bar_update(self, symbol, period, bar_list, has_new):
        """Process a bar update from reqHistoricalData streaming."""
        if has_new:
            # This should be what's returned/sent out the door
            last_bar = bar_list[-2]
            candle_raw = {
                "time": last_bar.date.timestamp(),
                "period": period.as_str(),
                "open": last_bar.open,
                "high": last_bar.high,
                "low": last_bar.low,
                "close": last_bar.close,
                "volume": last_bar.volume,
            }

            # I did this in another step because it should move into sym manager
            candle = Candle(
                period,
                datetime.fromtimestamp(candle_raw["time"]),
                candle_raw["open"],
                candle_raw["high"],
                candle_raw["low"],
                candle_raw["close"],
                candle_raw["volume"],
            )
            self.mgr.update_feed(symbol, period, candle)

    def live_data(self, symbol, period, exchange=""):
        """Return historical data for a symbol.

        :param str symbol: The symbol name
        :param CandlePeriod period: The candle period
        :param str exchange: The exchange the symbol is listed on
        :return: A list of candles, in dictionary format
        """
        contract = self.future_lookup(symbol, exchange=exchange)
        candles = []
        pd_str = period.as_str()

        bars = self.ib.reqHistoricalData(
            contract,
            "",
            self.lookback[pd_str],
            self.period_lookup[pd_str],
            "TRADES",
            False,  # useRTH is False to use ETH
            formatDate=1,  # Local Timezone (Use 2 for UTC)
            keepUpToDate=True,
        )

        for b in bars:
            candles.append(
                {
                    "time": b.date.timestamp(),
                    "period": pd_str,
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
            )
        bars.updateEvent += partial(self.on_bar_update, symbol, period)

        return candles

    def event_loop(self):
        """Run the IB event loop to process live data.

        .. note::
            This will block indefinitely
        """
        self.ib.run()
