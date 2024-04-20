import queue
import threading
import time

# from datetime import datetime
from decimal import Decimal
from queue import Queue

from ibapi.client import EClient
from ibapi.common import TagValueList, TickAttrib, TickAttribBidAsk, TickerId
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

API_PORT = 4002
CLIENT_ID = 78258


class IBApi(EWrapper, EClient):
    """Class to implement IBApi Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        EClient.__init__(self, self)

        self._queues = {}
        self._reqId = 0

    @property
    def reqId(self):
        """Return the next available request ID."""
        self._reqId += 1
        return self._reqId

    def error(self, reqId, errorCode, errorString, *args):
        """Receive errors from api callback."""
        print(errorCode, errorString)

    def reqContractDetails(self, contract: Contract):
        """Request full contract details for a contract."""
        self._queues["contractDetails"] = Queue()
        super().reqContractDetails(self.reqId, contract)
        return self._queues["contractDetails"]

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from callback."""
        self._queues["contractDetails"].put(contractDetails)

    # reqHistoricalData

    # def historicalData(self, reqId, bar):
    #     """Receive historical data form callback."""
    #     self._queues["historicalData"].put(bar)

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


###
# This works
# app.reqHistoricalData(1, contract, '', '1 D', '1 min', 'TRADES', 0, 2,
#     False, [])
##

app = IBApi()
app.connect("127.0.0.1", API_PORT, CLIENT_ID)

api_thread = threading.Thread(target=app.run)
api_thread.start()

# Need to fix this. This is not production-level
time.sleep(1)

contract = Contract()
contract.symbol = "ES"
contract.secType = "CONTFUT"
contract.currency = "USD"
contract.exchange = "CME"

try:
    print("Loading contract")
    contactDetails = app.reqContractDetails(contract).get(timeout=1.0)
    fullContract = contactDetails.contract
    print(fullContract)

    # print("Requesting Top of Book Quotes")
    # tickQueue = app.reqTickByTickData(fullContract, "BidAsk", 0, False)

    print("Requesting Market data")
    tickQueue = app.reqMktData(fullContract, "375", False, False, [])

    while True:
        try:
            print(tickQueue.get(timeout=0.25))
        except queue.Empty:
            pass

except KeyboardInterrupt:
    pass

except Exception as e:
    print(str(e))

finally:
    app.disconnect()
