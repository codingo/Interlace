
from .queue import Queue
from .loop import Loop


class Pool(Queue, Loop):

    """Pool is a loop that processes a Queue"""

    def __init__(self):

        """Definitions:
            - None

        Parameters:
            - None
        """

        # init super class Queue
        super(Pool, self).__init__()

    def stop_thread(self, clear_queue=False):

        """Stops the pool thread if it is running

        Parameters:
            - None
        """

        # check that the pool thread is running
        if self._kill is False and self._has_thread is True:

            # set kill trigger
            self._kill = True

            # set clear flag
            self._clear = clear_queue

    def _thread(self):

        """[Protected]
        The main pool thread.
        Updates schedule and executes task in queue

        Parameters:
            - None
        """

        # the pool now has a running thread
        self._has_thread = True

        # state is 1 (running)
        self._state = 1

        # while the kill flag is not set
        while self._kill is False:

            # call virtual update
            self.on_update()

        # once the loop exits,
        # state is 2 (stopping)
        self.state = 2

        # if the clear flag is set and there are items still to be processed
        while self._clear and self.length() > 0:

            # dequeue the first item
            item = self.dequeue()

            # try to execute it
            if not self.on_clear(item):

                # if execution not possible append to back and try again
                self.enqueue(item)

        # state is now 0 (stopped)
        self.state = 0

        # reset the kill flag
        self._kill = False

        # the pool no longer has a running thread
        self._has_thread = False

    def on_update(self):

        """Overridable method.
        Called on every loop update.
        no return

        Parameters:
            - None
        """
        pass

    def on_clear(self, item):

        """Overridable method.
        Called every loop while thread is stopping until queue is empty.
        Runs item and return True and item will be removed from queue.
        Returns False if item was not run and item will be appended to back of queue

        Parameters:
            - item: the latest item being processed
        """
        return True
