import heapq

from models import Event

class EventCalendar:
    def __init__(self):
        self._heap = []
        self._sequence = 0

    def schedule(self, time, event_type, data):
        self._sequence += 1
        event = Event(time, event_type, data)
        heapq.heappush(
            self._heap, (event.time, self._sequence, event)
        )

    def next(self):
        if self.isEmpty():
            return None
        return heapq.heappop(self._heap)[2]

    def isEmpty(self):
        return len(self._heap) == 0

    def __len__(self):
        return len(self._heap)

    def preview(self, count=4):
        return sorted(self._heap)[:count]
