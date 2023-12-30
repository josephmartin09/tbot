class FeedConnectError(Exception):
    """Exception indicating the attempt to connect to the data feed failed."""


class FeedDisconnectError(Exception):
    """Exception indicating an unexpected termination of feed's connection."""
