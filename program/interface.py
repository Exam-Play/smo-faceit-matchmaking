import tkinter as tk
from tkinter import ttk

from simulation import Simulation

SEARCH_REQUESTED = "SEARCH_REQUESTED"
LOBBY_FORMED = "LOBBY_FORMED"

class App:
    def __init__(self, root):
        self.root = root
        root.title("Матчмейкинг FACEIT — пошаговый режим (ОД2)")
        self.sim = None

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        self.entries = {}
        defaults = [("Игроков", "players", 4), ("λ одного игрока", "lam", 1.2),
                    ("μ сервера", "mu", 1.0), ("Размер буфера", "buf", 4),
                    ("Серверов", "servers", 2), ("N заявок", "n", 30)]
        for col, (title, key, val) in enumerate(defaults):
            ttk.Label(top, text=title).grid(row=0, column=col, padx=4)
            e = ttk.Entry(top, width=8)
            e.insert(0, str(val))
            e.grid(row=1, column=col, padx=4)
            self.entries[key] = e

        buttons = ttk.Frame(root, padding=6)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Сброс / Начать", command=self.reset).pack(side="left", padx=4)
        ttk.Button(buttons, text="Шаг", command=self.do_step).pack(side="left", padx=4)
        ttk.Button(buttons, text="Шаг ×10", command=lambda: self.do_step(10)).pack(side="left", padx=4)
        ttk.Button(buttons, text="До конца + итоги", command=self.do_run_all).pack(side="left", padx=4)

        self.canvas = tk.Canvas(root, width=900, height=330, bg="white")
        self.canvas.pack(padx=6, pady=4)

        self.log = tk.Text(root, height=12, width=120)
        self.log.pack(padx=6, pady=4)

        self.reset()

    def reset(self):
        g = lambda k, f: f(self.entries[k].get().replace(",", "."))
        self.sim = Simulation(
            n_players=g("players", int), lam=g("lam", float), mu=g("mu", float),
            buffer_size=g("buf", int), n_servers=g("servers", int),
            max_requests=g("n", int), seed=42)
        self.log.delete("1.0", "end")
        self.log.insert("end", "Модель создана. Нажимайте «Шаг».\n")
        self.draw()

    def do_step(self, times=1):
        for _ in range(times):
            if self.sim.is_finished():
                break
            msg = self.sim.step()
            self.log.insert("end", msg + "\n")
        if self.sim.is_finished():
            self.log.insert("end", "\n--- Моделирование завершено ---\n" + self.sim.summary() + "\n")
        self.log.see("end")
        self.draw()

    def do_run_all(self):
        self.sim.run_to_end()
        self.log.insert("end", "\n--- Прогон до конца ---\n" + self.sim.summary() + "\n")
        self.log.see("end")
        self.draw()

    def draw(self):
        c, sim = self.canvas, self.sim
        c.delete("all")
        q = sim.queue

        c.create_text(10, 12, anchor="w", font=("Arial", 11, "bold"),
                      text=f"Время: {sim.time:.2f}")
        c.create_text(120, 12, anchor="w", text=sim.last_message, width=770)

        c.create_rectangle(10, 100, 100, 160, fill="#cfe2f3")
        c.create_text(55, 130, text="Игроки\n(источники)", justify="center")
        c.create_line(100, 130, 130, 130, arrow="last")

        x0, y0, h = 130, 100, 60
        w = min(70, 470 // q.size)
        pointers = {}
        pointers.setdefault(q.put_ptr, []).append("put ▲ (запись)")
        pointers.setdefault(q.take_ptr, []).append("take ▲ (выбор)")
        c.create_text(x0, y0 - 28, anchor="w", font=("Arial", 10, "bold"),
                      text="Очередь поиска (кольцевой буфер)")
        for i, cell in enumerate(q.cells):
            x = x0 + i * w
            c.create_rectangle(x, y0, x + w, y0 + h, fill="#f9cb9c" if cell else "white")
            c.create_text(x + w / 2, y0 - 10, text=str(i + 1), fill="gray")
            if cell:
                c.create_text(x + w / 2, y0 + h / 2, text=cell.label, font=("Arial", 11, "bold"))
        for i, names in pointers.items():
            for j, name in enumerate(names):
                c.create_text(x0 + i * w + w / 2, y0 + h + 14 + 14 * j, text=name,
                              fill="#b45f06", font=("Arial", 8))

        sx, sw = 690, 190
        n = len(sim.servers)
        step_y = min(70, 260 // max(n, 1))
        buf_end = x0 + q.size * w
        c.create_text(sx, 40, anchor="w", font=("Arial", 10, "bold"), text="Серверы (приборы)")
        for s in sim.servers:
            y = 60 + s.id * step_y
            color = "#ea9999" if s.is_busy() else "#b6d7a8"
            c.create_rectangle(sx, y, sx + sw, y + step_y - 10, fill=color)
            if s.is_busy():
                txt = f"Сервер {s.id + 1}: заявка {s.current.label}\nзанят до {s.busy_until:.2f}"
            else:
                txt = f"Сервер {s.id + 1}: свободен"
            c.create_text(sx + sw / 2, y + (step_y - 10) / 2, text=txt, justify="center")
            if s.id == sim.server_ptr:
                c.create_text(sx - 6, y + (step_y - 10) / 2, anchor="e",
                              text="srv ►", fill="#b45f06", font=("Arial", 8))
            c.create_line(buf_end + 4, y0 + h / 2, sx - 45, y + (step_y - 10) / 2)

        cancelled = sum(sim.stats.cancelled)
        processed = sum(sim.stats.processed)
        c.create_text(10, 270, anchor="w", font=("Arial", 10),
                      text=f"Сгенерировано заявок: {sim.total_generated} из {sim.max_requests}   |   "
                           f"Лобби собрано: {processed}   |   "
                           f"Отказов (поиск отменён): {cancelled}   |   "
                           f"В очереди сейчас: {sum(1 for x in q.cells if x)}")
        c.create_text(10, 295, anchor="w", fill="gray",
                      text="Ближайшие события в календаре: " + ", ".join(
                          f"{'заявка игрока ' + str(d + 1) if et == SEARCH_REQUESTED else 'сервер ' + str(d + 1) + ' свободен'} @ {tt:.2f}"
                          for tt, _, et, d in sorted(sim.calendar)[:4]))

