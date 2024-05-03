import queue
import threading
import time


class PollableQueue(queue.Queue):
    """Queue object that notifies a QueuePoller when at least one item is placed in the queue."""

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

    def set_poll_evt(self, evt):
        """Set the event that this queue sets when an item is placed in the queue.

        This function is typically only called internally within QueuePoller.

        :param threading.Event evt: The event object to notify
        """
        self._poll_evt = evt


class QueuePoller:
    """Class used to efficiently wait on PollableQueue objects."""

    def _check_queues(self, queues):
        ready_list = []
        for q in queues:
            if q.qsize() > 0:
                ready_list.append(q)
        return ready_list

    def poll(self, queues, timeout=None):
        """Poll a list of queues for available data.

        :param list[queue.Queue] queues: A list of queues to poll
        :param timeout: The maximum waiting time before this operation returns. None indicates an indefinite wait
        :returns: A list of queues that have received data
        :rtype: list[queue.Queue]
        """
        # Make sure we're not polling anything other than PollableQueue.
        for q in queues:
            if not isinstance(q, PollableQueue):
                raise TypeError(
                    f"Cannot poll a queue that is not a 'PollableQueue'. Got {type(q)}"
                )

        # Check if anything is immediatley available
        initial_ready_list = self._check_queues(queues)
        if len(initial_ready_list) > 0:
            return initial_ready_list

        # Add the ready event and wait for a queue to trigger it
        evt = threading.Event()
        for q in queues:
            q.set_poll_evt(evt)

        if evt.wait(timeout=timeout):
            return self._check_queues(queues)
        return []

    def wait_all(self, queues, timeout=None):
        """Wait for all queues to have at least one update.

        This can be useful if you need to wait for each queue to get at least one item before returning

        :param list[queue.Queue] queues: A list of queues to poll
        :param timeout: The maximum waiting time before this operation returns. None indicates an indefinite wait
        :return: True if all queues were updated within the timeout, False otherwise
        :rtype: bool
        """
        if len(queues) == 0:
            return False

        complete_queues = {}
        for q in queues:
            complete_queues[id(q)] = False

        time_left = timeout
        while True:
            # Create a list of queues that still haven't returned a result
            poll_list = []
            for q in queues:
                if complete_queues[id(q)] is False:
                    poll_list.append(q)

            # Poll for updated queues
            poll_start_time = time.time()
            ready_list = self.poll(poll_list, timeout=time_left)
            poll_elapsed_time = time.time() - poll_start_time
            for q in ready_list:
                complete_queues[id(q)] = True

            # Check if every queue returned
            done = True
            for q in queues:
                if complete_queues[id(q)] is False:
                    done = False
                    break
            if done:
                return True

            # We're not done, check for timeout
            if timeout is not None:
                time_left -= poll_elapsed_time
                if time_left <= 0:
                    return False
