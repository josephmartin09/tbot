import json

import requests


class RestApiError(Exception):
    """Exception indicating the REST API call returned an error."""

    pass


class JsonRestApi:
    """Class to implement sending JSON-based REST requests to an HTTP API endpoint."""

    def __init__(self, base_url, rate_limiter=None):
        """Initialize the API instance.

        :param str base_url: The base URL of the API
        :param LinearRateLimiter rate_limiter: A LinearRateLimiter instance to be used to throttle the minimum request period
        """
        self._base_url = base_url
        self._rate_limiter = rate_limiter

    def get_json(self, endpoint, params=None):
        """Attempt to retrieve JSON from the specified url.

        :param str endpoint: The API endpoint to append to the API base_url. For example: /ping
        :param dict params: A dictionary of params to be sent in the GET request.
        :returns: A dict with the decoded JSON returned from the request
        :raises: RestApiError if
            * The response isn't a JSON payload
            * The status code of the request isn't 200
        """
        req_url = f"{self._base_url}{endpoint}"
        # If there's a rate limiter, use it before making the call
        if self._rate_limiter:
            self._rate_limiter.throttle()

        # Make sure the API returned a 200
        raw_resp = requests.get(req_url, params=params)
        if raw_resp.status_code != 200:
            raise RestApiError(
                "API responsed with error for request:",
                endpoint,
                "params:",
                params,
                "response:",
                raw_resp.text,
            )

        # Make sure the API responded with JSON
        resp = None
        try:
            resp = json.loads(raw_resp.text)
        except json.JSONDecodeError:
            pass
        if resp is None:
            raise RestApiError("API response wasn't JSON:", raw_resp.text)

        # At this point it looks good from a network standpoint
        # Return so user api-specific logic can be done
        return resp
