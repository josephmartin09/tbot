from .pollable_queue import PollableQueue


class CompletionQueue(PollableQueue):
    """Queue object that notifies completion after several items are returned.

    This queue is useful when there should not be a completion until many items are received (IBKR Historical Data)
    """

    def __init__(self, maxsize=0, key=""):
        """Initialize the queue.

        :param int maxsize: The maximum size of the queue. 0 indicates queue of infinite length
        :param str key: A key that can be used to identify the queue.
        """
        super().__init__(maxsize=maxsize, key=key)

    def complete(self):
        """Mark the queue operation as complete."""
        self._notify()
