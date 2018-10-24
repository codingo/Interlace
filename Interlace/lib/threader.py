import threading
import os


class Worker(object):
    def __init__(self, pool):
        self.pool = pool

    def __call__(self, task, output, timeout):
        self.run_task(task)
        self.pool.workers.append(self)

    @staticmethod
    def run_task(task):
        os.system(task)


class Pool(object):
    def __init__(self, max_workers, queue, timeout, output):
        self.queue = queue
        self.workers = [Worker(self) for w in range(max_workers)]
        self.timeout = timeout
        self.output = output

    def run(self):
        while True:

            # make sure resources are available
            if not self.workers:
                continue

            # check if the queue is empty
            if not self.queue:
                break

            # get a worker
            worker = self.workers.pop(0)

            # get task from queue
            task = self.queue.pop(0)

            # run
            thread = threading.Thread(target=worker, args=(task, self.output, self.timeout))
            thread.start()