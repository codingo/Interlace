import threading
import subprocess


class Worker(object):
    def __init__(self, pool):
        self.pool = pool

    def __call__(self, task):
        self.run_task(task)
        self.pool.workers.add(self)

    def run_task(self, task):
        try:
            subprocess.run(task)
        except subprocess.TimeoutExpired:
            self.pool.output.terminal(3, "", task, message="Timeout when running %s" % task)
        except subprocess.CalledProcessError:
            self.pool.output.terminal(3, "", task, message="Process error when running %s"
                                                      % task)


class Pool(object):
    def __init__(self, max_workers, queue, timeout, output):
        self.queue = queue
        self.workers = [Worker(self) for w in range(max_workers)]
        self.timeout = timeout
        self.output = output

    def run(self):
        while True:

            # make sure resources are available
            if not self.queue or not self.workers:
                continue

            # get a worker
            worker = self.workers.pop(0)

            # get task from queue
            task = self.queue.pop(0)

            # run
            thread = threading.Thread(target=worker, args=(task, self.output, self.timeout))
            thread.start()