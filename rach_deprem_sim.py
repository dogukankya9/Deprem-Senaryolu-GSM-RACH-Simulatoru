import tkinter as tk
from tkinter import ttk
import random
import time

class RachSimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GSM Deprem Modu - RACH Çakışması Simülatörü")
        self.root.geometry("1240x790")
        self.root.configure(bg="#d9d9d9")

        # -----------------------------
        # SİSTEM DURUM DEĞİŞKENLERİ
        # -----------------------------
        self.earthquake_mode = False
        self.earthquake_start_time = None

        # AYRI PAUSE / RESUME
        self.paused = False
        self.pause_start_time = None
        self.total_paused_duration = 0

        self.network_load = 25
        self.barring_level = 10
        self.collision_rate = 0
        self.total_attempts = 0
        self.success_count = 0
        self.blocked_count = 0
        self.collided_count = 0
        self.tick_count = 0

        self.manual_seismic_value = 0.0
        self.use_manual_seismic = False
        self.last_seismic_value = 0.0

        self.user_classes = {
            "AFAD / Ambulans / İtfaiye": {"priority": 1, "color": "#b30000"},
            "Kamu / Kritik Altyapı": {"priority": 2, "color": "#cc5500"},
            "Normal Vatandaş": {"priority": 3, "color": "#004c99"},
            "Düşük Öncelik / Toplu Trafik": {"priority": 4, "color": "#666666"}
        }

        self.logs = []
        self.history_tables = {}
        self.log_items = []
        self.selected_log_index = None
        self.selected_tick_no = None

        self.build_ui()
        self.refresh_labels(self.last_seismic_value)
        self.refresh_button_states()
        self.update_loop()

    # =========================================================
    # ARAYÜZ
    # =========================================================
    def build_ui(self):
        title = tk.Label(
            self.root,
            text="GSM DEPREM MODU / RACH ÇAKIŞMASI SİMÜLATÖRÜ",
            font=("Courier New", 18, "bold"),
            bg="#a6a6a6",
            fg="black",
            relief="raised",
            bd=3,
            pady=8
        )
        title.pack(fill="x", padx=8, pady=8)

        main_frame = tk.Frame(self.root, bg="#d9d9d9")
        main_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # SOL TARAF SCROLL
        left_outer = tk.Frame(main_frame, bg="#cfcfcf", relief="sunken", bd=2)
        left_outer.pack(side="left", fill="y", padx=(0, 6))

        self.left_canvas = tk.Canvas(left_outer, bg="#cfcfcf", highlightthickness=0, width=320)
        self.left_canvas.pack(side="left", fill="y", expand=False)

        left_scrollbar = tk.Scrollbar(left_outer, orient="vertical", command=self.left_canvas.yview)
        left_scrollbar.pack(side="right", fill="y")

        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_panel = tk.Frame(self.left_canvas, bg="#cfcfcf")
        self.left_panel = left_panel

        self.left_canvas_window = self.left_canvas.create_window((0, 0), window=left_panel, anchor="nw")

        left_panel.bind("<Configure>", self.on_left_panel_configure)
        self.left_canvas.bind("<Configure>", self.on_left_canvas_configure)

        self.left_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.left_canvas.bind_all("<Button-4>", self.on_mousewheel_linux)
        self.left_canvas.bind_all("<Button-5>", self.on_mousewheel_linux)

        # SAĞ PANEL
        right_panel = tk.Frame(main_frame, bg="#cfcfcf", relief="sunken", bd=2)
        right_panel.pack(side="right", fill="both", expand=True)

        info_title = tk.Label(
            left_panel, text="SİSTEM DURUMU",
            font=("Courier New", 13, "bold"),
            bg="#808080", fg="white", width=34
        )
        info_title.pack(fill="x", pady=4)

        self.lbl_earthquake = self.make_info_label(left_panel, "Deprem Modu: KAPALI")
        self.lbl_mode_time = self.make_info_label(left_panel, "Deprem Modu Süresi: 0 sn")
        self.lbl_pause = self.make_info_label(left_panel, "Simülasyon Durumu: ÇALIŞIYOR")
        self.lbl_seismic = self.make_info_label(left_panel, "Sismik Seviye: 0.00")
        self.lbl_network = self.make_info_label(left_panel, "Şebeke Yükü: %25")
        self.lbl_barring = self.make_info_label(left_panel, "Barring Seviyesi: %10")
        self.lbl_collision = self.make_info_label(left_panel, "RACH Çakışma: %0")
        self.lbl_total = self.make_info_label(left_panel, "Toplam Deneme: 0")
        self.lbl_success = self.make_info_label(left_panel, "Başarılı Erişim: 0")
        self.lbl_blocked = self.make_info_label(left_panel, "Barring Engeli: 0")
        self.lbl_collided = self.make_info_label(left_panel, "Çakışan Paket: 0")

        ttk.Separator(left_panel, orient="horizontal").pack(fill="x", padx=6, pady=8)

        control_title = tk.Label(
            left_panel, text="KONTROLLER",
            font=("Courier New", 12, "bold"),
            bg="#808080", fg="white", width=34
        )
        control_title.pack(fill="x", pady=4)

        seismic_frame = tk.Frame(left_panel, bg="#cfcfcf")
        seismic_frame.pack(fill="x", padx=6, pady=4)

        tk.Label(
            seismic_frame,
            text="Elle Sismik Değer:",
            font=("Courier New", 10),
            bg="#cfcfcf"
        ).pack(anchor="w")

        self.seismic_scale = tk.Scale(
            seismic_frame, from_=0, to=20, resolution=0.1,
            orient="horizontal", length=220,
            font=("Courier New", 9),
            command=self.on_manual_seismic_change
        )
        self.seismic_scale.set(0)
        self.seismic_scale.pack()

        self.chk_manual_var = tk.IntVar(value=0)
        chk_manual = tk.Checkbutton(
            seismic_frame,
            text="Elle sismik veri kullan",
            variable=self.chk_manual_var,
            font=("Courier New", 10),
            bg="#cfcfcf",
            command=self.toggle_manual_seismic
        )
        chk_manual.pack(anchor="w", pady=3)

        btn_frame = tk.Frame(left_panel, bg="#cfcfcf")
        btn_frame.pack(fill="x", padx=6, pady=6)

        # TEK DEPREM MODU BUTONU
        self.btn_trigger = tk.Button(
            btn_frame,
            text="DEPREM MODUNU TETİKLE",
            font=("Courier New", 10, "bold"),
            bg="#ffcc00",
            activebackground="#e6b800",
            width=28,
            relief="raised",
            bd=3,
            command=self.toggle_earthquake_mode
        )
        self.btn_trigger.pack(pady=3)

        # HER ZAMAN AKTİF PAUSE / RESUME
        self.btn_pause_resume = tk.Button(
            btn_frame,
            text="SİMÜLASYONU DURDUR",
            font=("Courier New", 10, "bold"),
            bg="#cccc00",
            activebackground="#b3b300",
            width=28,
            relief="raised",
            bd=3,
            state="normal",
            command=self.toggle_pause_resume
        )
        self.btn_pause_resume.pack(pady=3)

        self.btn_normal = tk.Button(
            btn_frame,
            text="NORMAL TRAFİK ÜRET",
            font=("Courier New", 10, "bold"),
            bg="#99ccff",
            activebackground="#7fbfff",
            width=28,
            relief="raised",
            bd=3,
            command=lambda: self.manual_generate_traffic(20, self.btn_normal)
        )
        self.btn_normal.pack(pady=3)

        self.btn_heavy = tk.Button(
            btn_frame,
            text="YOĞUN TRAFİK ÜRET",
            font=("Courier New", 10, "bold"),
            bg="#ff9966",
            activebackground="#ff8552",
            width=28,
            relief="raised",
            bd=3,
            command=lambda: self.manual_generate_traffic(60, self.btn_heavy)
        )
        self.btn_heavy.pack(pady=3)

        self.btn_reset = tk.Button(
            btn_frame,
            text="SAYAÇLARI SIFIRLA",
            font=("Courier New", 10, "bold"),
            bg="#dddddd",
            activebackground="#c8c8c8",
            width=28,
            relief="raised",
            bd=3,
            command=self.reset_counters
        )
        self.btn_reset.pack(pady=3)

        ttk.Separator(left_panel, orient="horizontal").pack(fill="x", padx=6, pady=8)

        legend_title = tk.Label(
            left_panel, text="ÖNCELİK SINIFLARI",
            font=("Courier New", 12, "bold"),
            bg="#808080", fg="white", width=34
        )
        legend_title.pack(fill="x", pady=4)

        for name, data in self.user_classes.items():
            lbl = tk.Label(
                left_panel,
                text=f"P{data['priority']} - {name}",
                font=("Courier New", 10, "bold"),
                bg=data["color"],
                fg="white",
                anchor="w",
                padx=6
            )
            lbl.pack(fill="x", padx=6, pady=2)

        tk.Label(left_panel, text="", bg="#cfcfcf", height=3).pack()

        table_title = tk.Label(
            right_panel, text="ERİŞİM DENEME TABLOSU",
            font=("Courier New", 13, "bold"),
            bg="#808080", fg="white"
        )
        table_title.pack(fill="x", pady=4)

        self.lbl_table_info = tk.Label(
            right_panel,
            text="Gösterilen Tablo: Son Tur",
            font=("Courier New", 10, "bold"),
            bg="#e6e6e6",
            anchor="w",
            relief="groove",
            bd=2,
            padx=6,
            pady=4
        )
        self.lbl_table_info.pack(fill="x", padx=8, pady=(2, 4))

        self.lbl_selected_log = tk.Label(
            right_panel,
            text="Seçilen Log: Yok",
            font=("Courier New", 10, "bold"),
            bg="#fff2cc",
            anchor="w",
            relief="groove",
            bd=2,
            padx=6,
            pady=4
        )
        self.lbl_selected_log.pack(fill="x", padx=8, pady=(0, 6))

        columns = ("id", "sinif", "oncelik", "istek", "barring", "sonuc")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", height=14)

        self.tree.heading("id", text="ID")
        self.tree.heading("sinif", text="Kullanıcı Sınıfı")
        self.tree.heading("oncelik", text="Öncelik")
        self.tree.heading("istek", text="İstek Sayısı")
        self.tree.heading("barring", text="Barring")
        self.tree.heading("sonuc", text="Sonuç")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("sinif", width=250, anchor="center")
        self.tree.column("oncelik", width=80, anchor="center")
        self.tree.column("istek", width=100, anchor="center")
        self.tree.column("barring", width=100, anchor="center")
        self.tree.column("sonuc", width=220, anchor="center")

        self.tree.pack(fill="x", padx=8, pady=6)

        log_title = tk.Label(
            right_panel, text="SİSTEM OLAY KAYITLARI (Satıra tıklayabilirsin)",
            font=("Courier New", 13, "bold"),
            bg="#808080", fg="white"
        )
        log_title.pack(fill="x", pady=(12, 4))

        log_frame = tk.Frame(right_panel, bg="#cfcfcf")
        log_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.log_listbox = tk.Listbox(
            log_frame,
            font=("Courier New", 10),
            bg="black",
            fg="#00ff00",
            selectbackground="#1e5eff",
            selectforeground="white",
            activestyle="dotbox",
            exportselection=False
        )
        self.log_listbox.pack(side="left", fill="both", expand=True)

        log_scroll = tk.Scrollbar(log_frame, command=self.log_listbox.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_listbox.config(yscrollcommand=log_scroll.set)

        self.log_listbox.bind("<<ListboxSelect>>", self.on_log_select)

        self.add_log("Sistem başlatıldı.")
        self.add_log("Normal çalışma modu aktif.")
        self.add_log("Log satırına tıklayarak ilgili turun tablosu görüntülenebilir.")

    # =========================================================
    # SCROLL
    # =========================================================
    def on_left_panel_configure(self, event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def on_left_canvas_configure(self, event):
        self.left_canvas.itemconfig(self.left_canvas_window, width=event.width)

    def on_mousewheel(self, event):
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
            if widget and self.is_widget_inside_left_panel(widget):
                self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except:
            pass

    def on_mousewheel_linux(self, event):
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
            if widget and self.is_widget_inside_left_panel(widget):
                if event.num == 4:
                    self.left_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.left_canvas.yview_scroll(1, "units")
        except:
            pass

    def is_widget_inside_left_panel(self, widget):
        parent = widget
        while parent is not None:
            if parent == self.left_panel:
                return True
            parent = parent.master
        return False

    # =========================================================
    # UI
    # =========================================================
    def make_info_label(self, parent, text):
        lbl = tk.Label(
            parent,
            text=text,
            font=("Courier New", 10, "bold"),
            bg="#e6e6e6",
            anchor="w",
            relief="groove",
            bd=2,
            padx=6,
            pady=4,
            width=34
        )
        lbl.pack(fill="x", padx=6, pady=2)
        return lbl

    def set_button_pressed_effect(self, button):
        button.config(relief="sunken", bd=5)
        self.root.after(180, lambda: button.config(relief="raised", bd=3))

    def refresh_button_states(self):
        # Tek deprem modu butonu
        if self.earthquake_mode:
            self.btn_trigger.config(
                state="normal",
                bg="#ff6666",
                activebackground="#e05555",
                text="DEPREM MODUNU DURDUR"
            )
        else:
            self.btn_trigger.config(
                state="normal",
                bg="#ffcc00",
                activebackground="#e6b800",
                text="DEPREM MODUNU TETİKLE"
            )

        # Pause / Resume HER ZAMAN aktif
        if self.paused:
            self.btn_pause_resume.config(
                state="normal",
                text="DEVAM ET",
                bg="#66cc66",
                activebackground="#52b352"
            )
            self.btn_normal.config(state="disabled", disabledforeground="#666666", bg="#cfd8dc")
            self.btn_heavy.config(state="disabled", disabledforeground="#666666", bg="#d7ccc8")
        else:
            self.btn_pause_resume.config(
                state="normal",
                text="SİMÜLASYONU DURDUR",
                bg="#cccc00",
                activebackground="#b3b300"
            )
            self.btn_normal.config(state="normal", bg="#99ccff")
            self.btn_heavy.config(state="normal", bg="#ff9966")

    # =========================================================
    # LOG
    # =========================================================
    def add_log(self, message, tick_no=None):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"

        self.logs.append(line)
        self.log_items.append((line, tick_no))

        if len(self.log_items) > 400:
            self.log_items.pop(0)

        self.refresh_log_listbox()

    def refresh_log_listbox(self):
        self.log_listbox.delete(0, tk.END)
        for text, _ in self.log_items:
            self.log_listbox.insert(tk.END, text)

        self.log_listbox.see(tk.END)
        self.log_listbox.yview_moveto(1.0)

    def clear_logs(self):
        self.logs.clear()
        self.log_items.clear()
        self.selected_log_index = None
        self.selected_tick_no = None
        self.log_listbox.delete(0, tk.END)
        self.lbl_selected_log.config(text="Seçilen Log: Yok")

    def on_log_select(self, event):
        selection = self.log_listbox.curselection()

        if not selection:
            self.selected_log_index = None
            self.selected_tick_no = None
            self.lbl_selected_log.config(text="Seçilen Log: Yok")
            self.root.after(10, lambda: self.log_listbox.yview_moveto(1.0))
            return

        index = selection[0]
        self.selected_log_index = index

        text, tick_no = self.log_items[index]

        if tick_no is None:
            self.selected_tick_no = None
            self.lbl_selected_log.config(text="Seçilen Log: Genel sistem kaydı")
            self.lbl_table_info.config(text="Gösterilen Tablo: Bu log için kayıtlı tur yok")
        else:
            self.selected_tick_no = tick_no
            self.lbl_selected_log.config(text=f"Seçilen Log: TUR {tick_no}")

            if tick_no in self.history_tables:
                rows = self.history_tables[tick_no]
                self.show_table_rows(rows)
                self.lbl_table_info.config(text=f"Gösterilen Tablo: Tur {tick_no}")
            else:
                self.lbl_table_info.config(text=f"Gösterilen Tablo: Tur {tick_no} bulunamadı")

        self.root.after(10, lambda: self.log_listbox.yview_moveto(1.0))

    # =========================================================
    # TABLO
    # =========================================================
    def show_table_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for item in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    item["id"],
                    item["class"],
                    f"P{item['priority']}",
                    1,
                    f"%{item['barring_prob']}",
                    item["result"]
                )
            )

    # =========================================================
    # YARDIMCI
    # =========================================================
    def on_manual_seismic_change(self, value):
        self.manual_seismic_value = float(value)
        self.last_seismic_value = self.manual_seismic_value
        self.refresh_labels(self.last_seismic_value)

    def toggle_manual_seismic(self):
        self.use_manual_seismic = bool(self.chk_manual_var.get())
        if self.use_manual_seismic:
            self.add_log("Elle sismik veri modu açıldı.")
        else:
            self.add_log("Otomatik sismik veri modu açıldı.")

    def manual_generate_traffic(self, boost, button):
        if self.paused:
            return
        self.set_button_pressed_effect(button)
        self.generate_traffic(manual_boost=boost)
        self.refresh_labels(self.last_seismic_value)

    # =========================================================
    # PAUSE / RESUME
    # =========================================================
    def toggle_pause_resume(self):
        self.set_button_pressed_effect(self.btn_pause_resume)

        if not self.paused:
            self.pause_simulation()
        else:
            self.resume_simulation()

    def pause_simulation(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
            self.add_log("Simülasyon DURDURULDU. Tüm değerler donduruldu.")
            self.refresh_labels(self.last_seismic_value)
            self.refresh_button_states()

    def resume_simulation(self):
        if self.paused:
            paused_duration = time.time() - self.pause_start_time
            self.total_paused_duration += paused_duration
            self.paused = False
            self.pause_start_time = None
            self.add_log("Simülasyon tekrar başlatıldı.")
            self.refresh_labels(self.last_seismic_value)
            self.refresh_button_states()

    # =========================================================
    # DEPREM MODU
    # =========================================================
    def toggle_earthquake_mode(self):
        self.set_button_pressed_effect(self.btn_trigger)

        if not self.earthquake_mode:
            self.earthquake_mode = True
            self.earthquake_start_time = time.time()

            self.add_log("Deprem modu MANUEL olarak aktifleştirildi.")
        else:
            self.earthquake_mode = False
            self.earthquake_start_time = None
            self.barring_level = 10

            self.add_log("Deprem modu kullanıcı tarafından durduruldu.")

        self.refresh_labels(self.last_seismic_value)
        self.refresh_button_states()

    def reset_counters(self):
        self.set_button_pressed_effect(self.btn_reset)

        self.total_attempts = 0
        self.success_count = 0
        self.blocked_count = 0
        self.collided_count = 0
        self.collision_rate = 0
        self.tick_count = 0

        self.tree.delete(*self.tree.get_children())
        self.history_tables.clear()
        self.lbl_table_info.config(text="Gösterilen Tablo: Son Tur")

        self.clear_logs()
        self.add_log("Sistem olay kayıtları ve sayaçlar sıfırlandı.")

        self.refresh_labels(self.last_seismic_value)

    # =========================================================
    # SİSMİK
    # =========================================================
    def get_seismic_value(self):
        if self.use_manual_seismic:
            return self.manual_seismic_value

        base = random.uniform(0.2, 3.5)
        if random.random() < 0.04:
            base += random.uniform(8, 15)

        return round(base, 2)

    def check_earthquake_trigger(self, seismic_value):
        threshold = 8.5
        if seismic_value >= threshold and not self.earthquake_mode:
            self.earthquake_mode = True
            self.earthquake_start_time = time.time()
            self.add_log(f"Sismik eşik aşıldı ({seismic_value}). Deprem modu aktif edildi.")
            self.refresh_button_states()

    def get_earthquake_mode_duration(self):
        if self.earthquake_mode and self.earthquake_start_time:
            if self.paused and self.pause_start_time is not None:
                return int(
                    self.pause_start_time
                    - self.earthquake_start_time
                    - self.total_paused_duration
                )
            else:
                return int(
                    time.time()
                    - self.earthquake_start_time
                    - self.total_paused_duration
                )
        return 0

    # =========================================================
    # ŞEBEKE
    # =========================================================
    def update_network_conditions(self):
        if not self.earthquake_mode:
            self.network_load += random.randint(-4, 4)
            self.network_load = max(10, min(55, self.network_load))
        else:
            self.network_load += random.randint(-3, 8)
            self.network_load = max(40, min(100, self.network_load))

        if self.earthquake_mode:
            if self.network_load >= 90:
                self.barring_level = 70
            elif self.network_load >= 80:
                self.barring_level = 55
            elif self.network_load >= 70:
                self.barring_level = 40
            elif self.network_load >= 60:
                self.barring_level = 25
            else:
                self.barring_level = 15
        else:
            if self.network_load >= 50:
                self.barring_level = 15
            elif self.network_load >= 35:
                self.barring_level = 10
            else:
                self.barring_level = 5

    def priority_barring_probability(self, priority):
        if priority == 1:
            return max(0, self.barring_level - 45)
        elif priority == 2:
            return max(0, self.barring_level - 20)
        elif priority == 3:
            return self.barring_level
        else:
            return min(95, self.barring_level + 15)

    # =========================================================
    # TRAFİK
    # =========================================================
    def generate_traffic(self, manual_boost=0):
        if self.paused:
            return

        self.tick_count += 1

        if self.earthquake_mode:
            user_count = random.randint(8, 18) + manual_boost // 8
        else:
            user_count = random.randint(3, 8) + manual_boost // 10

        attempts_this_round = []
        class_names = list(self.user_classes.keys())

        weighted_classes_normal = [
            class_names[0], class_names[1], class_names[2], class_names[2], class_names[2], class_names[3]
        ]
        weighted_classes_quake = [
            class_names[0], class_names[0], class_names[1],
            class_names[2], class_names[2], class_names[2], class_names[2], class_names[3]
        ]

        pool = weighted_classes_quake if self.earthquake_mode else weighted_classes_normal

        for i in range(user_count):
            chosen = random.choice(pool)
            priority = self.user_classes[chosen]["priority"]
            barring_prob = self.priority_barring_probability(priority)
            is_barred = random.randint(1, 100) <= barring_prob

            attempts_this_round.append({
                "id": f"{self.tick_count}-{i+1}",
                "class": chosen,
                "priority": priority,
                "barring_prob": barring_prob,
                "barred": is_barred,
                "result": ""
            })

        non_barred = [a for a in attempts_this_round if not a["barred"]]
        barred = [a for a in attempts_this_round if a["barred"]]

        available_slots = 6 if not self.earthquake_mode else 4
        non_barred.sort(key=lambda x: x["priority"])

        accepted = []
        collided = []

        if len(non_barred) <= available_slots:
            accepted = non_barred
        else:
            accepted = non_barred[:available_slots]
            overflow = non_barred[available_slots:]

            for item in overflow:
                if random.random() < 0.8:
                    collided.append(item)
                else:
                    accepted.append(item)

        for item in barred:
            item["result"] = "BARRING ENGELİ"
            self.blocked_count += 1

        for item in collided:
            item["result"] = "RACH ÇAKIŞMASI"
            self.collided_count += 1

        for item in accepted:
            if item["result"] == "":
                item["result"] = "ERİŞİM BAŞARILI"
                self.success_count += 1

        all_items = attempts_this_round
        self.total_attempts += len(all_items)

        if self.total_attempts > 0:
            self.collision_rate = int((self.collided_count / self.total_attempts) * 100)
        else:
            self.collision_rate = 0

        self.history_tables[self.tick_count] = [dict(item) for item in all_items]

        self.show_table_rows(all_items)
        self.lbl_table_info.config(text=f"Gösterilen Tablo: Son Tur (Tur {self.tick_count})")

        ok_count = sum(1 for x in all_items if x["result"] == "ERİŞİM BAŞARILI")
        barred_count = sum(1 for x in all_items if x["result"] == "BARRING ENGELİ")
        collision_count = sum(1 for x in all_items if x["result"] == "RACH ÇAKIŞMASI")

        log_message = (
            f"[TUR {self.tick_count}] "
            f"{len(all_items)} erişim denemesi üretildi | "
            f"Başarılı: {ok_count} | "
            f"Engelli: {barred_count} | "
            f"Çakışma: {collision_count}"
        )
        self.add_log(log_message, tick_no=self.tick_count)

    # =========================================================
    # LABEL
    # =========================================================
    def refresh_labels(self, seismic_value):
        mode_text = "AKTİF" if self.earthquake_mode else "KAPALI"
        mode_color = "#ff4d4d" if self.earthquake_mode else "#66cc66"

        pause_text = "DURDURULDU" if self.paused else "ÇALIŞIYOR"
        pause_color = "#ffcc66" if self.paused else "#99ff99"

        self.lbl_earthquake.config(text=f"Deprem Modu: {mode_text}", bg=mode_color)
        self.lbl_mode_time.config(text=f"Deprem Modu Süresi: {self.get_earthquake_mode_duration()} sn")
        self.lbl_pause.config(text=f"Simülasyon Durumu: {pause_text}", bg=pause_color)
        self.lbl_seismic.config(text=f"Sismik Seviye: {seismic_value:.2f}")
        self.lbl_network.config(text=f"Şebeke Yükü: %{self.network_load}")
        self.lbl_barring.config(text=f"Barring Seviyesi: %{self.barring_level}")
        self.lbl_collision.config(text=f"RACH Çakışma: %{self.collision_rate}")
        self.lbl_total.config(text=f"Toplam Deneme: {self.total_attempts}")
        self.lbl_success.config(text=f"Başarılı Erişim: {self.success_count}")
        self.lbl_blocked.config(text=f"Barring Engeli: {self.blocked_count}")
        self.lbl_collided.config(text=f"Çakışan Paket: {self.collided_count}")

    # =========================================================
    # ANA DÖNGÜ
    # =========================================================
    def update_loop(self):
        if self.paused:
            self.refresh_labels(self.last_seismic_value)
            self.root.after(1000, self.update_loop)
            return

        seismic_value = self.get_seismic_value()
        self.last_seismic_value = seismic_value

        self.check_earthquake_trigger(seismic_value)
        self.update_network_conditions()

        if self.earthquake_mode:
            self.generate_traffic(manual_boost=25)
        else:
            self.generate_traffic(manual_boost=0)

        self.refresh_labels(seismic_value)
        self.root.after(1000, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("default")
    app = RachSimulationApp(root)
    root.mainloop()
