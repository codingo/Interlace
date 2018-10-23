# module and pool can be used for other stuff,
# so it may be useful to be able it import it from here...
from .queue import Queue
from .pool import Pool as Pool

# should only be used by TaskManager, so obfuscating name
from .scheduler import TaskScheduler as _TaskScheduler

# some standard stuff required
from threading import Thread
from time import time, sleep


class TaskManager(Pool):
    """TaskManager is responsible for executing a large number of task on behalf of a group of modules.
    task can be appended in two different ways.
        - Immediate: task is added to the back of the queue and run asap
        - Scheduled: task is added to a schedule and executed at a given time (see TaskScheduler)
    """

    # seconds to sleep when there is nothing to do
    _SLEEP = 0.1

    def set_thread_sleep(self, seconds):
        self._SLEEP = seconds

    def __init__(self):

        """Definitions:
            - super: Pool
            - scheduler: TaskScheduler instance
        """

        # init super class (Pool)
        super(TaskManager, self).__init__()

        # instance of TaskScheduler to handle scheduled task
        self.scheduler = _TaskScheduler()

    def schedule_task(self, task):

        """Schedules a new task, see TaskScheduler.schedule_task

        Parameters:
            - The task to schedule
        """

        # when adding a task directly,
        # there is no need to specify the time
        # it is always calculated this way
        if 'time' not in task:
            task['time'] = time() + delay

        # call method in TaskScheduler instance
        self.scheduler.schedule_task(task)

    def on_update(self):

        """[Callback]
        Called on every Pool frame,
        runs overdue scheduled task and one from the queue

        Parameters:
            - None
        """

        # prioritises any overdue scheduled task waiting to be executed
        self.scheduler.update()

        # loop through all task until we find one we can use
        for task in self._queue:

            # if the task has been added through a module,
            # it must adhere to the module limit
            if "module" in task:

                # if we can find a worker on this module
                this_worker = task['module'].get_worker()
                if this_worker is not None:
                    # remove the task from the queue
                    self.remove(task)

                    # set the ask in the worker
                    this_worker.set_task(task)

                    # run the task on a new thread
                    Thread(target=this_worker.run_task).start()

                    # stop searching for usable task
                    break

            # the task was added directly
            # no limits to adhere to
            else:

                # create a temp worker
                worker = Worker(None)

                # set the task within the worker
                worker.set_task(task)

                # run task on new thread
                Thread(target=worker.run_task).start()

                # sleep thread based on state
        self._sleep()

    def on_clear(self, item):

        """[Callback]
        Called on every Pool frame when _kill has been activated.
        If the item can be processed, it is processed and True is returned.
        Otherwise, if the item can not be processed, False is returned

        Parameters:
            - the latest item
        """

        # if we can find a worker on this module
        this_worker = item['module'].get_worker()
        if this_worker is not None:
            # remove the task from the queue
            self.remove(item)

            # set the ask in the worker
            this_worker.set_task(item)

            # run the task on a new thread
            Thread(target=this_worker.run_task).start()

            # return true to delete the item
            return True

        # the item could not be processed,
        # return false to append to back of queue and try again
        return False

    def _sleep(self):

        """[Protected]
        Used by on_update as an optimization technique.
        If there are task to be processed, or an overdue scheduled task,
        the thread will not sleep at all.
        If the next scheduled task is less that the default sleep time,
        it will sleep until the next scheduled task expected execution time.
        Otherwise it will sleep for its default sleep time before running the loop again

        Parameters:
            - None
        """

        # get the current time
        time_now = time()

        # if there are items to process, either in queue or schedule
        if len(self._queue) > 0 or time_now > self.scheduler.next_time:

            # do not sleep
            return

        # if the time to the next scheduled task is less than the default sleep time
        elif self.scheduler.next_time - time_now < self._SLEEP:

            # sleep for time to next scheduled task
            sleep(self.scheduler.next_time - time_now)

        # otherwise, if inactive
        else:

            # sleep for default sleep time
            sleep(self._SLEEP)
