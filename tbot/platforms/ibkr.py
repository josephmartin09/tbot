import threading

# import time
from datetime import timedelta
from decimal import Decimal
from queue import Queue
from threading import Event, Thread

from ibapi.client import EClient
from ibapi.common import BarData, TagValueList, TickerId
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

from tbot.util import log

# log.disable_sublogger("ibapi")
LOGGER = log.get_logger()

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


class IBApi(EWrapper, EClient):
    """Class to implement IBApi Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        LOGGER.debug("Initializing IBKR EWrapper and EClient")
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self._queues = {}
        self._reqId = 0
        self._conn_evt = Event()
        self._thr = None

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
        # Some error codes are not errors.
        if errorCode in [2104, 2106, 2107, 2158]:
            return
        LOGGER.error(f"ERR_NO: {errorCode} MSG: {errorString}")

    def connect(self, host, port, clientId):
        """Connect to the IBKR API."""
        LOGGER.debug("Initiating connection to IB Gateway")
        super().connect(host, port, clientId)

        self._conn_evt.clear()
        self._thr = Thread(target=self.run)
        self._thr.start()

        LOGGER.debug("Waiting for connection acknowledgement")
        self._conn_evt.wait()
        LOGGER.debug("Connected to IB Gateway")

    def disconnect(self):
        """Disconnect from the IBKR API."""
        # The ibapi can call disconnect on itself
        if self._thr and self._thr.is_alive():
            if threading.current_thread().ident != self._thr.ident:
                super().disconnect()
                self._thr.join()
            else:
                # Disconnect called from IBKR thread. Doing nothing here prevents
                # race conditions that I'm not willing to debug
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
    def reqContractDetails(self, queue: Queue, contract: Contract):
        """Request full contract details for a contract."""
        reqId = self.nextReqId()
        self._queues[reqId] = queue
        return super().reqContractDetails(reqId, contract)

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from callback."""
        self._queues[reqId].put_nowait(contractDetails)

    # Real-time Bars
    def reqRealTimeBars(
        self,
        queue: Queue,
        contract: Contract,
        barSize: TickerId,
        whatToShow: str,
        useRTH: bool,
        realTimeBarsOptions: TagValueList,
    ):
        """Request real-time bars for a contract."""
        reqId = self.nextReqId()
        self._queues[reqId] = queue
        return super().reqRealTimeBars(
            reqId, contract, barSize, whatToShow, useRTH, realTimeBarsOptions
        )

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
        self._queues[reqId].put_nowait(
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
    # NOTE: We probably want to allow an end date string. It's been removed here
    def reqHistoricalData(
        self,
        queue: Queue,
        contract: Contract,
        period: timedelta,
        useRTH: TickerId,
        keepUpToDate: bool,
    ):
        """Request historical bar data for a contract."""
        reqId = self.nextReqId()
        self._queues[reqId] = queue
        return super().reqHistoricalData(
            reqId,
            contract,
            "",
            lookback[period],
            periods[period],
            "TRADES",
            useRTH,
            2,
            keepUpToDate,
            [],
        )

    def historicalData(self, reqId: TickerId, bar: BarData):
        """Receive initial historical data from callback."""
        self._queues[reqId].put_nowait(bar)

    def historicalDataUpdate(self, reqId: TickerId, bar: BarData):
        """Receive real-time bar updates from callback."""
        self._queues[reqId].put_nowait(bar)
