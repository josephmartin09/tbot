import traceback

from tbot.platforms.ibkr.queues import QueuePoller
from tbot.util import log

from .ibkr_rt_price import IbkrRtPrice

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
        self._feeds = []

    def run(self):
        """Run the application."""
        try:
            LOGGER.info("Running.")
            ibkr = IbkrRtPrice(["ES"])
            ibkr.connect()
            self._feeds = ibkr.request_price_feed()
            while True:
                ready = QueuePoller.poll(self._feeds.values(), 0.1)
                for r in ready:
                    update = r.get_nowait()
                    LOGGER.info(update)

        except KeyboardInterrupt:
            LOGGER.info("Keyboard Interrupt")

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            ibkr.disconnect()


if __name__ == "__main__":
    log.setup_logging()
    App().run()

    LOGGER.debug("Exited cleanly.")
