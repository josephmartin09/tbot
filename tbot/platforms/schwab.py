import asyncio
import json
import logging
import os

from schwab import auth, streaming

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
                print(json.dumps(message, indent=4))

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
