import traceback
from datetime import timedelta

from tbot.candles import CandleSeries
from tbot.platforms.ibkr.ibkr import Contract, IBApi
from tbot.platforms.ibkr.queues import CompletionQueue, QueuePoller, UpdateQueue
from tbot.util import log

API_PORT = 4002
CLIENT_ID = 78258

LOGGER = log.get_logger()

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

# SYMBOLS = ["ES", "NQ", "RTY", "YM", "HG", "GC", "CL"]
SYMBOLS = list(EXCHANGE_LOOKUP.keys())
SYMBOLS = ["ES"]

CANDLE_PERIODS = [
    timedelta(minutes=1),
    timedelta(minutes=2),
    timedelta(minutes=3),
    timedelta(minutes=5),
    timedelta(minutes=10),
    timedelta(minutes=15),
]


class ABCScanner:
    """Application to scan for ABCs at a key level."""

    def __init__(self, symbols):
        """Initialize the ABCScanner.

        :param list[str] symbols: The names of the continuous futures contracts to scan
        """
        self._symbols = symbols
        self._contracts = {}
        for s in self._symbols:
            self._contracts[s] = None

        self.ibkr = IBApi()

    def load_contract_info(self):
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

    def request_candles(self):
        """Request candles for the configured symbols."""
        # Iterate over each symbol and request lower timeframe data
        LOGGER.info("Requesting historical lower timeframe data")
        historical_queues = []
        update_queues = []
        for s in self._symbols:
            historical_queue = CompletionQueue(key=f"{s}-1m")
            update_queue = UpdateQueue(f"{s}-1m")
            historical_queues.append(historical_queue)
            update_queues.append(update_queue)
            self.ibkr.reqHistoricalData(
                historical_queue,
                update_queue,
                self._contracts[s],
                timedelta(minutes=1),
                False,
                True,
            )

        # Wait for initial historical data to be returned
        LOGGER.info("Waiting for historical lower timeframe data")
        QueuePoller.wait_all(historical_queues)
        candles = {}
        for q in historical_queues:
            candle_list = []
            # Convert each IBKR bar to a candle
            for i in range(q.qsize()):
                candle_list.append(q.get_nowait())

            # Convert the candles to a CandleSeries
            candles[q.key] = CandleSeries(
                timedelta(minutes=1), candle_list, len(candle_list)
            )
            for c in candles[q.key]:
                print(c)
        LOGGER.info("Received historical lower timeframe data")

    def run(self):
        """Run the application."""
        try:
            LOGGER.info(f"Running Application with symbols {self._symbols}")

            # Connect to ibkr
            self.ibkr.connect("127.0.0.1", API_PORT, CLIENT_ID)

            # Request IBKR contracts for symbols
            self.load_contract_info()

            # Request bar data for each contract
            LOGGER.info("Requesting bar data for contracts")
            self.request_candles()

        except KeyboardInterrupt:
            LOGGER.info("Shutdown Requested")

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            self.ibkr.disconnect()


if __name__ == "__main__":
    log.setup_logging()

    app = ABCScanner(SYMBOLS)
    app.run()
