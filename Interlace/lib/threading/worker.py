

class Worker:

    """Worker instances are used by Modules to regulate their resource usage"""

    def __init__(self, mod):

        """
        Definition:
            - module: the module 'master' of this worker
            - task: the workers latest task at any given time

        Parameters:
            - mod: the module 'master' of this worker
        """

        # set reference to the module 'master' of this worker
        self.module = mod

        # set current task to null
        self.task = None

        # if this is not a temp worker
        if self.module is not None:

            # register with the module master
            self.module.inactive_workers.append(self)

    def set_task(self, task):

        """Sets a task for the worker

        Parameters:
            - task: the task to be executed next
        """

        # if this is not a temp worker
        if self.module is not None:

            # remove self from modules waiting list
            self.module.inactive_workers.remove(self)

        # set current task
        self.task = task

    def run_task(self):

        """Runs latest task

        Parameters:
            - task: None
        """

        if self.task['kwargs'] is not None:
            # call the task method with args and kwargs
            data = self.task['method'](
                *self.task['args'],
                **self.task['kwargs']
            )

            # if there is a callback set
            if self.task['callback'] and data is not None:

                if type(self.task['callback']) == list or type(self.task['callback']) == tuple:

                    for c in self.task['callback']:
                        c(data)

                else:

                    # call the callback with the return of method
                    self.task['callback'](data)

        # set current task to None
        self.task = None

        # if this is not a temp module
        if self.module is not None:

            # register with module master
            self.module.inactive_workers.append(self)
