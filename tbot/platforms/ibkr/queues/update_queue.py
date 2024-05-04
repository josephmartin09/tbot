from .pollable_queue import PollableQueue


class UpdateQueue(PollableQueue):
    """Queue object that notifies a QueuePoller when at least one item is placed in the queue.

    This queue is useful when every update to the queue should be processed in poll().
    """

    def __init__(self, maxsize=0, key=""):
        """Initialize the queue.

        :param int maxsize: The maximum size of the queue. 0 indicates queue of infinite length
        :param str key: A key that can be used to identify the queue.
        """
        super().__init__(maxsize=maxsize, key=key)

    def put_nowait(self, item):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        super().put_nowait(item)
        self._notify()

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue without blocking.

        Only enqueue the item if a free slot is immediately available.
        Otherwise raise the Full exception.
        """
        super().put(item, block, timeout)
        self._notify()
