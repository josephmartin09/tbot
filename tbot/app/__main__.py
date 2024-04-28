import queue
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
            contract_q = queue.Queue()
            for s in self._symbols:
                # Create a continuous futures contract
                c = Contract()
                c.symbol = s
                c.secType = "CONTFUT"
                c.currency = "USD"
                c.exchange = EXCHANGE_LOOKUP.get(s, "")

                self.ibkr.reqContractDetails(contract_q, c)

            # This is serious garbage
            err = False
            for i in range(4):
                try:
                    c = contract_q.get(timeout=1).contract
                    c.secType = "FUT"
                    self._contracts[c.symbol] = c
                except queue.Empty:
                    err = True

                if err:
                    raise RuntimeError(
                        "Failed to load all requested contract definition"
                    )

            # Not being able to pend on multiple queues is garbage

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
