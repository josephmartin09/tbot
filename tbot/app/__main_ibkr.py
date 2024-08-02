import traceback
from datetime import datetime

from tbot.candles import Candle, CandlePeriod, CandleSeries
from tbot.platforms.ibkr import IBWrapper
from tbot.util import log

from .discord_msg import send_discord_msg
from .symbol_listener import SymbolListener
from .symbol_manager import SymbolManager

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")

PD = CandlePeriod("3m")

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


class Notes(SymbolListener):
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
        # LOGGER.debug(
        #     f"Running on {self.symbol}-{self.period}. Last candle start {self.feed.last.time}"
        # )
        last_high = self.feed.last.high
        last_low = self.feed.last.low
        last_time = self.feed.last.time
        for n in self.notes:
            if (last_low <= n) and (last_high >= n):
                msg = f"{self.symbol} at {n} at {last_time}"
                LOGGER.warning(msg)
                send_discord_msg(msg)


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
        ib = IBWrapper(self.mgr)

        try:
            LOGGER.info("Initializing Candles")
            send_discord_msg("Launching TBOT Scanner")
            for symbol, exchange in EXCHANGE_LOOKUP.items():
                # Load a live IBKR data feed
                candles_raw = ib.live_data(symbol, PD, exchange=exchange)
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

                # Register a strategy
                notes_listener = Notes(symbol, PD)
                self.mgr.add_listener(notes_listener)
                self.mgr.add_feed(symbol, PD, CandleSeries(PD, candles, 500))

            # Run
            LOGGER.info("Running Event loop")
            ib.event_loop()

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
