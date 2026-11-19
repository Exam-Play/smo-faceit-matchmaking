class EnqueueDispatcher:
    def __init__(self, queue, statistics, assignment_dispatcher=None):
        self.queue = queue
        self.statistics = statistics
        self.assignment_dispatcher = assignment_dispatcher

    def enqueue(self, request, t=None):
        self.statistics.registerGenerated(request)
        cancelled = self.queue.put(request)

        message = f"заявка {request.label} поступила в очередь."
        if cancelled is not None:
            self.statistics.registerCancelled(cancelled)
            message += (
                f" Очередь полна: выбита самая старая заявка "
                f"{cancelled.label} (отказ)."
            )

        if self.assignment_dispatcher is not None and t is not None:
            message += self.assignment_dispatcher.onQueueChanged(t)
        return message


class AssignmentDispatcher:
    def __init__(self, queue, servers, statistics, server_pointer=0):
        self.queue = queue
        self.servers = servers
        self.statistics = statistics
        self.server_pointer = server_pointer

    def onQueueChanged(self, t):
        if self.queue.is_empty():
            return ""

        server_count = len(self.servers)
        if server_count == 0:
            return " Нет доступных серверов."

        for offset in range(server_count):
            index = (self.server_pointer + offset) % server_count
            server = self.servers[index]

            if not server.is_busy():
                self.server_pointer = (index + 1) % server_count
                request = self.queue.take_next()
                if request is None:
                    return ""

                self.statistics.registerWaiting(
                    request, t - request.arrival_time
                )
                duration = server.startLobbyBuilding(request, t)
                return (
                    f" Сервер {server.id + 1} взял заявку "
                    f"{request.label} (займёт {duration:.2f})."
                )

        return " Все серверы заняты — заявки ждут."

    def onServerReleased(self, server, t):
        return self.onQueueChanged(t)
