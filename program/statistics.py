class Statistics:
    def __init__(self, n_players, n_servers):
        self.generated = [0] * n_players
        self.cancelled = [0] * n_players
        self.processed = [0] * n_players
        self.wait_times = [[] for _ in range(n_players)]
        self.service_times = [[] for _ in range(n_players)]

    def summary(self, servers, total_time):
        lines = [f"Общее время моделирования: {total_time:.2f}", ""]

        for k in range(len(self.generated)):
            g = self.generated[k]
            p_rej = self.cancelled[k] / g if g else 0
            t_w = sum(self.wait_times[k]) / len(self.wait_times[k]) if self.wait_times[k] else 0
            t_s = sum(self.service_times[k]) / len(self.service_times[k]) if self.service_times[k] else 0
            lines.append(f"Игрок {k + 1}: заявок {g}, отказов {self.cancelled[k]} "
                         f"(P_отк={p_rej:.3f}), обработано {self.processed[k]}, "
                         f"T_ож={t_w:.3f}, T_обсл={t_s:.3f}")
        lines.append("")

        for s in servers:
            load = s.busy_time / total_time if total_time else 0
            lines.append(f"Сервер {s.id + 1}: загрузка K_исп={load:.3f}")

        return "\n".join(lines)
