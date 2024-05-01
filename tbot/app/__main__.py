import queue
import threading
import time
import traceback

from tbot.platforms.ibkr import Contract, IBApi
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


class PollableQueue(queue.Queue):
    """Queue object that notifies a QueuePoller when at least one item is placed in the queue."""

    def __init__(self, maxsize=0):
        """Initialize the queue.

        :param int maxsize: The maximum size of the queue. 0 indicates queue of infinite length
        """
        super().__init__(maxsize=maxsize)
        self._poll_evt = None

    def _notify(self):
        if self._poll_evt:
            self._poll_evt.set()

    def put_nowait(self, item):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        super().put_nowait(item)
        self._notify()

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue without blocking.

        Only enqueue the item if a free slot is immediately available.
        Otherwise raise the Full exception.
        """
        super().put(item, block, timeout)
        self._notify()

    def set_poll_evt(self, evt):
        """Set the event that this queue sets when an item is placed in the queue.

        This function is typically only called internally within QueuePoller.

        :param threading.Event evt: The event object to notify
        """
        self._poll_evt = evt


class QueuePoller:
    """Class used to efficiently wait on PollableQueue objects."""

    def _check_queues(self, queues):
        ready_list = []
        for q in queues:
            if q.qsize() > 0:
                ready_list.append(q)
        return ready_list

    def poll(self, queues, timeout=None):
        """Poll a list of queues for available data.

        :param list[queue.Queue] queues: A list of queues to poll
        :param timeout: The maximum waiting time before this operation returns. None indicates an indefinite wait
        :returns: A list of queues that have received data
        :rtype: list[queue.Queue]
        """
        # Make sure we're not polling anything other than PollableQueue.
        for q in queues:
            if not isinstance(q, PollableQueue):
                raise TypeError(
                    f"Cannot poll a queue that is not a 'PollableQueue'. Got {type(q)}"
                )

        # Check if anything is immediatley available
        initial_ready_list = self._check_queues(queues)
        if len(initial_ready_list) > 0:
            return initial_ready_list

        # Add the ready event and wait for a queue to trigger it
        evt = threading.Event()
        for q in queues:
            q.set_poll_evt(evt)

        if evt.wait(timeout=timeout):
            return self._check_queues(queues)
        return []

    def wait_all(self, queues, timeout=None):
        """Wait for all queues to have at least one update.

        This can be useful if you need to wait for each queue to get at least one item before returning

        :param list[queue.Queue] queues: A list of queues to poll
        :param timeout: The maximum waiting time before this operation returns. None indicates an indefinite wait
        :return: True if all queues were updated within the timeout, False otherwise
        :rtype: bool
        """
        if len(queues) == 0:
            return False

        complete_queues = {}
        for q in queues:
            complete_queues[id(q)] = False

        time_left = timeout
        while True:
            # Create a list of queues that still haven't returned a result
            poll_list = []
            for q in queues:
                if complete_queues[id(q)] is False:
                    poll_list.append(q)

            # Poll for updated queues
            poll_start_time = time.time()
            ready_list = self.poll(poll_list, timeout=time_left)
            poll_elapsed_time = time.time() - poll_start_time
            for q in ready_list:
                complete_queues[id(q)] = True

            # Check if every queue returned
            done = True
            for q in queues:
                if complete_queues[id(q)] is False:
                    done = False
                    break
            if done:
                return True

            # We're not done, check for timeout
            if timeout is not None:
                time_left -= poll_elapsed_time
                if time_left <= 0:
                    return False


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
                q = PollableQueue()
                contract_queues.append(q)
                self.ibkr.reqContractDetails(q, c)

            # Save the returned contracts
            poller = QueuePoller()
            if not poller.wait_all(contract_queues, timeout=5):
                raise RuntimeError(
                    f"Failed to load requested contracts {self._symbols}"
                )
            for q in contract_queues:
                c = q.get_nowait().contract
                c.secType = "FUT"
                self._contracts[c.symbol] = c
                LOGGER.debug(c)
            LOGGER.info("Contract info received")

            # Request bar data for symbols
            LOGGER.info("Requesting bar data for contracts")

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
