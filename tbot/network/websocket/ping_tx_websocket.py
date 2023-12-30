import logging
import queue
from abc import abstractmethod
from datetime import datetime, timedelta

from . import JsonWebSocket


class PingTxWebSocket(JsonWebSocket):
    """Implemenation of a websocket that pings the remote endpoint at a pre-configured interval."""

    def __init__(self, url, ping_interval):
        """Initialize the web socket.

        :param str url: The URL of the websocket remote endpoint
        :param datetime.timedelta ping_interval: The time period of the ping operation.

        .. note::
            The ping operation is done transparently.  There is no user interaction requried to ping the remote endpoint.
        """
        super().__init__(url)

        if not isinstance(ping_interval, timedelta):
            raise TypeError(
                f"param 'ping_interval' must be of type dateime.timedelta. Got {type(ping_interval)}"
            )

        # Ensure the recv_timeout is not longer than the required ping interval. This prevents a case where the
        # ping operation is done too late because the recv() call was blocking too long.
        ping_interval_seconds = ping_interval.total_seconds()
        if self._recv_timeout > ping_interval_seconds:
            logging.warning(
                f"Lowering internal timeout to ping interval {ping_interval_seconds}"
            )
            self._recv_timeout = ping_interval_seconds

        self._last_ping = None
        self._ping_interval = ping_interval

    def _ping_if_time(self):
        now = datetime.now()
        if (self._last_ping is None) or ((self._last_ping + self._ping_interval) < now):
            self._send(self.create_ping_payload())
            if self._last_ping is not None:
                self._last_ping += self._ping_interval
            else:
                self._last_ping = now

    def _thr_loop_func(self):
        # Ping if needed
        self._ping_if_time()

        # Send anything that was queued
        while True:
            try:
                payload = self._tx_queue.get_nowait()
                self._send(payload)
            except queue.Empty:
                break

        # Recv
        payload = self._recv()
        if payload:
            if not self.is_pong_payload(payload):
                self._rx_queue.put_nowait(payload)

    @abstractmethod
    def create_ping_payload(self):
        """Create a ping payload in the format required by the remote endpoint.

        :returns: A message in the format of a ping message recognized by the remote endpoint.
        """
        pass

    @abstractmethod
    def is_pong_payload(self, payload):
        """Verify if the payload is a pong message from the remote endpoint.

        :param object payload: The payload to be tested as a pong payload.
        :returns:
            * True if the payload is a pong
            * False if the payload isn't a pong
        """
        pass
