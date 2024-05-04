import queue


class PollableQueue(queue.Queue):
    """PollableQueue base class.

    PollableQueues are intended to be used with QueuePoller to allow a caller to efficiently poll multiple queues for information. It is up
    to derived classes to implement logic for when the queue should indicate readyness.
    """

    def __init__(self, maxsize=0, key=""):
        """Initialize the queue.

        :param int maxsize: The maximum size of the queue. 0 indicates queue of infinite length
        :param str key: A key that can be used to identify the queue.
        """
        super().__init__(maxsize=maxsize)
        self._poll_evt = None
        self.key = key

    def _notify(self):
        if self._poll_evt:
            self._poll_evt.set()

    def set_poll_evt(self, evt):
        """Set the event that this queue sets when an item is placed in the queue.

        This function is typically only called internally within QueuePoller.

        :param threading.Event evt: The event object to notify
        """
        self._poll_evt = evt
