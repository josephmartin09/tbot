import traceback

from tbot.platforms.ibkr.queues import QueuePoller
from tbot.util import log

from .ibkr_rt_price import IbkrRtPrice
from .symbol_manager import SymbolManager

# from .ibkr_loader import SYMBOLS

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")


class App:
    """Class to implement a trading app.

    .. note::
        This description is left intentionally vague because I don't know what this class needs
    """

    def __init__(self):
        """Initialize the application."""
        self._queues = {}
        self._feeds = {}

    def _run(self):
        """Run the application."""
        try:
            LOGGER.info("Running.")
            ibkr = IbkrRtPrice(["ES"])
            ibkr.connect()
            self._queues = ibkr.request_price_feed()
            while True:
                ready = QueuePoller.poll(self._queues.values(), 0.1)
                for r in ready:
                    price_update = r.get_nowait()
                    LOGGER.info(price_update)

        except KeyboardInterrupt:
            LOGGER.info("Keyboard Interrupt")

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            ibkr.disconnect()

    def run(self):
        """Run the application."""
        mgr = SymbolManager()
        print(mgr)


if __name__ == "__main__":
    log.setup_logging()
    App().run()

    LOGGER.debug("Exited cleanly.")
