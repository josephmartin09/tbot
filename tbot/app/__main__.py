import traceback
from datetime import timedelta

from tbot.candles import CandleSeries
from tbot.platforms.ibkr.ibkr import Contract, IBApi
from tbot.platforms.ibkr.queues import CompletionQueue, QueuePoller, UpdateQueue
from tbot.util import log

API_PORT = 4002
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
SYMBOLS = ["CL", "GC"]

CANDLE_PERIODS = {
    "1m": timedelta(minutes=1),
    "2m": timedelta(minutes=2),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "10m": timedelta(minutes=10),
    "15m": timedelta(minutes=15),
}


class ABCScanner:
    """Application to scan for ABCs at a key level."""

    def __init__(self, symbols):
        """Initialize the ABCScanner.

        :param list[str] symbols: The names of the continuous futures contracts to scan
        """
        self._symbols = symbols
        self._contracts = {}
        self._candles = {}
        self._bar_queues = []
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
            for period_str, period in CANDLE_PERIODS.items():
                queue_key = f"{s}-{period_str}"
                LOGGER.debug(f"Requesting {queue_key}")
                historical_queue = CompletionQueue(key=queue_key)
                update_queue = UpdateQueue(key=queue_key)
                historical_queues.append(historical_queue)
                update_queues.append(update_queue)
                self.ibkr.reqHistoricalData(
                    historical_queue,
                    update_queue,
                    self._contracts[s],
                    period,
                    False,
                    True,
                )

        # Wait for initial historical data to be returned
        LOGGER.info(
            "Waiting for historical lower timeframe data (this could take a very long time)"
        )
        if not QueuePoller.wait_all(historical_queues, timeout=300):
            raise RuntimeError("Failed to load historical data for all Candles")
        for q in historical_queues:
            candle_list = []
            # Convert each IBKR bar to a candle
            for i in range(q.qsize()):
                candle_list.append(q.get_nowait())

            # Convert the candles to a CandleSeries
            self._candles[q.key] = CandleSeries(
                candle_list[0].period, candle_list, len(candle_list)
            )
        LOGGER.info("Received historical lower timeframe data")

        # Save the real-time queues for further updates
        self._bar_queues = update_queues

    def process_updates(self):
        """Process real-time bars and execute accordingly."""
        while True:
            rlist = QueuePoller.poll(self._bar_queues)
            for q in rlist:
                LOGGER.info(f"{q.key} {q.get_nowait()}")

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

            # Processing real-time updates
            LOGGER.info("Processing real-time bar updates")
            self.process_updates()

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
