import random

from dispatchers import EnqueueDispatcher, AssignmentDispatcher
from event_calendar import EventCalendar
from models import Player, MatchmakingServer
from queue_manager import MatchmakingQueue
from statistics import Statistics
from system_state import SystemState


SEARCH_REQUESTED = "SEARCH_REQUESTED"
LOBBY_FORMED = "LOBBY_FORMED"


class SimulationController:
    def __init__(
        self, n_players, lam, mu, buffer_size, n_servers,
        max_requests, seed=None
    ):
        if n_players <= 0:
            raise ValueError("Количество игроков должно быть положительным")
        if lam <= 0 or mu <= 0:
            raise ValueError("Параметры lambda и mu должны быть положительными")
        if max_requests < 0:
            raise ValueError("Количество заявок не может быть отрицательным")

        self.rng = random.Random(seed)
        self.lam = lam
        self.mu = mu
        self.max_requests = max_requests
        self.n_players = n_players

        self.time = 0.0
        self.calendar = EventCalendar()
        self.queue = MatchmakingQueue(buffer_size)
        self.servers = [
            MatchmakingServer(i, mu, self.rng, self.calendar)
            for i in range(n_servers)
        ]
        self.stats = Statistics(n_players, n_servers)
        self.players = [
            Player(i, lam, self.rng, self.calendar)
            for i in range(n_players)
        ]

        self.assignment_dispatcher = AssignmentDispatcher(
            self.queue, self.servers, self.stats
        )
        self.enqueue_dispatcher = EnqueueDispatcher(
            self.queue, self.stats, self.assignment_dispatcher
        )

        self.total_generated = 0
        self.last_message = "Модель создана. Нажмите «Шаг»."

        for player in self.players:
            player.schedule_first_request()
        self.state = self.create_system_state()

    @property
    def server_ptr(self):
        return self.assignment_dispatcher.server_pointer

    def is_finished(self):
        return self.calendar.isEmpty()

    def step(self):
        if self.is_finished():
            self.last_message = "Моделирование завершено."
            return self.last_message

        event = self.calendar.next()
        self.time = event.time

        if event.type == SEARCH_REQUESTED:
            message = self._handle_search_requested(event.data)
            dispatch_message = ""
            if self.total_generated >= self.max_requests and (
                "лимит заявок исчерпан" in message
            ):
                dispatch_message = self.assignment_dispatcher.onQueueChanged(
                    self.time
                )
        elif event.type == LOBBY_FORMED:
            message = self._handle_lobby_formed(event.data)
            server = self.servers[event.data]
            dispatch_message = self.assignment_dispatcher.onServerReleased(
                server, self.time
            )
        else:
            message = f"Неизвестный тип события: {event.type}"
            dispatch_message = ""

        self.last_message = f"t={self.time:.2f}: {message}{dispatch_message}"
        self.state = self.create_system_state()
        return self.last_message

    def _handle_search_requested(self, player_id):
        if self.total_generated >= self.max_requests:
            return (
                f"игрок {player_id + 1}: лимит заявок исчерпан, "
                f"событие отброшено."
            )

        self.total_generated += 1
        request = self.players[player_id].onSearchRequested(self.time)
        return self.enqueue_dispatcher.enqueue(request, self.time)

    def _handle_lobby_formed(self, server_id):
        server = self.servers[server_id]
        request, duration = server.onLobbyFormed(self.time)

        if request is None:
            return f"сервер {server_id + 1}: событие завершения без заявки."

        self.stats.registerProcessed(request, duration)
        return (
            f"сервер {server.id + 1} собрал лобби "
            f"для заявки {request.label}."
        )

    def runAuto(self, nRequests=None):
        if nRequests is None:
            while not self.is_finished():
                self.step()
        else:
            for _ in range(nRequests):
                if self.is_finished():
                    break
                self.step()

    def run_to_end(self):
        self.runAuto()

    def summary(self):
        return self.stats.summary(self.servers, self.time)

    def create_system_state(self):
        return SystemState(
            self.time, self.queue, self.server_ptr,
            self.servers, self.last_message
        )


Simulation = SimulationController
