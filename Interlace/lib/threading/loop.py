
from threading import Thread


class Loop:

    """A simple loop, with some callbacks for:
     on_start, on_stop and on_update"""

    # the current state of the pool
    _state = 0

    # should the queue clear on exit
    _clear = False

    # kills the thread if true
    _kill = False

    # true if the pool thread is running
    _has_thread = False

    def has_thread(self):

        """Returns true if the pool thread is running

        Parameters:
            - None
        """

        return self._has_thread

    def state(self):

        """returns the latest state of the pool
            - 0 = off
            - 1 = running
            - 2 = stopping

        Parameters:
            - None
        """

        return self._state

    def start_thread(self):

        """Starts the pool thread if it is not already started

        Parameters:
            - None
        """

        # check there is not a thread already running
        if self._has_thread is False and self._kill is False:

            # start the pool thread
            Thread(target=self._thread, daemon=True).start()

    def stop_thread(self):

        """Stops the pool thread if it is running

        Parameters:
            - None
        """

        # check that the pool thread is running
        if self._kill is False and self._has_thread is True:

            # set kill trigger
            self._kill = True

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

        self.on_start()

        # while the kill flag is not set
        while self._kill is False:

            # call virtual update
            self.on_update()

        # state is now 0 (stopped)
        self.state = 0

        self.on_stop()

        # reset the kill flag
        self._kill = False

        # the pool no longer has a running thread
        self._has_thread = False

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_update(self):

        """Overridable method.
        Called on every loop update.
        no return

        Parameters:
            - None
        """
        pass
