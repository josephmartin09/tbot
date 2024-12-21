import traceback

from tbot.candles import CandlePeriod, CandleSeries
from tbot.platforms.schwab_api import SchwabWrapper

# from .discord_msg import send_discord_msg
from tbot.symbol_manager import SymbolManager, SymbolSubscriber
from tbot.util import log

# from datetime import datetime


LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")

FUTURE_LIST = [
    "/HG",
    "/SI",
    "/GC",
    "/CL",
    "/NG",
    "/ES",
    "/NQ",
    "/RTY",
    "/YM",
    "/ZC",
    "/ZS",
]

EQUITY_LIST = [
    "$SPX",
    "$NDX",
    "$DJI",
    "$RUT",
    "$VIX",
]

PD = CandlePeriod("1m")


class Notes(SymbolSubscriber):
    """Class to notify when a candle crosses a note."""

    TONE_A = 440.0
    LOWER_BOUND = 0.1
    UPPER_BOUND = 5e6

    def __init__(self, symbol, period):
        """Initialize the listener."""
        super().__init__(symbol, period)

        # Setup up 12 equal-tempermant notes tuned to TONE_A
        self.notes = []
        interval = 2 ** (float(1) / float(12))
        curr_val = self.TONE_A
        while curr_val > self.LOWER_BOUND:
            self.notes.append(curr_val)
            curr_val /= interval
        curr_val = self.TONE_A * interval
        while curr_val < self.UPPER_BOUND:
            self.notes.append(curr_val)
            curr_val *= interval

        self.notes.sort()

    def on_update(self):
        """Run the check for a note crossing on the most recent candle."""
        last_high = self.feed.last.high
        last_low = self.feed.last.low
        last_time = self.feed.last.time
        for n in self.notes:
            if (last_low <= n) and (last_high >= n):
                msg = f"{self.symbol} at {n} at {last_time}"
                LOGGER.warning(msg)


class App:
    """Class to implement a trading app.

    .. note::
        This description is left intentionally vague because I don't know what this class needs
    """

    def __init__(self):
        """Initialize the application."""
        self.mgr = SymbolManager()

    def run(self):
        """Run the application."""
        schwab = SchwabWrapper(self.mgr)

        try:
            LOGGER.info("Initializing Candles")
            for symbol in FUTURE_LIST:
                # Request Live data
                schwab.add_future_stream(symbol, PD)

                # Register a strategy
                notes_listener = Notes(symbol, PD)
                self.mgr.add_subscriber(notes_listener)
                self.mgr.add_feed(symbol, PD, CandleSeries(PD, [], 500))

            for symbol in EQUITY_LIST:
                schwab.add_equity_stream(symbol, PD)
                self.mgr.add_feed(symbol, PD, CandleSeries(PD, [], 500))

            # Run
            LOGGER.info("Running Event loop")
            schwab.event_loop()

        except KeyboardInterrupt:
            schwab.disconnect()

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            schwab.disconnect()


if __name__ == "__main__":
    log.setup_logging()
    App().run()

    LOGGER.debug("Exited cleanly.")
