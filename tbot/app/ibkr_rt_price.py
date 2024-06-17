from tbot.platforms.ibkr.ibkr import Contract, IBApi
from tbot.platforms.ibkr.queues import QueuePoller, UpdateQueue
from tbot.util import log

IBKR_API_IP = "127.0.0.1"
IBKR_API_PORT = 4002
CLIENT_ID = 78258

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")

EXCHANGE_LOOKUP = {
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
    "YM": "CBOT",
    # Commodities
    "ZC": "CBOT",
    "ZS": "CBOT",
}

# SYMBOLS = list(EXCHANGE_LOOKUP.keys())
SYMBOLS = ["ES"]


class IbkrRtPrice:
    """Class used to load data from the IBKR exchange."""

    def __init__(self, symbols, realtime=True):
        """Initialize the ABCScanner.

        :param list[str] symbols: The names of the continuous futures contracts to scan
        """
        self.ibkr = IBApi()

        self._symbols = symbols
        self._contracts = {}

    def _load_contract_info(self):
        """Load full contract information for the symbols."""
        LOGGER.info("Requesting full contract info for symbols")
        contract_queues = []
        for s in self._symbols:
            # Create a continuous futures contract
            c = Contract()
            c.symbol = s
            c.secType = "CONTFUT"
            c.currency = "USD"
            c.exchange = EXCHANGE_LOOKUP.get(s, "")

            # Request the full contract details for the contract
            q = UpdateQueue()
            contract_queues.append(q)
            self.ibkr.reqContractDetails(q, c)

        # Wait for contract information to be returned
        if not QueuePoller.wait_all(contract_queues, timeout=5):
            raise RuntimeError(f"Failed to load requested contracts {self._symbols}")

        # Update the contracts using the API's contract information
        for q in contract_queues:
            c = q.get_nowait().contract
            c.secType = "FUT"
            self._contracts[c.symbol] = c
            LOGGER.debug(c)
        LOGGER.info("Contract info received")

    def connect(self):
        """Connect to the IBKR API."""
        self.ibkr.connect(IBKR_API_IP, IBKR_API_PORT, CLIENT_ID)

    def disconnect(self):
        """Disconnect from the IBKR API."""
        self.ibkr.disconnect()

    def request_price_feed(self):
        """Request candles for the configured symbols."""
        self._load_contract_info()

        feed_queues = {}
        for symbol, contract in self._contracts.items():
            update_queue = UpdateQueue(key=symbol)
            self.ibkr.reqRealTimeBars(update_queue, contract, "TRADES", False)
            feed_queues[symbol] = update_queue

        return feed_queues
