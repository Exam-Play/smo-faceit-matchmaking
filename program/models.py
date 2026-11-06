class SearchRequest:
    def __init__(self, player_id, number, arrival_time):
        self.player_id = player_id
        self.number = number
        self.arrival_time = arrival_time # не путать - это время входа в систему
        self.service_start = None # а это когда сервер начал обработку

    @property
    def label(self):
        return f"{self.player_id + 1}.{self.number}"


class MatchmakingServer:
    def __init__(self, server_id):
        self.id = server_id
        self.current = None
        self.busy_until = None
        self.busy_time = 0.0

    def is_busy(self):
        return self.current is not None