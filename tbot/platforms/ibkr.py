from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

from datetime import datetime
import threading
import time

API_PORT = 4002
CLIENT_ID = 78258

class IBApi(EWrapper, EClient):
    """Example IB Wrapper."""

    def __init__(self):
        """Initialize the parent IB Classes."""
        EClient.__init__(self, self)

    def historicalData(self, reqId, bar):
        """Call back to receive historical bar data."""
        print(f"Time: {datetime.fromtimestamp(int(bar.date))} Close: {bar.close}")

    def headTimestamp(self, reqId: int, headTimestamp: str):
        """Call back to receive inital timestamp."""
        print("Head timestamp", headTimestamp)

app = IBApi()
app.connect('127.0.0.1', API_PORT, CLIENT_ID)

api_thread = threading.Thread(target=app.run, daemon=True)
api_thread.start()

time.sleep(1)

contract = Contract()
contract.symbol = 'CL'
contract.secType = 'CONTFUT'
contract.exchange = 'NYMEX'
contract.currency = 'USD'

app.reqHistoricalData(1, contract, '', '1 D', '1 min', 'TRADES', 0, 2,
    False, [])
time.sleep(3)
app.disconnect()
