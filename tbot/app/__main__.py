import traceback
from datetime import datetime

from tbot.candles import Candle, CandlePeriod, CandleSeries
from tbot.platforms.ibkr import IBWrapper
from tbot.util import log

from .symbol_listener import SymbolListener
from .symbol_manager import SymbolManager

# from .ibkr_loader import SYMBOLS

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")

SYM = "HG"
EXCHANGE = "COMEX"
PD = CandlePeriod("5m")


class Notes(SymbolListener):
    """Class to notify when a candle crosses a note."""

    TONE_A = 440.0
    LOWER_BOUND = 0.1
    UPPER_BOUND = 5e6

    def __init__(self):
        """Initialize the listener."""
        super().__init__(SYM, PD)

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

    def run(self):
        """Run the check for a note crossing on the most recent candle."""
        last_high = self.feed.last.high
        last_low = self.feed.last.low
        last_time = self.feed.last.time
        for n in self.notes:
            if (last_low < n) and (last_high > n):
                LOGGER.warning(f"{self.symbol} at {n} at {last_time}")


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
        # Hack to replay part of the series
        ib = IBWrapper()
        candles_raw = ib.historical_data(SYM, PD, exchange=EXCHANGE)
        candles = []
        for cr in candles_raw:
            candles.append(
                Candle(
                    PD,
                    datetime.fromtimestamp(cr["time"]),
                    cr["open"],
                    cr["high"],
                    cr["low"],
                    cr["close"],
                    cr["volume"],
                )
            )

        notes_listener = Notes()
        self.mgr.add_listener(notes_listener)
        self.mgr.add_feed(SYM, PD, CandleSeries(PD, candles[0:2], 500))

        try:
            for c in candles[2:]:
                self.mgr.update_feed(SYM, PD, c)
                if notes_listener.has_update():
                    notes_listener.run()

        except KeyboardInterrupt:
            pass

        except Exception:
            LOGGER.error(traceback.format_exc())

        finally:
            ib.disconnect()


if __name__ == "__main__":
    log.setup_logging()
    App().run()

    LOGGER.debug("Exited cleanly.")
