import threading
import time

from .pollable_queue import PollableQueue


class QueuePoller:
    """Class used to efficiently wait on PollableQueue objects."""

    @classmethod
    def _check_queues(cls, queues):
        ready_list = []
        for q in queues:
            if q.qsize() > 0:
                ready_list.append(q)
        return ready_list

    @classmethod
    def poll(cls, queues, timeout=None):
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
        initial_ready_list = cls._check_queues(queues)
        if len(initial_ready_list) > 0:
            return initial_ready_list

        # Add the ready event and wait for a queue to trigger it
        evt = threading.Event()
        for q in queues:
            q.set_poll_evt(evt)

        if evt.wait(timeout=timeout):
            return cls._check_queues(queues)
        return []

    @classmethod
    def wait_all(cls, queues, timeout=None):
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
            ready_list = cls.poll(poll_list, timeout=time_left)
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
