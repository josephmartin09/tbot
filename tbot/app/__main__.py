import queue
import traceback
from datetime import datetime, timedelta

from tbot.candles import Candle, CandleSeries
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

SYMBOLS = ["ES", "NQ", "RTY", "YM", "HG", "GC", "CL"]

CANDLE_PERIODS = [
    timedelta(minutes=1),
    timedelta(minutes=2),
    timedelta(minutes=3),
    timedelta(minutes=5),
    timedelta(minutes=10),
    timedelta(minutes=15),
]


def to_candle(bar, period):
    """Convert an IBKR BarData object to a Candle object."""
    bartime = None
    if period >= timedelta(days=1):
        bartime = datetime.strptime(bar.date, "%Y%m%d").astimezone()
    else:
        bartime = datetime.fromtimestamp(int(bar.date)).astimezone()
    return Candle(
        period,
        bartime,
        float(bar.open),
        float(bar.high),
        float(bar.low),
        float(bar.close),
        float(bar.volume),
    )


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
        historicalQueues = []
        updateQueues = []
        for s in self._symbols:
            historicalQueue = CompletionQueue(key=f"{s}-1m")
            updateQueue = UpdateQueue(f"{s}-1m")
            historicalQueues.append(historicalQueue)
            updateQueues.append(updateQueue)
            self.ibkr.reqHistoricalData(
                historicalQueue,
                updateQueue,
                self._contracts[s],
                timedelta(minutes=1),
                False,
                True,
            )

        # Wait for initial historical data to be returned
        LOGGER.info("Waiting for initial historical data")
        QueuePoller.wait_all(historicalQueues)
        candles = {}
        for q in historicalQueues:
            candle_list = []
            try:
                while True:
                    candle_list.append(to_candle(q.get_nowait(), timedelta(minutes=1)))

            except queue.Empty:
                candles[q.key] = CandleSeries(
                    timedelta(minutes=1), candle_list, len(candle_list)
                )

        # Process updates
        LOGGER.info("Processing real-time candle updates")
        while True:
            rlist = QueuePoller.poll(updateQueues)
            for updateQueue in rlist:
                for i in range(updateQueue.qsize()):
                    candles[q.key].append(to_candle(updateQueue.get_nowait()))

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
