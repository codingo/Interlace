import subprocess
import os
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Event
from tqdm import tqdm

import platform

if platform.system().lower() == 'linux':
    shell = os.getenv("SHELL") if os.getenv("SHELL") else "/bin/sh"
else:
    shell = None

class Task(object):
    def __init__(self, command):
        self.task = command
        self.self_lock = None
        self.sibling_locks = []

    def __cmp__(self, other):
        return self.name() == other.name()

    def __hash__(self):
        return self.task.__hash__()

    def clone(self):
        new_task = Task(self.task)
        new_task.self_lock = self.self_lock
        new_task.sibling_locks = self.sibling_locks
        return new_task

    def replace(self, old, new):
        self.task = self.task.replace(old, new)

    def run(self, t=False):
        for lock in self.sibling_locks:
            lock.wait()
        self._run_task(t)
        if self.self_lock:
            self.self_lock.set()

    def wait_for(self, siblings):
        for sibling in siblings:
            self.sibling_locks.append(sibling.get_lock())

    def name(self):
        return self.task

    def get_lock(self):
        if not self.self_lock:
            self.self_lock = Event()
            self.self_lock.clear()
        return self.self_lock

    def _run_task(self, t=False):
        s = subprocess.Popen(self.task, shell=True,
                             stdout=subprocess.PIPE,
                             encoding="utf-8",
                             executable=shell)
        out, _ = s.communicate()

        if out != "":
            if t:
                t.write(out)
            else:
                print(out)


class Worker(object):
    def __init__(self, task_queue, timeout, output, tq):
        self.queue = task_queue
        self.timeout = timeout
        self.output = output
        self.tqdm = tq

    def __call__(self):
        queue = self.queue
        while True:
            try:
                task = next(queue)
                if isinstance(self.tqdm, tqdm):
                    self.tqdm.update(1)
                    # run task
                    task.run(self.tqdm)
                else:
                    task.run()
            except StopIteration:
                break


class Pool(object):
    def __init__(self, max_workers, task_queue, timeout, output, progress_bar):

        # convert stdin input to integer
        max_workers = int(max_workers)

        # check if there are enough workers
        if max_workers <= 0:
            raise ValueError("Workers must be >= 1")

        tasks_count = next(task_queue)

        # check if the queue is empty
        if not tasks_count:
            raise ValueError("The queue is empty")

        self.queue = task_queue
        self.timeout = timeout
        self.output = output
        self.max_workers = min(tasks_count, max_workers)

        if not progress_bar:
            self.tqdm = tqdm(total=tasks_count)
        else:
            self.tqdm = True

    def run(self):
        workers = [Worker(self.queue, self.timeout, self.output, self.tqdm) for w in range(self.max_workers)]

        # run
        with ThreadPoolExecutor(self.max_workers) as executors:
            for worker in workers:
                executors.submit(worker)


# test harness
if __name__ == "__main__":
    tasks = ["sleep 1",
             "sleep 2",
             "sleep 3",
             "sleep 4",
             "sleep 5",
             "sleep 6",
             "sleep 7",
             "sleep 8",
             "sleep 9",
             "sleep 1",
             "echo 'Char!'"]
    p = Pool(4, tasks, 0, 0, True)
    p.run()
