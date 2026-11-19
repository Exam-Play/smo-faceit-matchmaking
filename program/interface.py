import tkinter as tk
from tkinter import ttk

from simulation import SimulationController, SEARCH_REQUESTED


class App:
    def __init__(self, root):
        self.root = root
        root.title("Матчмейкинг FACEIT — пошаговый режим (ОД2)")
        self.sim = None

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        self.entries = {}
        defaults = [
            ("Игроков", "players", 4),
            ("λ одного игрока", "lam", 1.2),
            ("μ сервера", "mu", 1.0),
            ("Размер буфера", "buf", 4),
            ("Серверов", "servers", 2),
            ("N заявок", "n", 30),
        ]
        for col, (title, key, value) in enumerate(defaults):
            ttk.Label(top, text=title).grid(row=0, column=col, padx=4)
            entry = ttk.Entry(top, width=8)
            entry.insert(0, str(value))
            entry.grid(row=1, column=col, padx=4)
            self.entries[key] = entry

        buttons = ttk.Frame(root, padding=6)
        buttons.pack(fill="x")
        ttk.Button(
            buttons, text="Сброс / Начать", command=self.reset
        ).pack(side="left", padx=4)
        ttk.Button(
            buttons, text="Шаг", command=self.do_step
        ).pack(side="left", padx=4)
        ttk.Button(
            buttons, text="Шаг ×10", command=lambda: self.do_step(10)
        ).pack(side="left", padx=4)
        ttk.Button(
            buttons, text="До конца + итоги", command=self.do_run_all
        ).pack(side="left", padx=4)

        self.canvas = tk.Canvas(root, width=900, height=330, bg="white")
        self.canvas.pack(padx=6, pady=4)

        self.log = tk.Text(root, height=12, width=120)
        self.log.pack(padx=6, pady=4)

        self.reset()

    def reset(self):
        def get_value(key, converter):
            return converter(self.entries[key].get().replace(",", "."))

        self.sim = SimulationController(
            n_players=get_value("players", int),
            lam=get_value("lam", float),
            mu=get_value("mu", float),
            buffer_size=get_value("buf", int),
            n_servers=get_value("servers", int),
            max_requests=get_value("n", int),
            seed=None,
        )
        self.log.delete("1.0", "end")
        self.log.insert("end", "Модель создана. Нажимайте «Шаг».\n")
        self.draw()

    def do_step(self, times=1):
        for _ in range(times):
            if self.sim.is_finished():
                break
            self.log.insert("end", self.sim.step() + "\n")

        if self.sim.is_finished():
            self.log.insert(
                "end",
                "\n--- Моделирование завершено ---\n"
                + self.sim.summary() + "\n"
            )
        self.log.see("end")
        self.draw()

    def do_run_all(self):
        self.sim.runAuto()
        self.log.insert(
            "end",
            "\n--- Прогон до конца ---\n" + self.sim.summary() + "\n"
        )
        self.log.see("end")
        self.draw()

    def draw(self):
        state = self.sim.create_system_state()
        c = self.canvas
        c.delete("all")

        c.create_text(
            10, 12, anchor="w", font=("Arial", 11, "bold"),
            text=f"Время: {state.time:.2f}"
        )
        c.create_text(
            120, 12, anchor="w", text=state.lastMessage, width=770
        )

        c.create_rectangle(10, 100, 100, 160, fill="#cfe2f3")
        c.create_text(55, 130, text="Игроки\n(источники)", justify="center")
        c.create_line(100, 130, 130, 130, arrow="last")

        x0, y0, height = 130, 100, 60
        width = min(70, 470 // len(state.queueCells))
        pointers = {}
        pointers.setdefault(state.putPointer, []).append("put ▲ (запись)")
        pointers.setdefault(state.takePointer, []).append("take ▲ (выбор)")

        c.create_text(
            x0, y0 - 28, anchor="w", font=("Arial", 10, "bold"),
            text="Очередь поиска (кольцевой буфер)"
        )
        for index, cell in enumerate(state.queueCells):
            x = x0 + index * width
            c.create_rectangle(
                x, y0, x + width, y0 + height,
                fill="#f9cb9c" if cell else "white"
            )
            c.create_text(x + width / 2, y0 - 10, text=str(index + 1), fill="gray")
            if cell:
                c.create_text(
                    x + width / 2, y0 + height / 2,
                    text=cell.label, font=("Arial", 11, "bold")
                )

        for index, names in pointers.items():
            for offset, name in enumerate(names):
                c.create_text(
                    x0 + index * width + width / 2,
                    y0 + height + 14 + 14 * offset,
                    text=name, fill="#b45f06", font=("Arial", 8)
                )

        server_x, server_width = 690, 190
        server_count = len(state.servers)
        step_y = min(70, 260 // max(server_count, 1))
        buffer_end = x0 + len(state.queueCells) * width

        c.create_text(
            server_x, 40, anchor="w", font=("Arial", 10, "bold"),
            text="Серверы (приборы)"
        )
        for server in state.servers:
            y = 60 + server.id * step_y
            color = "#ea9999" if server.is_busy() else "#b6d7a8"
            c.create_rectangle(
                server_x, y, server_x + server_width, y + step_y - 10,
                fill=color
            )
            if server.is_busy():
                label = (
                    f"Сервер {server.id + 1}: заявка {server.current.label}\n"
                    f"занят до {server.busy_until:.2f}"
                )
            else:
                label = f"Сервер {server.id + 1}: свободен"

            c.create_text(
                server_x + server_width / 2,
                y + (step_y - 10) / 2,
                text=label, justify="center"
            )
            if server.id == state.serverPointer:
                c.create_text(
                    server_x - 6, y + (step_y - 10) / 2,
                    anchor="e", text="srv ►", fill="#b45f06",
                    font=("Arial", 8)
                )
            c.create_line(
                buffer_end + 4, y0 + height / 2,
                server_x - 45, y + (step_y - 10) / 2
            )

        cancelled = sum(self.sim.stats.cancelled)
        processed = sum(self.sim.stats.processed)
        queued = sum(1 for cell in state.queueCells if cell is not None)
        c.create_text(
            10, 270, anchor="w", font=("Arial", 10),
            text=(
                f"Сгенерировано заявок: {self.sim.total_generated} "
                f"из {self.sim.max_requests}   |   "
                f"Лобби собрано: {processed}   |   "
                f"Отказов (поиск отменён): {cancelled}   |   "
                f"В очереди сейчас: {queued}"
            )
        )

        upcoming = []
        for _, _, event in self.sim.calendar.preview(4):
            if event.type == SEARCH_REQUESTED:
                description = f"заявка игрока {event.data + 1}"
            else:
                description = f"сервер {event.data + 1} свободен"
            upcoming.append(f"{description} @ {event.time:.2f}")

        c.create_text(
            10, 295, anchor="w", fill="gray",
            text="Ближайшие события в календаре: " + ", ".join(upcoming)
        )
