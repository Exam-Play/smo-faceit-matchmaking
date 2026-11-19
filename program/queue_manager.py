class MatchmakingQueue:
    def __init__(self, size):
        if size <= 0:
            raise ValueError("Размер буфера должен быть положительным")
        self.size = size
        self.cells = [None] * size
        self.put_ptr = 0
        self.take_ptr = 0

    def is_empty(self):
        return all(cell is None for cell in self.cells)

    def put(self, request):
        for offset in range(self.size):
            index = (self.put_ptr + offset) % self.size
            if self.cells[index] is None:
                self.cells[index] = request
                self.put_ptr = (index + 1) % self.size
                return None

        index = min(
            range(self.size),
            key=lambda i: self.cells[i].arrival_time
        )
        cancelled_request = self.cells[index]
        self.cells[index] = request
        self.put_ptr = (index + 1) % self.size
        return cancelled_request

    def take_next(self):
        for offset in range(self.size):
            index = (self.take_ptr + offset) % self.size
            if self.cells[index] is not None:
                request = self.cells[index]
                self.cells[index] = None
                self.take_ptr = (index + 1) % self.size
                return request
        return None
