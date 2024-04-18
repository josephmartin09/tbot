import threading
import time
from datetime import datetime
from queue import Queue

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

API_PORT = 4002
CLIENT_ID = 78258


class IBApi(EWrapper, EClient):
    """Example IB Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        EClient.__init__(self, self)
        self._q = Queue()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson):
        """Receive errors from api callback."""
        print(errorCode, errorString)

    def historicalData(self, reqId, bar):
        """Receive historical data form callback."""
        self._q.put(bar)

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from callback."""
        self._q.put(contractDetails)

    def tickByTickBidAsk(
        self, reqId, time, bidPrice, askPrice, bidSize, askSize, tickAttribBidAsk
    ):
        """Receive bid/ask ticks from callback.

        .. note::
            It appears these are aggregated, but I don't know how.
        """
        print(datetime.fromtimestamp(time), bidPrice, bidSize, askPrice, askSize)


app = IBApi()
app.connect("127.0.0.1", API_PORT, CLIENT_ID)

api_thread = threading.Thread(target=app.run)
api_thread.start()

time.sleep(1)

contract = Contract()
# contract.symbol = 'CL'
# contract.secType = 'CONTFUT'
# contract.exchange = 'NYMEX'
# contract.currency = 'USD'

contract.symbol = "NQ"
contract.secType = "CONTFUT"
contract.exchange = "CME"
contract.currency = "USD"

# This works
# app.reqHistoricalData(1, contract, '', '1 D', '1 min', 'TRADES', 0, 2,
#     False, [])

app.reqContractDetails(1, contract)
otherContract = app._q.get().contract
app.reqTickByTickData(3, otherContract, "BidAsk", 0, False)

try:
    while True:
        bar = app._q.get()
        print(f"Time: {datetime.fromtimestamp(int(bar.date))} Close: {bar.close}")

except KeyboardInterrupt:
    pass

app.disconnect()
