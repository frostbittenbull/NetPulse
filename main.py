import sys
import os
import subprocess
import threading
import customtkinter as ctk
from datetime import datetime

ctk.set_appearance_mode("dark")

def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

class SubnetScanner(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NetPulse")
        self.geometry("560x500")
        self.resizable(False, False)
        self.configure(fg_color="#0d0d0f")

        try:
            icon_path = resource_path("icon.ico")
            self.iconbitmap(icon_path)
            self.wm_iconbitmap(icon_path)
        except Exception:
            pass

        self._scanning = False
        self._stop_flag = False
        self._results = []
        self._subnet = ""

        self._build_ui()
        self.bind("<Return>", lambda event: self._toggle_scan())
        self._center_window()
        self._animate_intro()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        input_frame = ctk.CTkFrame(self, fg_color="#0d0d0f", corner_radius=0, height=38)
        input_frame.pack(fill="x", padx=12, pady=(8, 0))
        input_frame.pack_propagate(False)

        subnet_lbl = ctk.CTkLabel(
            input_frame,
            text="ПОДСЕТЬ:",
            font=("Courier New", 14, "bold"),
            text_color="#808080",
        )
        subnet_lbl.pack(side="left", padx=(0, 8))

        self.subnet_entry = ctk.CTkEntry(
            input_frame,
            font=("Courier New", 11),
            fg_color="#0a0a0c",
            text_color="#7cfc98",
            border_color="#1e1e1e",
            border_width=1,
            corner_radius=6,
            placeholder_text="192.168.1",
            placeholder_text_color="#3a3a3a",
            height=26,
            width=480,
        )
        self.subnet_entry.pack(side="left")

        console_frame = ctk.CTkFrame(self, fg_color="#0d0d0f", corner_radius=0)
        console_frame.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        self.console_box = ctk.CTkTextbox(
            console_frame,
            fg_color="#0a0a0c",
            text_color="#7cfc98",
            font=("Courier New", 11),
            corner_radius=6,
            border_width=1,
            border_color="#1e1e1e",
            scrollbar_button_color="#1e1e1e",
            scrollbar_button_hover_color="#2e2e2e",
            wrap="word",
        )
        self.console_box.pack(fill="both", expand=True)
        self.console_box.configure(state="disabled")

        self.console_box.tag_config("green",  foreground="#4ade80")
        self.console_box.tag_config("red",    foreground="#f87171")
        self.console_box.tag_config("accent", foreground="#5b5ef4")
        self.console_box.tag_config("dim",    foreground="#555566")
        self.console_box.tag_config("yellow", foreground="#fbbf24")

        bottom = ctk.CTkFrame(self, fg_color="#0d0d0f", corner_radius=0, height=46)
        bottom.pack(fill="x", side="bottom", padx=12, pady=(0, 10))
        bottom.pack_propagate(False)

        self.scan_btn = ctk.CTkButton(
            bottom,
            text="▶  Начать сканирование",
            font=("Courier New", 11, "bold"),
            fg_color="#1a5c2a",
            hover_color="#2a7c3a",
            text_color="#ffffff",
            corner_radius=6,
            height=28,
            border_width=0,
            command=self._toggle_scan,
        )
        self.scan_btn.pack(fill="x", expand=True)

    def _animate_intro(self):
        lines = [
            ("", None),
            ("  Введите подсеть и нажмите «Начать сканирование».", None),
            ("  Будут проверены все адреса .1 — .254.", "dim"),
            ("", None),
        ]
        for i, (line, tag) in enumerate(lines):
            self.after(i * 55, lambda l=line, t=tag: self.log(l, tag=t))

    def log(self, text, tag=None):
        self.console_box.configure(state="normal")
        if tag:
            self.console_box.insert("end", text + "\n", tag)
        else:
            self.console_box.insert("end", text + "\n")
        self.console_box.see("end")
        self.console_box.configure(state="disabled")

    def _set_status(self, state: str = "idle"):
        colors = {
            "idle":    ("#2e2e2e", "#3d3d3d"),
            "working": ("#7f2020", "#a03030"),
            "done":    ("#1a5c2a", "#2a7c3a"),
        }
        btn_color, hover_color = colors.get(state, colors["idle"])
        self.scan_btn.configure(fg_color=btn_color, hover_color=hover_color)

    def _toggle_scan(self):
        if self._scanning:
            self._stop_flag = True
            self.scan_btn.configure(state="disabled", text="⏳  Остановка…")
        else:
            self._start_scan()

    def _start_scan(self):
        subnet = self.subnet_entry.get().strip()
        if not subnet:
            self.log("  ✗ Укажите подсеть!", tag="red")
            return

        self._subnet = subnet
        self._results = []
        self._scanning = True
        self._stop_flag = False

        self.scan_btn.configure(
            text="■  Стоп",
            fg_color="#7f2020",
            hover_color="#a03030",
            state="normal",
        )
        self._set_status("working")

        self.log("")
        self.log(f"  Подсеть: {subnet}.0/24", tag="accent")
        self.log("  Запуск полного сканирования…", tag="dim")
        self.log("")

        threading.Thread(target=self._scan_worker, args=(subnet,), daemon=True).start()

    def _scan_worker(self, subnet):
        responded = 0
        total = 254

        for i in range(1, total + 1):
            if self._stop_flag:
                break

            ip = f"{subnet}.{i}"
            try:
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "200", ip],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="cp866",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                alive = "TTL=" in result.stdout
            except Exception:
                alive = False

            if alive:
                responded += 1
                self._results.append(f"{ip} - ОТВЕЧАЕТ")
                self.after(0, lambda line=f"  {ip}  ─  ОТВЕЧАЕТ": self.log(line, tag="green"))
            else:
                self._results.append(f"{ip} - НЕ ОТВЕЧАЕТ")
                self.after(0, lambda line=f"  {ip}  ─  НЕ ОТВЕЧАЕТ": self.log(line, tag="red"))

        stopped = self._stop_flag

        def finish():
            self.log("")
            if stopped:
                self.log("  ✗ Сканирование остановлено.", tag="yellow")
            else:
                self.log(f"  ✓ Готово. Ответили: {responded}/{total}", tag="green")
            self.log("")
            self._scanning = False
            self._stop_flag = False
            self.scan_btn.configure(
                state="normal",
                text="▶  Начать сканирование",
                fg_color="#1a5c2a",
                hover_color="#2a7c3a",
            )
            self._set_status("done" if not stopped else "idle")

        self.after(0, finish)

if __name__ == "__main__":
    app = SubnetScanner()
    app.mainloop()