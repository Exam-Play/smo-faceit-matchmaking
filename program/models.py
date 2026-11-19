class SearchRequest:
    def __init__(self, player_id, number, arrival_time):
        self.player_id = player_id
        self.number = number
        self.arrival_time = arrival_time
        self.service_start = None
        self.service_end = None

    @property
    def label(self):
        return f"{self.player_id + 1}.{self.number}"


class Event:
    def __init__(self, time, event_type, data):
        self.time = time
        self.type = event_type
        self.data = data


class Player:
    def __init__(self, player_id, lam, rng, event_calendar):
        self.id = player_id
        self.lam = lam
        self.rng = rng
        self.event_calendar = event_calendar
        self.request_counter = 0

    def schedule_first_request(self):
        self.event_calendar.schedule(
            self.rng.expovariate(self.lam), "SEARCH_REQUESTED", self.id
        )

    def onSearchRequested(self, t):
        self.request_counter += 1
        request = SearchRequest(self.id, self.request_counter, t)
        next_time = t + self.rng.expovariate(self.lam)
        self.event_calendar.schedule(next_time, "SEARCH_REQUESTED", self.id)
        return request


class MatchmakingServer:
    """Сервер, собирающий лобби для одной заявки."""

    def __init__(self, server_id, mu, rng, event_calendar):
        self.id = server_id
        self.mu = mu
        self.rng = rng
        self.event_calendar = event_calendar
        self.current = None
        self.busy_until = None
        self.busy_time = 0.0

    def is_busy(self):
        return self.current is not None

    def startLobbyBuilding(self, request, t):
        self.current = request
        request.service_start = t
        duration = self.rng.expovariate(self.mu)
        self.busy_until = t + duration
        self.event_calendar.schedule(
            self.busy_until, "LOBBY_FORMED", self.id
        )
        return duration

    def onLobbyFormed(self, t):
        request = self.current
        if request is None:
            return None, 0.0

        duration = t - request.service_start
        request.service_end = t
        self.busy_time += duration
        self.current = None
        self.busy_until = None
        return request, duration
