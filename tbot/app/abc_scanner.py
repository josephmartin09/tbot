from texttable import Texttable

from tbot.indicators.qte import GannAnalysis, GannDir
from tbot.util import log

from .discord_msg import send_discord_msg

LOGGER = log.get_logger()
LOGGER.setLevel("DEBUG")


class ABCScanner:
    """Application to scan for ABCs at a key level."""

    WAIT_PRICE_LEVEL = 1
    WAIT_ABC = 2
    DONE = 3

    def __init__(self, name, candles):
        """Initialize the ABCScanner.

        :param string name: A name to give this strategy.
        :param CandleSeries candles: The candle series to use by the strategy.
        """
        self._name = name
        self._candles = candles

        self._candles.register_indicator("gann", GannAnalysis())

    def update(self):
        """Execute an update of the strategy.

        .. note::
            This is guaranteed to be called after a new candle is received. There's no need to check for a new candle
        """
        potential_abc = self._candles.indicators["gann"].last["abcs"][-1]
        if potential_abc == GannDir.UP:
            LOGGER.info(f"Notifying ABC UP for {self._name}")
            table_msg = Texttable()
            table_msg.add_row(["Symbol", "ABC Time", "Direction"])
            table_msg.add_row([self._name, self._candles.last.time, "SHORT"])
            send_discord_msg(table_msg.draw())

        elif potential_abc == GannDir.DOWN:
            LOGGER.info(f"Notifying ABC DOWN for {self._name}")
            table_msg = Texttable()
            table_msg.add_row(["Symbol", "ABC Time", "Direction"])
            table_msg.add_row([self._name, self._candles.last.time, "LONG"])
            send_discord_msg(table_msg.draw())
