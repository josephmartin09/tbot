import asyncio
import logging
import os
from datetime import datetime

from schwab import auth, streaming

from tbot.candles import Candle, CandlePeriod

LOGGER = logging.getLogger(__name__)


class SchwabWrapper:
    """A wrapper class around schwab-py."""

    def __init__(self, mgr):
        """Initialize the IB API.

        :param SymbolManager mgr: A reference to the symbol manager
        """
        # Connect to Schwab, and fail if you can't
        token_path = "./token.json"
        # callback_url = "https://127.0.0.1:8100"
        api_key = os.environ["SCHWAB_KEY"]
        app_secret = os.environ["SCHWAB_SECRET"]

        client = auth.client_from_token_file(
            token_path=token_path, api_key=api_key, app_secret=app_secret, asyncio=True
        )

        self.client = streaming.StreamClient(client)
        self.mgr = mgr

        self._futures = []
        self._equities = []

    def add_future_stream(self, symbol, period):
        """Add a symbol to the futures streams."""
        LOGGER.warning("PERIOD PARAMETER HAS NO EFFECT in add_future_stream")
        if symbol not in self._futures:
            self._futures.append(symbol)

    def add_equity_stream(self, symbol, period):
        """Add a symbol to the equity streams."""
        LOGGER.warning("PERIOD PARAMETER HAS NO EFFECT in add_equity_stream")
        if symbol not in self._equities:
            self._equities.append(symbol)

    def event_loop(self):
        """Run the event loop."""

        async def read_stream():
            await self.client.login()

            def on_bar(message):
                # HACK: There's a bug in equity subs streaming: volume and open mixed
                if message["service"] == "CHART_EQUITY":
                    for raw_bar in message["content"]:
                        open_price = raw_bar["VOLUME"]
                        volume = raw_bar["OPEN_PRICE"]
                        raw_bar["OPEN_PRICE"] = open_price
                        raw_bar["VOLUME"] = volume

                period = CandlePeriod("1m")
                for raw_bar in message["content"]:
                    # Convert bar into candle
                    candle = Candle(
                        period,
                        datetime.fromtimestamp(raw_bar["CHART_TIME"] / 1000),
                        raw_bar["OPEN_PRICE"],
                        raw_bar["HIGH_PRICE"],
                        raw_bar["LOW_PRICE"],
                        raw_bar["CLOSE_PRICE"],
                        raw_bar["VOLUME"],
                    )
                    self.mgr.update_feed(raw_bar["key"], period, candle)

            self.client.add_chart_futures_handler(on_bar)
            self.client.add_chart_equity_handler(on_bar)
            await self.client.chart_futures_subs(self._futures)
            await self.client.chart_equity_add(self._equities)

            while True:
                await self.client.handle_message()

        asyncio.run(read_stream())

    def disconnect(self):
        """Disconnect from the Schwab API."""
        print("CALLED DISCONNECT")
        asyncio.get_event_loop().stop()
