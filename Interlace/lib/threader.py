import subprocess
from multiprocessing import Event
from threading import Thread

from tqdm import tqdm


class Task(object):
    def __init__(self, command):
        self.task = command
        self._lock = None
        self._waiting_for_task = False

    def __cmp__(self, other):
        return self.name() == other.name()

    def __hash__(self):
        return self.task.__hash__()

    def clone(self):
        new_task = Task(self.task)
        new_task._lock = self._lock
        new_task._waiting_for_task = self._waiting_for_task
        return new_task

    def replace(self, old, new):
        self.task = self.task.replace(old, new)

    def run(self, t=False):
        if not self._waiting_for_task:
            self._run_task(t)
            if self._lock:
                self._lock.set()
        else:
            self._lock.wait()
            self._run_task(t)

    def wait_for(self, lock):
        self._lock = lock
        self._waiting_for_task = True

    def set_lock(self):
        if not self._lock:
            self._lock = Event()
            self._lock.clear()

    def name(self):
        return self.task

    def get_lock(self):
        return self._lock

    def _run_task(self, t=False):
        if t:
            s = subprocess.Popen(self.task, shell=True, stdout=subprocess.PIPE)
            t.write(s.stdout.readline().decode("utf-8"))
        else:
            subprocess.Popen(self.task, shell=True)


class TaskBlock(Task):
    def __init__(self, name):
        super().__init__('')
        self._name = name
        self.tasks = []

    def name(self):
        return self._name

    def add_task(self, task):
        self.tasks.append(task)

    def __len__(self):
        return len(self.tasks)

    def __hash__(self):
        hash_value = 0
        for t in self.tasks:
            hash_value ^= t.__hash__()
        return hash_value

    def __iter__(self):
        return self.tasks.__iter__()

    def last(self):
        return self.tasks[-1]

    def _run_task(self, t=False):
        for task in self.tasks:
            task._run_task(t)

    def get_tasks(self):
        return self.tasks


class Worker(object):
    def __init__(self, task_queue, timeout, output, tqdm):
        self.queue = task_queue
        self.timeout = timeout
        self.output = output
        self.tqdm = tqdm

    def __call__(self):
        while True:
            try:
                # get task from queue
                task = self.queue.pop(0)
                if isinstance(self.tqdm, tqdm):
                    self.tqdm.update(1)
                    # run task
                    task.run(self.tqdm)
                else:
                    task.run()
            except IndexError:
                break


class Pool(object):
    def __init__(self, max_workers, task_queue, timeout, output, progress_bar):

        # convert stdin input to integer
        max_workers = int(max_workers)

        # check if there are enough workers
        if max_workers <= 0:
            raise ValueError("Workers must be >= 1")

        # check if the queue is empty
        if not task_queue:
            raise ValueError("The queue is empty")

        self.queue = task_queue
        self.timeout = timeout
        self.output = output
        self.max_workers = min(len(task_queue), max_workers)

        if not progress_bar:
            self.tqdm = tqdm(total=len(task_queue))
        else:
            self.tqdm = True

    def run(self):
        workers = [Worker(self.queue, self.timeout, self.output, self.tqdm) for w in range(self.max_workers)]
        threads = []

        # run
        for worker in workers:
            thread = Thread(target=worker)
            thread.start()
            threads.append(thread)

        # wait until all workers have completed their tasks
        for thread in threads:
            thread.join()


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
