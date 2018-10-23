

class Queue:

    """Queue was intended as a c# style queue"""

    def __init__(self):

        """Definitions:
            - self._queue: the queue of items

        Parameters:
            - None
        """

        # the queue of items
        self._queue = []

    def enqueue(self, item):

        """Adds a new item to the back of the queue"""

        # append item to back of queue
        self._queue.append(item)

    def dequeue(self):

        """Removes an item from the beginning of the queue and returns it.
        Returns none if the queue is empty

        Parameters:
            - None
        """

        # if the queue length is more than zero get the first item
        # otherwise return None
        return self._queue.pop(0) if len(self._queue) > 0 else None

    def dequeue_at(self, index):
        """Removes an item from the queue at a given index and returns it.
        Returns none if the queue is empty

        Parameters:
            - index: the index of the item you wish to remove and return
        """

        # if the queue length is longer than the given index, return item at index,
        # otherwise return None
        return self._queue.pop(index) if len(self._queue) > index else None

    def remove(self, item):

        """Removes an item from the queue

        Parameters:
            - item: the item you wish to remove and return
        """

        # remove the item from the list
        self._queue.remove(item)

    def length(self):

        """Returns the integer number of items in the queue

        Parameters:
            - None
        """

        # return the number of items in the queue
        return len(self._queue)

    def items(self):

        """A get property for the queue

        Parameters:
            - None
        """

        # returns the queue
        return self._queue

    def wipe(self):

        """Deletes every item in the queue immediately

        Parameters:
            - None
        """

        # create a fresh queue
        self._queue = []

    def index_of(self, item):

        """Returns the index of a given item

        Parameters:
            - The item you wish to retrieve an index for
        """

        # return the index of item
        return self._queue.index(item)

    def index(self, index):

        """Returns the item at a given index

        Parameters:
            - The index of the item you wish to retrieve
        """

        # return queue item at index
        return self._queue[index]

