from enum import IntEnum

from tbot.util import log

from .ibkr_loader import IbkrLoader

# from .ibkr_loader import SYMBOLS

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")


class AppState(IntEnum):
    """Valid Application States."""

    pass


class App:
    """Class to implement a trading app.

    .. note::
        This description is left intentionally vague because I don't know what this class needs
    """

    def __init__(self):
        """Initialize the application."""
        pass

    def run(self):
        """Run the application."""
        LOGGER.info("Running.")
        ibkr = IbkrLoader(["ES"], realtime=False)
        candles = ibkr.run()
        print(candles)


if __name__ == "__main__":
    log.setup_logging()

    app = App()
    app.run()

    LOGGER.debug("Exited cleanly.")
