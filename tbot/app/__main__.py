import queue
import threading
import traceback

from tbot.platforms.ibkr import Contract, IBApi
from tbot.util import log

# from threading import Condition


API_PORT = 4002
CLIENT_ID = 78258

LOGGER = log.get_logger()

# This is duplicated. Remove eventually
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

SYMBOLS = ["ES", "NQ", "RTY", "YM"]


class MultiQueue(queue.Queue):
    """Queue that allows waiting for multiple items efficiently."""

    def __init__(self, maxsize=0, nwait=1):
        """Initialize the MultiQueue.

        :param int maxsize: The maximum number of items in the queue. 0 specifies infinite length
        :param int nwait: The number of items required for wait_for_all to return True
        """
        super().__init__(maxsize=maxsize)
        self._nwait = nwait

        self._cv_lock = threading.Lock()
        self._cond = threading.Condition(self._cv_lock)

    def is_complete(self):
        """Determine if there are at least nwait items in the queue."""
        return self.qsize() >= self._nwait

    def put_nowait(self, item):
        """Put an item in the queue, without blocking."""
        super().put_nowait(item)
        with self._cond:
            if self.is_complete():
                self._cond.notify()

    def wait_for_all(self, timeout=None):
        """Wait until at least nwait items are in the queue.

        :param float timeout: The number of seconds to wait. If timeout is None, the wait is indefinite
        :return: True if there are n items in the queue, False if there was a timeout
        :rtype: bool
        """
        with self._cond:
            return self._cond.wait_for(self.is_complete, timeout=timeout)


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

    def run(self):
        """Run the application."""
        try:
            LOGGER.info(f"Running Application with symbols {self._symbols}")

            # Connect to ibkr
            self.ibkr.connect("127.0.0.1", API_PORT, CLIENT_ID)

            # Request IBKR contracts for symbols
            contract_q = MultiQueue(nwait=len(self._symbols))
            for s in self._symbols:
                # Create a continuous futures contract
                c = Contract()
                c.symbol = s
                c.secType = "CONTFUT"
                c.currency = "USD"
                c.exchange = EXCHANGE_LOOKUP.get(s, "")

                self.ibkr.reqContractDetails(contract_q, c)

            # Save the returned contracts
            if not contract_q.wait_for_all(timeout=5):
                raise RuntimeError("Couldn't load all the contracts")
            for i in range(len(self._symbols)):
                c = contract_q.get_nowait().contract
                c.secType = "FUT"
                self._contracts[c.symbol] = c

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
