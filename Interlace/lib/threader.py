import threading
import os


class Worker(object):
    def __init__(self, queue, timeout, output):
        self.queue = queue
        self.timeout = timeout
        self.output = output

    def __call__(self):
        while True:
            try:
                # get task from queue
                task = self.queue.pop(0)
                # run task
                self.run_task(task)
            except IndexError:
                break

    @staticmethod
    def run_task(task):
        os.system(task)


class Pool(object):
    def __init__(self, max_workers, queue, timeout, output):
        
        # convert stdin input to integer
        max_workers = int(max_workers)

        # check if there are enough workers
        if max_workers <= 0:
            raise ValueError("Workers must be >= 1")

        # check if the queue is empty
        if not queue:
            raise ValueError("The queue is empty")

        self.queue = queue
        self.timeout = timeout
        self.output = output
        self.max_workers = max_workers

    def run(self):

        workers = [Worker(self.queue, self.timeout, self.output) for w in range(self.max_workers)]
        threads = []


        # run
        for worker in workers:
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)

        # wait until all workers have completed their tasks
        for thread in threads:
            thread.join()

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
    p = Pool(4, tasks, 0, 0)
    p.run()
