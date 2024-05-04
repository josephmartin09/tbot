import queue
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
from queue import Queue
from threading import Event

from ibapi.client import EClient
from ibapi.common import BarData, TagValueList, TickAttrib, TickAttribBidAsk, TickerId
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

from tbot.candles import Candle, CandleSeries

API_PORT = 4002
CLIENT_ID = 78258

periods = {
    timedelta(minutes=1): "1 min",
    timedelta(minutes=2): "2 mins",
    timedelta(minutes=3): "3 mins",
    timedelta(minutes=5): "5 mins",
    timedelta(minutes=10): "10 mins",
    timedelta(minutes=15): "15 mins",
    timedelta(hours=1): "1 hour",
    timedelta(days=1): "1 day",
    timedelta(weeks=1): "1 week",
}

lookback = {
    timedelta(minutes=1): "1 D",
    timedelta(minutes=2): "2 D",
    timedelta(minutes=3): "3 D",
    timedelta(minutes=5): "5 D",
    timedelta(minutes=10): "10 D",
    timedelta(minutes=15): "2 W",
    timedelta(hours=1): "3 W",
    timedelta(days=1): "2 M",
    timedelta(weeks=1): "6 M",
}

cached_contracts = {""}


class IBApi(EWrapper, EClient):
    """Class to implement IBApi Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        EClient.__init__(self, self)

        self._queues = {}
        self._reqId = 0
        self._connect_evt = Event()

    @property
    def reqId(self):
        """Return the next available request ID."""
        self._reqId += 1
        return self._reqId

    def error(self, reqId, errorCode, errorString, *args):
        """Receive errors from api callback."""
        print(errorCode, errorString)

    def nextValidId(self, nextValidId):
        """Receive connection validation.

        .. note::
            For now, it's being used to indicate connection success
        """
        print("CONNECTION SUCCESS")
        self._reqId = nextValidId

    def reqContractDetails(self, contract: Contract):
        """Request full contract details for a contract."""
        self._queues["contractDetails"] = Queue()
        super().reqContractDetails(self.reqId, contract)
        return self._queues["contractDetails"]

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from callback."""
        self._queues["contractDetails"].put(contractDetails)

    def reqHistoricalData(
        self,
        contract: Contract,
        endDateTime: str,
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: TickerId,
        formatDate: TickerId,
        keepUpToDate: bool,
        chartOptions: TagValueList,
    ):
        """Request historical bar data for a contract."""
        self._queues["historicalData"] = Queue()
        super().reqHistoricalData(
            self.reqId,
            contract,
            endDateTime,
            durationStr,
            barSizeSetting,
            whatToShow,
            useRTH,
            formatDate,
            keepUpToDate,
            chartOptions,
        )
        return self._queues["historicalData"]

    def historicalData(self, reqId: TickerId, bar: BarData):
        """Receive historical data form callback."""
        super().historicalData(reqId, bar)
        self._queues["historicalData"].put(bar)

    def reqTickByTickData(
        self,
        contract: Contract,
        tickType: str,
        numberOfTicks: TickerId,
        ignoreSize: bool,
    ):
        """Request bid/ask quotes."""
        self._queues["tickData"] = Queue()
        super().reqTickByTickData(
            self.reqId, contract, tickType, numberOfTicks, ignoreSize
        )
        return self._queues["tickData"]

    def tickByTickBidAsk(
        self,
        reqId: TickerId,
        time: TickerId,
        bidPrice: float,
        askPrice: float,
        bidSize: Decimal,
        askSize: Decimal,
        tickAttribBidAsk: TickAttribBidAsk,
    ):
        """Receive bid/ask quotes from callback.

        .. note::
            This is what I originally called "quote".  It's the most recent bid/ask after a transaction took
            place.
        """
        self._queues["tickData"].put(
            {
                "time": time,
                "bidPrice": bidPrice,
                "askPrice": askPrice,
                "bidSize": bidSize,
                "askSize": askSize,
                "tickAttribBidAsk": tickAttribBidAsk,
            }
        )

    def reqMktData(
        self,
        contract: Contract,
        genericTickList: str,
        snapshot: bool,
        regulatorySnapshot: bool,
        mktDataOptions: TagValueList,
    ):
        """Request tick data for a contract."""
        print(
            "WARNING: Ignoring snapshot and regulatorySnapshot parameters to avoid paying for snapshots."
        )
        self._queues["mktData"] = Queue()
        super().reqMktData(
            self.reqId, contract, genericTickList, False, False, mktDataOptions
        )
        return self._queues["mktData"]

    def tickPrice(
        self, reqId: TickerId, tickType: TickerId, price: float, attrib: TickAttrib
    ):
        """Receive price ticks from the market data feed.

        .. note::
            Please see https://ibkrcampus.com/ibkr-api-page/twsapi-doc/#available-tick-types
        """
        if tickType == 1:
            self._queues["mktData"].put(
                {"tickType": tickType, "price": price, "attrib": attrib, "dir": "BID"}
            )
        elif tickType == 2:
            self._queues["mktData"].put(
                {"tickType": tickType, "price": price, "attrib": attrib, "dir": "ASK"}
            )

    def tickSize(self, reqId: TickerId, tickType: TickerId, size: Decimal):
        """Receive size ticks from the market data feed."""
        if tickType == 86:
            self._queues["mktData"].put({"tickType": tickType, "size": size})

    def tickGeneric(self, reqId: TickerId, tickType: TickerId, value: float):
        """Receive generic ticks from the market data feed."""
        self._queues["mktData"].put({"tickType": tickType, "value": value})

    def tickString(self, reqId: TickerId, tickType: TickerId, value: str):
        """Receive string ticks from the market data feed."""
        # These are most recent T&S tick
        if tickType == 48 or tickType == 77:
            self._queues["mktData"].put({"tickType": tickType, "value": value})


def get_market_ohlc(symbol, period, end_dt, tz_str=None):
    """Return YFinance's market OHLC for the symbol.

    :param str symbol: The symbol to request
    :param timedelta period: The candle period
    :param datetime end_dt: The most recent date to receive candles for
    :param str tz_str: pytz string specifying timezone to return the data in.  If None, the computer's local timezone will be used

    .. note::
        The start of the series is determined by the candle period. The lookback table is defined as follows

    .. code-block::

        lookback = {
            timedelta(minutes=1): "1 D",
            timedelta(minutes=2): "2 D",
            timedelta(minutes=3): "3 D",
            timedelta(minutes=5): "5 D",
            timedelta(minutes=10): "10 D",
            timedelta(minutes=15): "2 W",
            timedelta(hours=1): "3 W",
            timedelta(days=1): "2 M",
            timedelta(weeks=1): "6 M",
        }
    """
    app = IBApi()
    app.connect("127.0.0.1", API_PORT, CLIENT_ID)

    api_thread = threading.Thread(target=app.run)
    api_thread.start()

    # How to get rid of this sleep?
    time.sleep(1)

    bars = list()
    try:
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "CONTFUT"
        contract.currency = "USD"
        contract.exchange = "COMEX"

        print("Loading contract")
        fullContract = app.reqContractDetails(contract).get(timeout=1.0).contract
        print(fullContract)

        print("Loading Historical Data")
        # Am I supposed to give a endDate to know when to stop parsing?  That seems to be the "right" way
        respQueue = app.reqHistoricalData(
            fullContract,
            "",
            lookback[period],
            periods[period],
            "TRADES",
            0,
            2,
            False,
            [],
        )
        while True:
            try:
                bars.append(respQueue.get(timeout=0.25))
            except queue.Empty:
                if len(bars) > 0:
                    break

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(str(e))

    finally:
        app.disconnect()

        if len(bars) == 0:
            return []

        candles = []
        for b in bars:
            bartime = None
            if period >= timedelta(days=1):
                bartime = datetime.strptime(b.date, "%Y%m%d").astimezone(tz_str)
            else:
                bartime = datetime.fromtimestamp(int(b.date)).astimezone(tz_str)
            candles.append(
                Candle(
                    period,
                    bartime,
                    float(b.open),
                    float(b.high),
                    float(b.low),
                    float(b.close),
                    float(b.volume),
                )
            )
        return CandleSeries(period, candles, len(candles))


# # Stuff I need eventually
# print("Requesting Top of Book Quotes")
# tickQueue = app.reqTickByTickData(fullContract, "BidAsk", 0, False)

# print("Requesting Market data")
# tickQueue = app.reqMktData(fullContract, "375", False, False, [])

# while True:
#     try:
#         print(tickQueue.get(timeout=0.25))
#     except queue.Empty:
#         pass
