class SystemState:
    def __init__(self, time, queue, server_pointer, servers, last_message):
        self.time = time
        self.queueCells = list(queue.cells)
        self.putPointer = queue.put_ptr
        self.takePointer = queue.take_ptr
        self.serverPointer = server_pointer
        self.servers = list(servers)
        self.lastMessage = last_message