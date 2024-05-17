from tbot.util import log

from .ibkr_loader import SYMBOLS, IbkrLoader

LOGGER = log.get_logger()


if __name__ == "__main__":
    log.setup_logging()

    app = IbkrLoader(SYMBOLS)
    app.run()
