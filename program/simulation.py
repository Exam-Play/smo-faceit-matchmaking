import heapq
import random

from models import SearchRequest, MatchmakingServer
from queue_manager import MatchmakingQueue
from statistics import Statistics

SEARCH_REQUESTED = "SEARCH_REQUESTED"
LOBBY_FORMED = "LOBBY_FORMED"

class Simulation:
    def __init__(self, n_players, lam, mu, buffer_size, n_servers, max_requests, seed=None):
        self.rng = random.Random(seed)
        self.lam = lam
        self.mu = mu
        self.max_requests = max_requests
        self.n_players = n_players

        self.time = 0.0
        self.calendar = []
        self._seq = 0

        self.queue = MatchmakingQueue(buffer_size)
        self.servers = [MatchmakingServer(i) for i in range(n_servers)]
        self.server_ptr = 0
        self.stats = Statistics(n_players, n_servers)
        self.total_generated = 0
        self.player_counter = [0] * n_players
        self.last_message = "Модель создана. Нажмите «Шаг»."

        for k in range(n_players):
            self._schedule(self.rng.expovariate(lam), SEARCH_REQUESTED, k)

    def _schedule(self, t, event_type, data):
        self._seq += 1
        heapq.heappush(self.calendar, (t, self._seq, event_type, data))

    def is_finished(self):
        return len(self.calendar) == 0

    def step(self):
        if self.is_finished():
            self.last_message = "Моделирование завершено."
            return self.last_message

        t, _, ev_type, data = heapq.heappop(self.calendar)
        self.time = t

        if ev_type == SEARCH_REQUESTED:
            msg = self._on_search_requested(data)
        else:
            msg = self._on_lobby_formed(data)

        msg += self._dispatch()
        self.last_message = f"t={self.time:.2f}: {msg}"
        return self.last_message

    def _on_search_requested(self, k):
        if self.total_generated >= self.max_requests:
            return f"игрок {k + 1}: лимит заявок исчерпан, событие отброшено."
        self.total_generated += 1
        self.player_counter[k] += 1
        req = SearchRequest(k, self.player_counter[k], self.time)
        self.stats.generated[k] += 1

        self._schedule(self.time + self.rng.expovariate(self.lam), SEARCH_REQUESTED, k)
    
        old = self.queue.put(req)
        msg = f"заявка {req.label} поступила в очередь."
        if old is not None:
            self.stats.cancelled[old.player_id] += 1
            msg += f" Очередь полна: выбита самая старая заявка {old.label} (отказ)."
        return msg

    def _on_lobby_formed(self, server_id):
        s = self.servers[server_id]
        req = s.current
        tau = self.time - req.service_start
        s.busy_time += tau
        self.stats.processed[req.player_id] += 1
        self.stats.service_times[req.player_id].append(tau)
        s.current = None
        s.busy_until = None
        return f"сервер {s.id + 1} собрал лобби для заявки {req.label}."

    def _dispatch(self):
        if self.queue.is_empty():
            return ""
        n = len(self.servers)
        for i in range(n):
            idx = (self.server_ptr + i) % n
            if not self.servers[idx].is_busy():
                server = self.servers[idx]
                self.server_ptr = (idx + 1) % n
                req = self.queue.take_next()
                req.service_start = self.time
                self.stats.wait_times[req.player_id].append(self.time - req.arrival_time)
                tau = self.rng.expovariate(self.mu)
                server.current = req
                server.busy_until = self.time + tau
                self._schedule(server.busy_until, LOBBY_FORMED, server.id)
                return f" Сервер {server.id + 1} взял заявку {req.label} (займёт {tau:.2f})."
        return " Все серверы заняты — заявки ждут."

    def run_to_end(self):
        while not self.is_finished():
            self.step()

    def summary(self):
        return self.stats.summary(self.servers, self.time)
