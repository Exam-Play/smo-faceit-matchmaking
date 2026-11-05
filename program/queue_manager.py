class MatchmakingQueue:
    def __init__(self, size):
        self.size = size
        self.cells = [None] * size
        self.put_ptr = 0
        self.take_ptr = 0

    def is_empty(self):
        return all(c is None for c in self.cells)

    def put(self, req):
        for i in range(self.size):
            idx = (self.put_ptr + i) % self.size

            if self.cells[idx] is None:
                self.cells[idx] = req
                self.put_ptr = (idx + 1) % self.size
                return None

        idx = min(range(self.size), key=lambda k: self.cells[k].arrival_time)
        old = self.cells[idx]

        self.cells[idx] = req
        self.put_ptr = (idx + 1) % self.size

        return old

    def take_next(self):
        for i in range(self.size):
            idx = (self.take_ptr + i) % self.size

            if self.cells[idx] is not None:
                req = self.cells[idx]
                self.cells[idx] = None
                self.take_ptr = (idx + 1) % self.size
                return req

        return None
