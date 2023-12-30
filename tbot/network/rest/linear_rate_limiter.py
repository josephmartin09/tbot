import time
from datetime import datetime, timedelta


class LinearRateLimiter:
    """Class to rate limit HTTPS REST requests to a configurable per-second period."""

    def __init__(self, period):
        """Initialize the rate limiter.

        :param datetime.timedelta period: The period between requests that is desired by using the throttle mechanism
        """
        if not isinstance(period, timedelta):
            raise TypeError(
                f"Time increment needs to be a timedelta, got {type(timedelta)}"
            )

        self._incr = period
        self._last_run = None

    def throttle(self):
        """Sleep as much time as needed to ensure execution rate does not exceed the configured period."""
        # In the case where we've never run, run immediatley
        now = datetime.now()
        if not self._last_run:
            self._last_run = now
            return

        # Calculate how long to sleep to perform the rate-limit
        sleep_seconds = ((self._last_run + self._incr) - (now)).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

            # Subtle point: By linearly adding time (rather than just using another datetime.now()),
            # you end up steering the rate away from being affected by execution time
            self._last_run += self._incr

        # In this case, we assume the execution of the program doesn't need rate limiting,
        # or there's been a large pause since the last throttle call.
        else:
            self._last_run = now
