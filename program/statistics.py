class Statistics:
    def __init__(self, n_players, n_servers):
        self.generated = [0] * n_players
        self.cancelled = [0] * n_players
        self.processed = [0] * n_players
        self.wait_times = [[] for _ in range(n_players)]
        self.service_times = [[] for _ in range(n_players)]

    def registerGenerated(self, request):
        self.generated[request.player_id] += 1

    def registerCancelled(self, request):
        self.cancelled[request.player_id] += 1

    def registerWaiting(self, request, wait):
        self.wait_times[request.player_id].append(wait)

    def registerProcessed(self, request, service_time):
        self.processed[request.player_id] += 1
        self.service_times[request.player_id].append(service_time)

    def summary(self, servers, total_time):
        lines = [f"Общее время моделирования: {total_time:.2f}", ""]

        for player_id, generated in enumerate(self.generated):
            rejected_probability = (
                self.cancelled[player_id] / generated if generated else 0
            )
            waiting = self.wait_times[player_id]
            service = self.service_times[player_id]
            avg_wait = sum(waiting) / len(waiting) if waiting else 0
            avg_service = sum(service) / len(service) if service else 0

            lines.append(
                f"Игрок {player_id + 1}: заявок {generated}, "
                f"отказов {self.cancelled[player_id]} "
                f"(P_отк={rejected_probability:.3f}), "
                f"обработано {self.processed[player_id]}, "
                f"T_ож={avg_wait:.3f}, T_обсл={avg_service:.3f}"
            )

        lines.append("")
        for server in servers:
            load = server.busy_time / total_time if total_time else 0
            lines.append(
                f"Сервер {server.id + 1}: загрузка K_исп={load:.3f}"
            )
        return "\n".join(lines)