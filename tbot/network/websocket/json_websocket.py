import json
import logging
import queue
from abc import ABC
from datetime import timedelta
from threading import Event, Thread

from websocket import WebSocket, WebSocketTimeoutException


def check_thr_exception(f):
    """Decorate the thread exception catching mechanism.

    If an exception from the other thread was detected, disconnect the socket and re-raise that exception
    in the main thread.
    """

    def _check(self, *args, **kwargs):
        if self._thr_exception:
            e = self._thr_exception
            self.disconnect()
            raise e
        return f(self, *args, **kwargs)

    return _check


class JsonWebSocket(ABC):
    """Class implementing base functionality of a websocket receiving JSON payloads."""

    def __init__(self, url, internal_timeout=timedelta(milliseconds=100)):
        """Initialize the web socket.

        :param str url: The URL of the websocket remote endpoint
        :param datetime.timedelta internal_timeout: The maximum receive timeout to use on the internal socket's recv() operation.

        .. note::
            internal_timeout is NOT the same as the recv_timeout parameter in the recv() function. You can adjust
            internal_timeout to shorten the socket thread's max loop time, if that is any use in your application.
            You likely don't need to set this parameter different than what's default.

        .. note::
            This puts the websocket in a state where it is ready for connect() to be called. The websocket
            is initialized unconnected, and a separate call to connect() is neccessary to perform the underlying
            networking.
        """
        self._url = url

        if not isinstance(internal_timeout, timedelta):
            raise TypeError(
                f"param 'internal_timeout' must be of type datetime.timedelta. Got {type(internal_timeout)}"
            )
        self._recv_timeout = internal_timeout.total_seconds()
        self._reset_state()

    def __del__(self):
        """Ensure socket is disconnected gracefully if object is going out of scope."""
        self.disconnect()

    def _reset_state(self):
        self._ws = None
        self._stop_evt = Event()
        self._rx_queue = queue.Queue()
        self._tx_queue = queue.Queue()
        self._thr = None
        self._thr_exception = None

    def _check_thr_exception(self):
        if self._thr_exception:
            e = self._thr_exception
            self.disconnect()
            raise e

    def _thr_loop_func(self):
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
            self._rx_queue.put_nowait(payload)

    def _thr_func(self, start_evt):
        start_evt.set()
        try:
            while not self._stop_evt.is_set():
                self._thr_loop_func()
        except Exception as e:
            self._thr_exception = e
            return

    def _send(self, payload):
        if self._ws:
            # Serialize the payload to JSON
            payload = json.dumps(payload)

            # Try to send the payload to the remote endpoint
            try:
                self._ws.send(payload)

            # Something went wrong: it could be for many unpredicatble reasons, so we simply catch it, log it,
            # then pigeon-hole it into ConnectionResetError
            except Exception:
                raise ConnectionResetError(f"Connection to {self._url} was terminated.")
        else:
            raise RuntimeError("Called _send() on a disconnected websocket.")

    def _recv(self):
        if self._ws:
            try:
                return json.loads(self._ws.recv())

            # Websocket timeout occurred
            except WebSocketTimeoutException:
                return None

            # Something went wrong: it could be for many unpredicatble reasons, so we simply catch it, log it,
            # then pigeon-hole it into ConnectionResetError
            except Exception:
                raise ConnectionResetError(f"Connection to {self._url} was terminated.")
        else:
            raise RuntimeError("Called _recv() on a disconnected websocket.")

    def connect(self):
        """Attempt to connect the websocket to the configured remote endpoint.

        :raises ConnectionError: Raised if connection to the remote endpoint failed.
        """
        if not self._ws:
            # Create a websocket
            self._ws = WebSocket()

            # Attempt to connect to the remote endpoint on the main thread
            err = None
            try:
                self._ws.connect(self._url)
                self._ws.settimeout(self._recv_timeout)

            except Exception as e:
                logging.error(e)
                err = e

            if err:
                self._reset_state()
                raise ConnectionError(f"Failed to connect to {self._url}")

            # Launch a thread to handle actual socket operation
            start_evt = Event()
            self._thr = Thread(target=self._thr_func, args=(start_evt,))
            self._thr.start()
            start_evt.wait()

        else:
            raise RuntimeError(
                "Called connect() on an already connected JsonWebSocket."
            )

    def disconnect(self):
        """Disconnect the websocket from the remote endpoint."""
        if hasattr(self, "_ws") and self._ws:
            # Join the thread
            self._stop_evt.set()
            self._thr.join()

            # Close the websocket connection
            self._ws.close()

            # Reset all internal state so connect() can be called again
            self._reset_state()

    @check_thr_exception
    def send(self, payload):
        """Send a payload over the websocket.

        :param object payload: The payload to send.
        :raises TypeError: Raised if the payload could not be serialized to json
        :raises ConnectionResetError: Raised if
            * the remote endpoint disconnected during the operation
            * a lower-level socket exception occurred
        :raises RuntimeError: Raised if this method is called on a disconnected websocket

        .. note::
            All exceptions that occur at lower levels are pigeon-holed into the set of exceptions listed above.
            This is done to provide the user a finite-number of conditions to check that are independent of the
            networking implementation taking place lower in the stack.
        """
        self._tx_queue.put_nowait(payload)

    @check_thr_exception
    def recv(self, timeout=None):
        """Receive a payload from the websocket.

        :param datetime.timedelta timeout:
            * The maximum amount of time to block waiting for
        :returns:
            * The JSON-decoded payload received from the remote endpoint
            * None if the socket receive operation timed out
        :raises TypeError: Raised if the payload could not be deserialized from json
        :raises ConnectionResetError: Raised if
            * the remote endpoint disconnected during the operation
            * a lower-level socket exception occurred
        :raises RuntimeError: Raised if this method is called on a disconnected websocket

        .. note::
            All exceptions that occur at lower levels are pigeon-holed into the set of exceptions listed above.
            This is done to provide the user a finite-number of conditions to check that are independent of the
            networking implementation taking place lower in the stack.
        """
        try:
            timeout_s = None if timeout is None else timeout.total_seconds()
            return self._rx_queue.get(timeout=timeout_s)

        except queue.Empty:
            return None
