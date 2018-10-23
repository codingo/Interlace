
# requires .worker for 'force run' technique
from .worker import Worker

# some standard stuff required
from threading import Thread
from time import time


class TaskScheduler:

    """TaskScheduler is intended to be an extension to the TaskManager class.
    It allows task to be added to a queue and executed based on their time deadline,
    (as opposed to the order they sit in the queue).

    Scheduled task have the same options as regular ones, with a few extras.
        - time: the expected time of execution.
        - reoccurring: should the task be triggered again?
        - delay: will cause the task to be triggered every <delay> seconds.
        - run_now: should the task be run immediately (as well).
    """

    def __init__(self):

        """Definitions:
            - self.task: the list of scheduled task
            - self.next_index: the task list index of the next scheduled task
            - self.next_time: the expected execution time of the next scheduled task

        Parameters:
            - None
        """

        # task waiting for deadline
        self.tasks = []

        # expected execution time of next scheduled task
        self.next_index = -1

        # index of next scheduled task in task list
        self.next_time = -1.0

    def update(self):

        """Called every time you want to update the schedule,
        this should really be as often as possible (every frame, if from a loop).

        Runs any over due task and prepares the next

        Parameters:
            - None
        """

        # if a task is due, it is force run
        if self.next_index >= 0 and time() > self.next_time:

            # find the task in the list and force run it
            task = self.tasks.pop(self.next_index)
            self._force_run(task)

            # reset next time and index
            self.next_time = -1
            self.next_index = -1

            # if the task is reoccurring, it is set up again
            if task['reoccurring']:
                task['time'] = time() + task['delay']
                task['run_now'] = False
                self.tasks.append(task)

            # set up the next time and index
            self._prepare_next()

    def schedule_task(self, task):

        """Adds a new task to the schedule.
        Also triggers _prepare_next in case this task is expected earlier than the latest

        Parameters:
            - task: the task to run
        """


        # add the task to the list
        self.tasks.append(task)

        # if it has the 'run_now' flag,
        # force run it now too
        if task['run_now']:
            self._force_run(task)

        # prepare next index and time,
        # in case new task is earlier than one currently set
        self._prepare_next()

    def _force_run(self, task):

        """[Protected]
        Force run is a way of bypassing thread restrictions enforced by the pool and its modules.
        A temp worker is created, used and destroyed.

        Parameters:
            - task: the task to run
        """

        # create a temp worker
        worker = Worker(None)

        # set the task within the worker
        worker.set_task(task)

        # run task on new thread
        Thread(target=worker.run_task).start()

    def _prepare_next(self):

        """[Protected]
        Finds the item in the queue with the lowest timestamp and
        records its expected execution time and index within queue

        Parameters:
            - None
        """

        # for each task in the schedule
        for task in self.tasks:

            # if the task is already overdue,
            # set it as next and skip the rest of search
            if time() > task['time']:
                self.next_index = self.tasks.index(task)
                self.next_time = task['time']
                break

            # otherwise if there is no next task
            # or this one is required sooner than the one currently set,
            # set it but continue searching
            elif self.next_index < 0 or task['time'] < self.next_time:
                self.next_index = self.tasks.index(task)
                self.next_time = task['time']
