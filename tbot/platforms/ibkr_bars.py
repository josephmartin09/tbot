# import queue
import threading

# import time
from datetime import datetime, timedelta
from decimal import Decimal
from queue import Queue
from threading import Event, Thread

from ibapi.client import EClient
from ibapi.common import BarData, TagValueList, TickerId
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

from tbot.candles import Candle

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

exchange_lookup = {
    # Metals
    "HG": "COMEX",
    "SI": "COMEX",
    "GC": "COMEX",
    # Energy
    "CL": "NYMEX",
    "NG": "NYMEX",
    # Indices
    "ES": "CME",
    "NQ": "CME",
    "RTY": "CME",
    "YM": "CME",
    "VX": "CME",
    # Commodities
    "ZC": "CBOT",
    "ZS": "CBOT",
}


class IBApi(EWrapper, EClient):
    """Class to implement IBApi Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self._queues = {}
        self._reqId = 0
        self._conn_evt = Event()
        self._thr = None

    def _add_queue(self, reqId):
        self._queues[reqId] = Queue()

    def nextReqId(self):
        """Return the next available request ID."""
        currReqId = self._reqId
        self._reqId += 1
        return currReqId

    def error(
        self,
        reqId: TickerId,
        errorCode: TickerId,
        errorString: str,
        advancedOrderRejectJson="",
    ):
        """Receive errors from api callback."""
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)

    def connect(self, host, port, clientId):
        """Connect to the IBKR API."""
        super().connect(host, port, clientId)

        self._conn_evt.clear()
        self._thr = Thread(target=self.run)
        self._thr.start()
        self._conn_evt.wait()

    def disconnect(self):
        """Disconnect from the IBKR API."""
        # The ibapi can call disconnect on itself
        if self._thr and self._thr.is_alive():
            if threading.current_thread().ident != self._thr.ident:
                super().disconnect()
                self._thr.join()
            else:
                # Remote disconnect
                pass

    def nextValidId(self, nextValidId):
        """Receive connection validation.

        .. note::
            For now, it's being used to indicate connection success
        """
        self._reqId = nextValidId
        if not self._conn_evt.is_set():
            self._conn_evt.set()

    # Contract and Contract Search
    def reqContractDetails(self, contract: Contract):
        """Request full contract details for a contract."""
        reqId = self.nextReqId()
        self._add_queue(reqId)
        super().reqContractDetails(reqId, contract)
        return self._queues[reqId]

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from callback."""
        self._queues[reqId].put(contractDetails)

    def reqContractFromSymbol(self, symbol, exchange=None):
        """Retrieve a Contract from a symbol.

        :param str symbol: The symbol to attempt to retreive a contract for
        :param str exchange: The exchange the symbol is managed by.  If left as None, a best guess will be attempted
        """
        # First, request the continuous futures contract details
        contContract = Contract()
        contContract.symbol = symbol
        contContract.secType = "CONTFUT"
        contContract.currency = "USD"

        # If the user supplies an exchange, use that
        if exchange is not None:
            contContract.exchange = exchange

        # If not, try to look it up from well-known list
        else:
            contContract.exchange = exchange_lookup.get(symbol, "")
            if contContract.exchange == "":
                print("WARNING: Exchange field unknown. ibapi will try to guess")
        contractDetails = app.reqContractDetails(contContract).get()

        # Docs seem to imply real time bars need FUT instead of CONTFUT.
        contractDetails.contract.secType = "FUT"

        return contractDetails.contract

    # Real-time Bars
    def reqRealTimeBars(
        self,
        contract: Contract,
        barSize: TickerId,
        whatToShow: str,
        useRTH: bool,
        realTimeBarsOptions: TagValueList,
    ):
        """Request Real-Time bars for a contract."""
        reqId = self.nextReqId()
        self._add_queue(reqId)
        super().reqRealTimeBars(
            reqId, contract, barSize, whatToShow, useRTH, realTimeBarsOptions
        )
        return self._queues[reqId]

    def realtimeBar(
        self,
        reqId: TickerId,
        time: TickerId,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: Decimal,
        wap: Decimal,
        count: TickerId,
    ):
        """Receive a real-time bar."""
        self._queues[reqId].put(
            {
                "time": time,
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "wap": wap,
                "count": count,
            }
        )

    # Historical Bars
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
        reqId = self.nextReqId()
        self._add_queue(reqId)
        super().reqHistoricalData(
            reqId,
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
        return self._queues[reqId]

    def historicalData(self, reqId: TickerId, bar: BarData):
        """Receive initial historical data from callback."""
        self._queues[reqId].put(bar)

    def historicalDataUpdate(self, reqId: TickerId, bar: BarData):
        """Receive real-time bar updates from callback."""
        self._queues[reqId].put(bar)


if __name__ == "__main__":
    try:
        app = IBApi()
        app.connect("127.0.0.1", API_PORT, CLIENT_ID)

        # Load a contract
        contract = app.reqContractFromSymbol("NG")
        print(contract)

        # Receive real-time bars
        period = timedelta(days=1)
        barQueue = app.reqHistoricalData(
            contract,
            "",
            lookback[period],
            periods[period],
            "TRADES",
            0,  # Use ETH (0) or RTH (1)
            2,  # Receive UNIX timestamp
            True,  # Stream real-time bars after historical data
            [],
        )
        while True:
            b = barQueue.get()
            bartime = None
            if period >= timedelta(days=1):
                bartime = datetime.strptime(b.date, "%Y%m%d").astimezone()
            else:
                bartime = datetime.fromtimestamp(int(b.date)).astimezone()
            print(
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

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(e)

    finally:
        app.disconnect()
