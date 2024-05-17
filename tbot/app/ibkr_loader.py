import traceback
from datetime import timedelta

from tbot.candles import CandleSeries
from tbot.platforms.ibkr.ibkr import Contract, IBApi
from tbot.platforms.ibkr.queues import CompletionQueue, QueuePoller, UpdateQueue
from tbot.util import log

from .abc_scanner import ABCScanner

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

CANDLE_PERIODS = {
    "1m": timedelta(minutes=1),
    "2m": timedelta(minutes=2),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "10m": timedelta(minutes=10),
    "15m": timedelta(minutes=15),
}


class IbkrLoader:
    """Class used to load data from the IBKR exchange."""

    def __init__(self, symbols):
        """Initialize the ABCScanner.

        :param list[str] symbols: The names of the continuous futures contracts to scan
        """
        self.ibkr = IBApi()

        self._symbols = symbols
        self._contracts = {}
        self._candle_history = {}
        self._candle_current = {}
        self._bar_queues = []
        self._strategys = {}

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
                historical_queue = CompletionQueue(key=queue_key)
                update_queue = UpdateQueue(key=queue_key)
                historical_queues.append(historical_queue)
                update_queues.append(update_queue)

                LOGGER.debug(f"Requesting {queue_key}")
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

        # Save the returned historical bars into a CandleSeries
        for q in historical_queues:
            candle_list = []
            for i in range(q.qsize() - 1):
                candle_list.append(q.get_nowait())

            # Convert the candles to a CandleSeries
            self._candle_history[q.key] = CandleSeries(
                candle_list[0].period, candle_list, len(candle_list)
            )

            # Append the last candle to "forming candles"
            self._candle_current[q.key] = q.get_nowait()

            # Create a strategy
            self._strategys[q.key] = ABCScanner(q.key, self._candle_history[q.key])

        LOGGER.info("Received historical lower timeframe data")

        # Save the real-time queues for further updates
        self._bar_queues = update_queues

    def process_updates(self):
        """Process real-time bars and execute accordingly."""
        strategy_update_keys = []
        rlist = QueuePoller.poll(self._bar_queues)
        if len(rlist) > 0:
            for q in rlist:
                new_candle = q.get_nowait()
                if new_candle.time > self._candle_current[q.key].time:
                    self._candle_history[q.key].append(self._candle_current[q.key])
                    strategy_update_keys.append(q.key)
                self._candle_current[q.key] = new_candle

        return strategy_update_keys

    def execute_strategies(self, update_keys):
        """Execute requested strategies.

        :param list update_keys: A list of keys whose strategies to execute for
        """
        for queue_key in update_keys:
            self._strategys[queue_key].update()

    def run(self):
        """Run the application."""
        try:
            LOGGER.info(f"Running Application with symbols {self._symbols}")

            # Connect to ibkr
            self.ibkr.connect(IBKR_API_IP, IBKR_API_PORT, CLIENT_ID)

            # Request IBKR contracts for symbols
            self.load_contract_info()

            # Request bar data for each contract
            LOGGER.info("Requesting bar data for contracts")
            self.request_candles()

            # Processing real-time updates
            LOGGER.info("Processing real-time bar updates")
            while True:
                strategy_update_keys = self.process_updates()

                self.execute_strategies(strategy_update_keys)

        except KeyboardInterrupt:
            LOGGER.info("Shutdown Requested")

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            self.ibkr.disconnect()
